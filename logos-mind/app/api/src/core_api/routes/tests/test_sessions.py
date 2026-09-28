from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from core_api.models.api import StepSessionRequest
from core_api.models.domain import AgentAction, Claim, EvidenceItem, WorldState
from core_api.routes import sessions as sessions_route


def make_world_state() -> WorldState:
    return WorldState(
        security={
            "ticker": "DEMO",
            "as_of_date": date(2026, 9, 27),
        },
        market_state={},
        fundamental_state={},
        event_state={},
        peer_state={},
        state_version="route-test-v1",
    )


def make_evidence_item(*, evidence_id: UUID) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_type="test",
        source_ref="test://bull-rebuttal-route",
        observed_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
        title="Route test evidence",
        summary=(
            "Revenue grew year over year and guidance was maintained. "
            "The evidence packet does not include margin or valuation data."
        ),
        freshness_score=0.95,
        confidence=0.95,
    )

def make_round_1_bull_opening(*, evidence_id: UUID) -> Claim:
    return Claim(
        claim_id=uuid4(),
        round_no=1,
        side="bull",
        claim_type="opening",
        thesis=(
            "Revenue growth and maintained guidance support a constructive "
            "operating outlook, subject to the limits of the supplied record."
        ),
        confidence=0.64,
        evidence_ids=[evidence_id],
        target_claim_ids=[],
        status="active",
    )

def make_round_2_bear_opening(*, evidence_id: UUID) -> Claim:
    return Claim(
        claim_id=uuid4(),
        round_no=2,
        side="bear",
        claim_type="opening",
        thesis=(
            "The evidence packet lacks margin and valuation support needed "
            "to establish a durable constructive conclusion."
        ),
        confidence=0.68,
        evidence_ids=[evidence_id],
        target_claim_ids=[uuid4()],
        status="active",
    )


def make_round_3_bull_rebuttal(
    *,
    evidence_id: UUID,
    bear_claim_id: UUID,
) -> Claim:
    return Claim(
        claim_id=uuid4(),
        round_no=3,
        side="bull",
        claim_type="rebuttal",
        thesis=(
            "Maintained guidance supports the operating trajectory, while "
            "missing margin and valuation evidence appropriately narrows "
            "the constructive conclusion."
        ),
        confidence=0.61,
        evidence_ids=[evidence_id],
        target_claim_ids=[bear_claim_id],
        status="active",
    )
def make_round_4_bear_rebuttal(
    *,
    evidence_id: UUID, 
    bull_rebuttal_claim_id: UUID, 
) -> Claim:
    return Claim(
        claim_id=uuid4(),
        round_no=4,
        side="bear",
        claim_type="rebuttal",
        thesis=(
            "The Bull rebuttal narrows its conclusion but does not resolve "
            "the missing margin, valuation, and conversion evidence needed "
            "to establish durable economics."
        ),
        confidence=0.66,
        evidence_ids=[evidence_id],
        target_claim_ids=[bull_rebuttal_claim_id],
        status="active",
    )

