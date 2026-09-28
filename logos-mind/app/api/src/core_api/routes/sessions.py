from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db_session
from core_api.models.api import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionDetailResponse,
    SessionListResponse,
    StepSessionRequest,
    StepSessionResponse,
)
from core_api.models.domain import SessionState
from repositories.sessions import SessionRepository
from core_api.services.agents.planner import PlannerService
from core_api.services.agents.risk_agent import RiskAgentService
from core_api.services.agents.judge_agent import JudgeAgentService
from core_api.services.evidence.mappers import map_massive_news_to_evidence
from core_api.services.world_state.builder import WorldStateBuilder
from core_api.services.session.bootstrap import (
    build_initial_control_checks,
    build_initial_memory_episodes,
)
from core_api.services.session.judge_memory import build_judge_summary_episode


router = APIRouter()
builder = WorldStateBuilder()
planner = PlannerService()
risk_agent = RiskAgentService()
judge_agent = JudgeAgentService()


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    payload: CreateSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> CreateSessionResponse:
    world_state = await builder.build(
        ticker=payload.ticker,
        as_of_date=payload.as_of_date,
    )

    session = SessionState(
        world_state=world_state,
        actions=[],
        claims=[],
        controls={
            "grounding_ok": True,
            "contradictions": [],
        },
        memory_summary={
            "episodes_found": 0,
            "patterns_found": 0,
        },
    )

    repo = SessionRepository(db)
    await repo.create_session(
        session=session,
        window_days=payload.window_days,
        mode=payload.mode,
    )
    
    # Removing until their results are incorporated into WorldState or EvidenceItem
    # short_volume = await massive_client.get_short_volume(payload.ticker, limit=10)
    # short_interest = await massive_client.get_short_interest(payload.ticker, limit=4)
    # free_float = await massive_client.get_float(payload.ticker, limit=10)
    
    news_items = world_state.event_state.get("raw_news_items", [])
    evidence_items = [map_massive_news_to_evidence(item) for item in news_items]

    memory_episodes = build_initial_memory_episodes(
        world_state=world_state,
        evidence_count=len(evidence_items),
    )
    control_checks = build_initial_control_checks(
        world_state=world_state,
        evidence_count=len(evidence_items),
    )

    await repo.insert_evidence_items(session.session_id, evidence_items)
    await repo.insert_memory_episodes(session.session_id, memory_episodes)
    await repo.insert_control_checks(session.session_id, control_checks)
    await repo.commit()

    return CreateSessionResponse(
        session_id=session.session_id,
        status="created",
        session=session,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db_session),
) -> SessionListResponse:
    repo = SessionRepository(db)
    sessions = await repo.list_sessions(limit=20)
    return SessionListResponse(sessions=sessions)


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> SessionDetailResponse:
    repo = SessionRepository(db)
    session = await repo.get_session_detail(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

DEBATE_PHASES = (
    "bull_opening",
    "bear_opening",
    "bull_rebuttal",
    "bear_rebuttal",
    "judge_verdict",
)


def get_debate_phase(round_no: int) -> str:
    phase_index = round_no - 1

    if phase_index >= len(DEBATE_PHASES):
        raise HTTPException(
            status_code=409,
            detail=(
                "This session's debate is complete. "
                "Create a new session or add an explicit restart workflow."
            ),
        )

    return DEBATE_PHASES[phase_index]


@router.post("/sessions/{session_id}/step", response_model=StepSessionResponse)
async def step_session(
    session_id: UUID,
    payload: StepSessionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> StepSessionResponse:
    repo = SessionRepository(db)
    session = await repo.get_session_detail(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    round_no = await repo.get_next_round_no(session_id)
    phase = get_debate_phase(round_no)

    evidence_items = await repo.get_recent_evidence_items(
        session_id=session_id,
        limit=payload.max_evidence_items,
    )
    if phase != "judge_verdict" and not evidence_items:
        raise HTTPException(
            status_code=422,
            detail=(
                "This debate phase requires session evidence, but no evidence "
                "items are available for the session."
            )
        )

    judge_memory_episode = None

    if phase == "bull_opening":
        action, claim, control_checks = await planner.step_from_evidence(
            world_state=session.world_state,
            evidence_items=evidence_items,
        )

    elif phase == "bear_opening":
        bull_claims = await repo.get_recent_claims(
            session_id=session_id,
            side="bull",
            limit=3,
        )
        action, claim, control_checks = await risk_agent.open_case(
            world_state=session.world_state,
            evidence_items=evidence_items,
            opposing_claims=bull_claims,
        )

    elif phase == "bull_rebuttal":
        bear_claims = await repo.get_recent_claims(
            session_id=session_id,
            side="bear",
            limit=3,
            round_no=2,
            claim_type="opening",
            status="active",
        )
        
        if not bear_claims:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cannot execute Bull rebuttal: no active Round 2 Bear opening "
                    "claims exist for this session."
                ),
            )
        
        action, claim, control_checks = await planner.rebut(
            world_state=session.world_state,
            evidence_items=evidence_items,
            opposing_claims=bear_claims,
        )

    elif phase == "bear_rebuttal":
        bull_claims = await repo.get_recent_claims(
            session_id=session_id,
            side="bull",
            round_no=3,
            claim_type="rebuttal",
            status="active",
            limit=3,
        )
        if not bull_claims: 
            raise HTTPException(
                status_code=409,
                detail=(
                    "Cannot execute Bear rebuttal: no active Round 3 Bull rebuttal "
                    "claims exist for this session."
                ),
            )
        action, claim, control_checks = await risk_agent.rebut(
            world_state=session.world_state,
            evidence_items=evidence_items,
            opposing_claims=bull_claims,
        )

    else:
        required_claims_turns = (
            ("bull", 1, "opening"),
            ("bear", 2, "opening"),
            ("bull", 3, "rebuttal"),
            ("bear", 4, "rebuttal"),
        )
        recent_claims = []
        for side, required_round_no, claim_type in required_claims_turns:
            matching_claims = await repo.get_recent_claims(
                session_id=session_id,
                side=side,
                round_no=required_round_no,
                claim_type=claim_type,
                status="active",
                limit=1,
            )

            if not matching_claims:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Cannot execute Judge verdict: missing active "
                        f"Round {required_round_no} {side.title()} {claim_type} "
                        "claim for this session."
                    ),
                )
            recent_claims.append(matching_claims[0])

        recent_actions = await repo.get_recent_actions(
            session_id=session_id,
            limit=8,
        )
        recent_actions = [
            action
            for action in recent_actions
            if action.round_no in {1, 2, 3, 4}
        ]
        try:
            action, claim, control_checks = await judge_agent.evaluate_debate(
                recent_claims=recent_claims,
                recent_actions=recent_actions,
            )
        except ValueError as exc: 
            raise HTTPException(
                status_code=409,
                detail=f"Cannot execute Judge verdict: {exc}",
            ) from exc 
        
        judge_memory_episode = build_judge_summary_episode(
            action=action,
            claim=claim,
            control_checks=control_checks,
        )

    action = action.model_copy(
        update={"round_no": round_no},
    )

    if claim is not None:
        claim = claim.model_copy(
            update={"round_no": round_no},
        )
    try:
        await repo.insert_agent_action(
            session_id=session_id,
            round_no=round_no,
            action=action,
        )

        if claim is not None:
            await repo.insert_agent_claim(
                session_id=session_id,
                round_no=round_no,
                claim=claim,
            )

        await repo.insert_control_checks(session_id, control_checks)

        if judge_memory_episode is not None:
            await repo.insert_memory_episodes(session_id, [judge_memory_episode])

        await repo.commit()
    except Exception:
        await db.rollback()
        raise 

    return StepSessionResponse(
        session_id=session_id,
        step_status="completed",
        phase=phase,
        action=action,
        claim=claim,
        controls={
            "checks_written": len(control_checks),
            "round_no": round_no,
            "phase": phase,
            "action_agent": action.agent_name,
        },
        stepped_at=datetime.now(timezone.utc),
    )