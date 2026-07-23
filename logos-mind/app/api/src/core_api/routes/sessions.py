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
from core_api.services.massive.client import MassiveClient
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
massive_client = MassiveClient()


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

    short_volume = await massive_client.get_short_volume(payload.ticker, limit=10)
    short_interest = await massive_client.get_short_interest(payload.ticker, limit=4)
    free_float = await massive_client.get_float(payload.ticker, limit=10)

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
    evidence_items = await repo.get_recent_evidence_items(
        session_id=session_id,
        limit=payload.max_evidence_items,
    )
    step_slot = (round_no - 1) % 3

    judge_memory_episode = None

    if step_slot == 0:
        action, claim, control_checks = planner.step_from_evidence(evidence_items)
    elif step_slot == 1:
        latest_claim = await repo.get_latest_claim(session_id)
        action, claim, control_checks = risk_agent.step_from_context(
            evidence_items=evidence_items,
            latest_claim=latest_claim,
        )
    else:
        recent_claims = await repo.get_recent_claims(session_id=session_id, limit=2)
        recent_actions = await repo.get_recent_actions(session_id=session_id, limit=6)
        action, claim, control_checks = judge_agent.evaluate_debate(
            recent_claims=recent_claims,
            recent_actions=recent_actions,
        )
        judge_memory_episode = build_judge_summary_episode(
            action=action,
            claim=claim,
            control_checks=control_checks,
        )

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

    return StepSessionResponse(
        session_id=session_id,
        step_status="completed",
        action=action,
        claim=claim,
        controls={
            "checks_written": len(control_checks),
            "round_no": round_no,
            "action_agent": action.agent_name,
        },
        stepped_at=datetime.now(timezone.utc),
    )