def make_completed_debate(
    *,
    evidence_id: UUID,) -> tuple[list[Claim], list[AgentAction]]:
    bull_opening = make_round_1_bull_opening(
        evidence_id=evidence_id,
    )
    bear_opening = make_round_2_bear_opening(
        evidence_id=evidence_id,
    )
    bear_opening = bear_opening.model_copy(
        update={
            "target_claim_ids": [bull_opening.claim_id],
        },
    )

    bull_rebuttal = make_round_3_bull_rebuttal(
        evidence_id=evidence_id,
        bear_claim_id=bear_opening.claim_id,
    )

    bear_rebuttal = make_round_4_bear_rebuttal(
        evidence_id=evidence_id,
        bull_rebuttal_claim_id=bull_rebuttal.claim_id,
    )
    

    actions = [
        AgentAction(
            action_id=uuid4(),
            round_no=1,
            agent_name="planner",
            action_type="make_bull_case",
            rationale="Bull opening action.",
            evidence_ids=[evidence_id],
            confidence=0.64,
        ),
        AgentAction(
            action_id=uuid4(),
            round_no=2,
            agent_name="risk_agent",
            action_type="make_bear_case",
            rationale="Bear opening action.",
            evidence_ids=[evidence_id],
            confidence=0.68,
        ),
        AgentAction(
            action_id=uuid4(),
            round_no=3,
            agent_name="planner",
            action_type="rebut_bear_case",
            rationale="Bull rebuttal action.",
            evidence_ids=[evidence_id],
            confidence=0.61,
        ),
        AgentAction(
            action_id=uuid4(),
            round_no=4,
            agent_name="risk_agent",
            action_type="rebut_bull_case",
            rationale="Bear rebuttal action.",
            evidence_ids=[evidence_id],
            confidence=0.66,
        ),
    ]

    return [
        bull_opening,
        bear_opening,
        bull_rebuttal,
        bear_rebuttal,
    ], actions

class FakeSessionRepository:
    def __init__(self, db: object) -> None:
        self.db = db
        self.session = None
        self.evidence_items: list[EvidenceItem] = []
        self.recent_claims: list[Claim] = []
        self.recent_actions: list[AgentAction] = []
        self.next_round_no = 3

        self.get_recent_claims_calls: list[dict] = []
        self.get_recent_actions_calls: list[dict] = []

        self.insert_agent_action_calls: list[dict] = []
        self.insert_agent_claim_calls: list[dict] = []
        self.insert_control_checks_calls: list[dict] = []
        self.insert_memory_episodes_calls: list[dict] = []

        self.commit_calls = 0

    async def get_session_detail(self, session_id: UUID):
        assert self.session is not None
        assert session_id == self.session.session_id
        return self.session

    async def get_next_round_no(self, session_id: UUID) -> int:
        assert self.session is not None
        assert session_id == self.session.session_id
        return self.next_round_no

    async def get_recent_evidence_items(
        self,
        *,
        session_id: UUID,
        limit: int,
    ) -> list[EvidenceItem]:
        assert self.session is not None
        assert session_id == self.session.session_id
        assert limit == 10
        return self.evidence_items

    async def get_recent_claims(
        self,
        *,
        session_id: UUID,
        **kwargs,
    ) -> list[Claim]:
        assert self.session is not None
        assert session_id == self.session.session_id

        self.get_recent_claims_calls.append(kwargs)

        filtered_claims = list(self.recent_claims)

        if "side" in kwargs:
            filtered_claims = [
                claim
                for claim in filtered_claims
                if claim.side == kwargs["side"]
            ]

        if "round_no" in kwargs:
            filtered_claims = [
                claim
                for claim in filtered_claims
                if claim.round_no == kwargs["round_no"]
            ]

        if "claim_type" in kwargs:
            filtered_claims = [
                claim
                for claim in filtered_claims
                if claim.claim_type == kwargs["claim_type"]
            ]

        if "status" in kwargs:
            filtered_claims = [
                claim
                for claim in filtered_claims
                if claim.status == kwargs["status"]
            ]

        limit = kwargs.get("limit")
        if limit is not None:
            filtered_claims = filtered_claims[:limit]

        return filtered_claims

    async def get_recent_actions(
        self,
        *,
        session_id: UUID,
        limit: int,
    ) -> list[AgentAction]:
        assert self.session is not None
        assert session_id == self.session.session_id

        self.get_recent_actions_calls.append(
            {
                "limit": limit,
            }
        )

        return self.recent_actions[:limit]

    async def insert_agent_action(
        self,
        *,
        session_id: UUID,
        round_no: int,
        action: AgentAction,
    ) -> None:
        self.insert_agent_action_calls.append(
            {
                "session_id": session_id,
                "round_no": round_no,
                "action": action,
            }
        )

    async def insert_agent_claim(
        self,
        *,
        session_id: UUID,
        round_no: int,
        claim: Claim,
    ) -> None:
        self.insert_agent_claim_calls.append(
            {
                "session_id": session_id,
                "round_no": round_no,
                "claim": claim,
            }
        )

    async def insert_control_checks(
        self,
        session_id: UUID,
        control_checks: list[dict],
    ) -> None:
        self.insert_control_checks_calls.append(
            {
                "session_id": session_id,
                "control_checks": control_checks,
            }
        )

    async def insert_memory_episodes(
        self,
        session_id: UUID,
        episodes: list[dict],
    ) -> None:
        self.insert_memory_episodes_calls.append(
            {
                "session_id": session_id,
                "episodes": episodes,
            }
        )

    async def commit(self) -> None:
        self.commit_calls += 1


@pytest.fixture
def route_fakes(monkeypatch):
    fake_repo = FakeSessionRepository(db=object())
    fake_planner = SimpleNamespace(rebut=AsyncMock())
    fake_risk_agent = SimpleNamespace(
        open_case=AsyncMock(),
        rebut=AsyncMock(),
    )
    fake_judge_agent = SimpleNamespace(evaluate_debate=AsyncMock())

    monkeypatch.setattr(
        sessions_route,
        "SessionRepository",
        lambda db: fake_repo,
    )
    monkeypatch.setattr(sessions_route, "planner", fake_planner)
    monkeypatch.setattr(sessions_route, "risk_agent", fake_risk_agent)
    monkeypatch.setattr(sessions_route, "judge_agent", fake_judge_agent)

    return fake_repo, fake_planner, fake_risk_agent, fake_judge_agent


@pytest.mark.asyncio
async def test_bull_rebuttal_uses_only_active_round_2_bear_openings(
    route_fakes,
) -> None:
    fake_repo, fake_planner, fake_risk_agent, fake_judge_agent = route_fakes

    session_id = uuid4()
    evidence_id = uuid4()
    world_state = make_world_state()
    evidence_item = make_evidence_item(evidence_id=evidence_id)
    bear_opening = make_round_2_bear_opening(evidence_id=evidence_id)
    bull_rebuttal = make_round_3_bull_rebuttal(
        evidence_id=evidence_id,
        bear_claim_id=bear_opening.claim_id,
    )

    fake_repo.session = SimpleNamespace(
        session_id=session_id,
        world_state=world_state,
    )
    fake_repo.evidence_items = [evidence_item]
    fake_repo.recent_claims = [bear_opening]

    expected_action = AgentAction(
        action_id=uuid4(),
        agent_name="planner",
        action_type="rebut_bear_case",
        rationale="The Bull case is narrowed but remains evidence-grounded.",
        evidence_ids=[evidence_id],
        confidence=0.61,
        round_no=0,
    )
    expected_control_checks = [
        {
            "check_type": "evidence_citation",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "counterclaim_targeting",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
    ]

    fake_planner.rebut.return_value = (
        expected_action,
        bull_rebuttal,
        expected_control_checks,
    )

    response = await sessions_route.step_session(
        session_id=session_id,
        payload=StepSessionRequest(max_evidence_items=10),
        db=object(),
    )

    assert response.step_status == "completed"
    assert response.phase == "bull_rebuttal"
    assert response.controls["round_no"] == 3
    assert response.controls["phase"] == "bull_rebuttal"

    assert fake_repo.get_recent_claims_calls == [
        {
            "side": "bear",
            "limit": 3,
            "round_no": 2,
            "claim_type": "opening",
            "status": "active",
        }
    ]

    fake_planner.rebut.assert_awaited_once_with(
        world_state=world_state,
        evidence_items=[evidence_item],
        opposing_claims=[bear_opening],
    )
    fake_risk_agent.open_case.assert_not_awaited()
    fake_risk_agent.rebut.assert_not_awaited()
    fake_judge_agent.evaluate_debate.assert_not_awaited()

    assert response.action.round_no == 3
    assert response.claim is not None
    assert response.claim.round_no == 3

    assert len(fake_repo.insert_agent_action_calls) == 1
    action_write = fake_repo.insert_agent_action_calls[0]
    assert action_write["session_id"] == session_id
    assert action_write["round_no"] == 3
    assert action_write["action"].round_no == 3
    assert action_write["action"].agent_name == "planner"
    assert action_write["action"].action_type == "rebut_bear_case"

    assert len(fake_repo.insert_agent_claim_calls) == 1
    claim_write = fake_repo.insert_agent_claim_calls[0]
    assert claim_write["session_id"] == session_id
    assert claim_write["round_no"] == 3
    assert claim_write["claim"].round_no == 3
    assert claim_write["claim"].side == "bull"
    assert claim_write["claim"].claim_type == "rebuttal"
    assert claim_write["claim"].target_claim_ids == [
        bear_opening.claim_id
    ]

    assert fake_repo.insert_control_checks_calls == [
        {
            "session_id": session_id,
            "control_checks": expected_control_checks,
        }
    ]
    assert fake_repo.commit_calls == 1


@pytest.mark.asyncio
async def test_bull_rebuttal_requires_active_round_2_bear_opening(
    route_fakes,
) -> None:
    fake_repo, fake_planner, fake_risk_agent, fake_judge_agent = route_fakes

    session_id = uuid4()
    evidence_id = uuid4()
    world_state = make_world_state()

    fake_repo.session = SimpleNamespace(
        session_id=session_id,
        world_state=world_state,
    )
    fake_repo.evidence_items = [
        make_evidence_item(evidence_id=evidence_id)
    ]
    fake_repo.bear_claims = []

    with pytest.raises(HTTPException) as exc_info:
        await sessions_route.step_session(
            session_id=session_id,
            payload=StepSessionRequest(max_evidence_items=10),
            db=object(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == (
        "Cannot execute Bull rebuttal: no active Round 2 Bear opening "
        "claims exist for this session."
    )

    assert fake_repo.get_recent_claims_calls == [
        {
            "side": "bear",
            "limit": 3,
            "round_no": 2,
            "claim_type": "opening",
            "status": "active",
        }
    ]

    fake_planner.rebut.assert_not_awaited()
    fake_risk_agent.open_case.assert_not_awaited()
    fake_risk_agent.rebut.assert_not_awaited()
    fake_judge_agent.evaluate_debate.assert_not_awaited()

    assert fake_repo.insert_agent_action_calls == []
    assert fake_repo.insert_agent_claim_calls == []
    assert fake_repo.insert_control_checks_calls == []
    assert fake_repo.commit_calls == 0

@pytest.mark.asyncio
async def test_bear_rebuttal_uses_only_active_round_3_bull_rebuttals(
    route_fakes,
) -> None:
    fake_repo, fake_planner, fake_risk_agent, fake_judge_agent = route_fakes

    session_id = uuid4()
    evidence_id = uuid4()
    world_state = make_world_state()
    evidence_item = make_evidence_item(evidence_id=evidence_id)
    bull_rebuttal = make_round_3_bull_rebuttal(
        evidence_id=evidence_id,
        bear_claim_id=uuid4(),
    )
    bear_rebuttal = make_round_4_bear_rebuttal(
        evidence_id=evidence_id,
        bull_rebuttal_claim_id=bull_rebuttal.claim_id,
    )

    fake_repo.next_round_no = 4
    fake_repo.session = SimpleNamespace(
        session_id=session_id,
        world_state=world_state,
    )
    fake_repo.evidence_items = [evidence_item]
    fake_repo.recent_claims = [bull_rebuttal]

    expected_action = AgentAction(
        action_id=uuid4(),
        agent_name="risk_agent",
        action_type="rebut_bull_case",
        rationale=(
            "The Bull rebuttal narrows the case but does not resolve the "
            "material information gaps identified by the Bear."
        ),
        evidence_ids=[evidence_id],
        confidence=0.66,
        round_no=0,
    )
    expected_control_checks = [
        {
            "check_type": "evidence_citation",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "counterclaim_targeting",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "rebuttal_posture",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "uncertainty_disclosure",
            "status": "warn",
            "severity": "info",
            "details": {
                "information_gaps": [],
            },
        },
    ]

    fake_risk_agent.rebut.return_value = (
        expected_action,
        bear_rebuttal,
        expected_control_checks,
    )

    response = await sessions_route.step_session(
        session_id=session_id,
        payload=StepSessionRequest(max_evidence_items=10),
        db=object(),
    )

    assert response.step_status == "completed"
    assert response.phase == "bear_rebuttal"
    assert response.controls["round_no"] == 4
    assert response.controls["phase"] == "bear_rebuttal"

    assert fake_repo.get_recent_claims_calls == [
        {
            "side": "bull",
            "round_no": 3,
            "claim_type": "rebuttal",
            "status": "active",
            "limit": 3,
        }
    ]

    fake_risk_agent.rebut.assert_awaited_once_with(
        world_state=world_state,
        evidence_items=[evidence_item],
        opposing_claims=[bull_rebuttal],
    )
    fake_planner.rebut.assert_not_awaited()
    fake_risk_agent.open_case.assert_not_awaited()
    fake_judge_agent.evaluate_debate.assert_not_awaited()

    assert response.action.round_no == 4
    assert response.claim is not None
    assert response.claim.round_no == 4
    assert response.claim.side == "bear"
    assert response.claim.claim_type == "rebuttal"
    assert response.claim.target_claim_ids == [bull_rebuttal.claim_id]

    assert len(fake_repo.insert_agent_action_calls) == 1
    action_write = fake_repo.insert_agent_action_calls[0]
    assert action_write["session_id"] == session_id
    assert action_write["round_no"] == 4
    assert action_write["action"].round_no == 4
    assert action_write["action"].agent_name == "risk_agent"
    assert action_write["action"].action_type == "rebut_bull_case"

    assert len(fake_repo.insert_agent_claim_calls) == 1
    claim_write = fake_repo.insert_agent_claim_calls[0]
    assert claim_write["session_id"] == session_id
    assert claim_write["round_no"] == 4
    assert claim_write["claim"].round_no == 4
    assert claim_write["claim"].side == "bear"
    assert claim_write["claim"].claim_type == "rebuttal"
    assert claim_write["claim"].target_claim_ids == [
        bull_rebuttal.claim_id
    ]

    assert fake_repo.insert_control_checks_calls == [
        {
            "session_id": session_id,
            "control_checks": expected_control_checks,
        }
    ]
    assert fake_repo.commit_calls == 1

@pytest.mark.asyncio
async def test_bear_rebuttal_requires_active_round_3_bull_rebuttal(
    route_fakes,
) -> None:
    fake_repo, fake_planner, fake_risk_agent, fake_judge_agent = route_fakes

    session_id = uuid4()
    evidence_id = uuid4()

    fake_repo.next_round_no = 4
    fake_repo.session = SimpleNamespace(
        session_id=session_id,
        world_state=make_world_state(),
    )
    fake_repo.evidence_items = [
        make_evidence_item(evidence_id=evidence_id)
    ]
    fake_repo.recent_claims = []

    with pytest.raises(HTTPException) as exc_info:
        await sessions_route.step_session(
            session_id=session_id,
            payload=StepSessionRequest(max_evidence_items=10),
            db=object(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == (
        "Cannot execute Bear rebuttal: no active Round 3 Bull rebuttal "
        "claims exist for this session."
    )

    assert fake_repo.get_recent_claims_calls == [
        {
            "side": "bull",
            "round_no": 3,
            "claim_type": "rebuttal",
            "status": "active",
            "limit": 3,
        }
    ]

    fake_planner.rebut.assert_not_awaited()
    fake_risk_agent.open_case.assert_not_awaited()
    fake_risk_agent.rebut.assert_not_awaited()
    fake_judge_agent.evaluate_debate.assert_not_awaited()

    assert fake_repo.insert_agent_action_calls == []
    assert fake_repo.insert_agent_claim_calls == []
    assert fake_repo.insert_control_checks_calls == []
    assert fake_repo.commit_calls == 0

@pytest.mark.asyncio
async def test_judge_verdict_uses_completed_active_debate_and_persists_summary(
    route_fakes,
) -> None:
    fake_repo, fake_planner, fake_risk_agent, fake_judge_agent = route_fakes

    session_id = uuid4()
    evidence_id = uuid4()
    claims, actions = make_completed_debate(
        evidence_id=evidence_id,
    )

    fake_repo.next_round_no = 5
    fake_repo.session = SimpleNamespace(
        session_id=session_id,
        world_state=make_world_state(),
    )
    fake_repo.recent_claims = claims
    fake_repo.recent_actions = actions

    expected_action = AgentAction(
        action_id=uuid4(),
        round_no=0,
        agent_name="judge_agent",
        action_type="evaluate_debate",
        rationale=(
            "The record supports an inconclusive assessment because operating "
            "momentum is present, but valuation and margin evidence remain "
            "unresolved."
        ),
        evidence_ids=[evidence_id],
        confidence=0.56,
    )
    expected_claim = Claim(
        claim_id=uuid4(),
        round_no=0,
        side="judge",
        claim_type="verdict",
        thesis=(
            "inconclusive: Operating momentum is present, but the supplied "
            "record does not resolve valuation and margin uncertainty."
        ),
        confidence=0.56,
        evidence_ids=[evidence_id],
        target_claim_ids=[
            claims[0].claim_id,
            claims[2].claim_id,
            claims[3].claim_id,
        ],
        status="active",
    )
    expected_control_checks = [
        {
            "check_type": "distinct_evidence",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "contradiction_quality",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "unsupported_repetition",
            "status": "pass",
            "severity": "info",
            "details": {},
        },
        {
            "check_type": "judge_verdict",
            "status": "pass",
            "severity": "info",
            "details": {
                "verdict": "inconclusive",
            },
        },
    ]

    fake_judge_agent.evaluate_debate.return_value = (
        expected_action,
        expected_claim,
        expected_control_checks,
    )

    response = await sessions_route.step_session(
        session_id=session_id,
        payload=StepSessionRequest(max_evidence_items=10),
        db=object(),
    )

    assert response.step_status == "completed"
    assert response.phase == "judge_verdict"
    assert response.controls["round_no"] == 5
    assert response.controls["phase"] == "judge_verdict"
    assert response.controls["action_agent"] == "judge_agent"
    assert response.controls["checks_written"] == 4

    assert fake_repo.get_recent_claims_calls == [
        {
            "side": "bull",
            "round_no": 1,
            "claim_type": "opening",
            "status": "active",
            "limit": 1,
        },
        {
            "side": "bear",
            "round_no": 2,
            "claim_type": "opening",
            "status": "active",
            "limit": 1,
        },
        {
            "side": "bull",
            "round_no": 3,
            "claim_type": "rebuttal",
            "status": "active",
            "limit": 1,
        },
        {
            "side": "bear",
            "round_no": 4,
            "claim_type": "rebuttal",
            "status": "active",
            "limit": 1,
        },
    ]
    assert fake_repo.get_recent_actions_calls == [{"limit": 8}]

    fake_judge_agent.evaluate_debate.assert_awaited_once_with(
        recent_claims=claims,
        recent_actions=actions,
    )
    fake_planner.rebut.assert_not_awaited()
    fake_risk_agent.open_case.assert_not_awaited()
    fake_risk_agent.rebut.assert_not_awaited()

    assert response.action.round_no == 5
    assert response.action.agent_name == "judge_agent"
    assert response.action.action_type == "evaluate_debate"

    assert response.claim is not None
    assert response.claim.round_no == 5
    assert response.claim.side == "judge"
    assert response.claim.claim_type == "verdict"
    assert response.claim.thesis.startswith("inconclusive:")

    assert len(fake_repo.insert_agent_action_calls) == 1
    action_write = fake_repo.insert_agent_action_calls[0]
    assert action_write["session_id"] == session_id
    assert action_write["round_no"] == 5
    assert action_write["action"].round_no == 5
    assert action_write["action"].agent_name == "judge_agent"
    assert action_write["action"].action_type == "evaluate_debate"

    assert len(fake_repo.insert_agent_claim_calls) == 1
    claim_write = fake_repo.insert_agent_claim_calls[0]
    assert claim_write["session_id"] == session_id
    assert claim_write["round_no"] == 5
    assert claim_write["claim"].round_no == 5
    assert claim_write["claim"].side == "judge"
    assert claim_write["claim"].claim_type == "verdict"

    assert fake_repo.insert_control_checks_calls == [
        {
            "session_id": session_id,
            "control_checks": expected_control_checks,
        }
    ]

    assert len(fake_repo.insert_memory_episodes_calls) == 1
    memory_write = fake_repo.insert_memory_episodes_calls[0]
    assert memory_write["session_id"] == session_id
    assert len(memory_write["episodes"]) == 1

    episode = memory_write["episodes"][0]
    assert episode["episode_type"] == "judge_summary"
    assert episode["payload"]["judge_confidence"] == 0.56
    assert episode["payload"]["judge_claim"] == (
        "inconclusive: Operating momentum is present, but the supplied "
        "record does not resolve valuation and margin uncertainty."
    )
    assert episode["payload"]["checks"] == expected_control_checks

    assert fake_repo.commit_calls == 1

@pytest.mark.asyncio
async def test_judge_verdict_requires_all_active_debate_turns(
    route_fakes,
) -> None:
    fake_repo, fake_planner, fake_risk_agent, fake_judge_agent = route_fakes

    session_id = uuid4()
    evidence_id = uuid4()
    claims, actions = make_completed_debate(
        evidence_id=evidence_id,
    )

    fake_repo.next_round_no = 5
    fake_repo.session = SimpleNamespace(
        session_id=session_id,
        world_state=make_world_state(),
    )
    fake_repo.recent_claims = claims[:3]
    fake_repo.recent_actions = actions

    with pytest.raises(HTTPException) as exc_info:
        await sessions_route.step_session(
            session_id=session_id,
            payload=StepSessionRequest(max_evidence_items=10),
            db=object(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == (
        "Cannot execute Judge verdict: missing active Round 4 Bear rebuttal "
        "claim for this session."
    )

    assert fake_repo.get_recent_claims_calls == [
        {
            "side": "bull",
            "round_no": 1,
            "claim_type": "opening",
            "status": "active",
            "limit": 1,
        },
        {
            "side": "bear",
            "round_no": 2,
            "claim_type": "opening",
            "status": "active",
            "limit": 1,
        },
        {
            "side": "bull",
            "round_no": 3,
            "claim_type": "rebuttal",
            "status": "active",
            "limit": 1,
        },
        {
            "side": "bear",
            "round_no": 4,
            "claim_type": "rebuttal",
            "status": "active",
            "limit": 1,
        },
    ]

    assert fake_repo.get_recent_actions_calls == []
    fake_judge_agent.evaluate_debate.assert_not_awaited()

    assert fake_repo.insert_agent_action_calls == []
    assert fake_repo.insert_agent_claim_calls == []
    assert fake_repo.insert_control_checks_calls == []
    assert fake_repo.insert_memory_episodes_calls == []
    assert fake_repo.commit_calls == 0