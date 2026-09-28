from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from core_api.models.debate import (
    BearClaimOutput,
    BearRebuttalClaimOutput,
    BearRebuttalOutput,
    BearTurnOutput,
    BullTurnOutput,
    DebateClaimOutput,
)
from core_api.models.domain import Claim, EvidenceItem, WorldState
from core_api.services.agents.planner import PlannerService
from core_api.services.agents.risk_agent import RiskAgentService


class FakeLLMClient:
    def __init__(self, output: object) -> None:
        self.output = output
        self.calls: list[dict] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type,
    ) -> object:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_model": response_model,
            }
        )
        return self.output


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
        state_version="agent-test-v1",
    )


def make_evidence_item(
    *,
    evidence_id: UUID,
    source_type: str = "test",
    summary: str = (
        "Revenue grew year over year and management maintained guidance."
    ),
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_type=source_type,
        source_ref=f"test://{source_type}/{evidence_id}",
        observed_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
        title=f"{source_type} evidence",
        summary=summary,
        freshness_score=0.95,
        confidence=0.95,
    )


@pytest.mark.asyncio
async def test_planner_builds_bull_opening_from_structured_output() -> None:
    evidence_id = uuid4()
    evidence_items = [
        make_evidence_item(evidence_id=evidence_id),
    ]

    output = BullTurnOutput(
        rationale=(
            "The supplied evidence indicates revenue momentum and maintained "
            "guidance, supporting a narrow constructive interpretation."
        ),
        confidence=0.64,
        claims=[
            DebateClaimOutput(
                thesis=(
                    "Reported revenue growth and maintained guidance support "
                    "a constructive operating interpretation."
                ),
                confidence=0.62,
                evidence_ids=[evidence_id],
                information_gaps=[
                    "The packet does not include valuation or margin evidence."
                ],
            )
        ],
        information_gaps=[
            "The packet does not include valuation or margin evidence."
        ],
    )
    fake_llm = FakeLLMClient(output)
    planner = PlannerService(llm_client=fake_llm)

    action, claim, control_checks = await planner.step_from_evidence(
        world_state=make_world_state(),
        evidence_items=evidence_items,
    )

    assert len(fake_llm.calls) == 1
    assert fake_llm.calls[0]["response_model"] is BullTurnOutput

    assert action.agent_name == "planner"
    assert action.action_type == "advance_bull_case"
    assert action.evidence_ids == [evidence_id]
    assert action.confidence == 0.64

    assert claim is not None
    assert claim.side == "bull"
    assert claim.claim_type == "opening"
    assert claim.thesis == (
        "Reported revenue growth and maintained guidance support "
        "a constructive operating interpretation."
    )
    assert claim.confidence == 0.62
    assert claim.evidence_ids == [evidence_id]
    assert claim.target_claim_ids == []
    assert claim.status == "active"

    assert control_checks == [
        {
            "check_type": "evidence_citation",
            "status": "pass",
            "severity": "info",
            "details": {
                "generated_claim_count": 1,
                "cited_evidence_count": 1,
                "invalid_evidence_ids": [],
            },
        },
        {
            "check_type": "uncertainty_disclosure",
            "status": "pass",
            "severity": "info",
            "details": {
                "information_gaps": [
                    "The packet does not include valuation or margin evidence."
                ],
            },
        },
    ]


@pytest.mark.asyncio
async def test_risk_agent_builds_bear_opening_targeting_bull_claim() -> None:
    evidence_id = uuid4()
    bull_claim_id = uuid4()

    evidence_items = [
        make_evidence_item(
            evidence_id=evidence_id,
            source_type="risk_signal",
            summary=(
                "The supplied packet lacks valuation, margin, and cash-flow "
                "evidence needed to validate durable economics."
            ),
        ),
    ]
    bull_claim = Claim(
        claim_id=bull_claim_id,
        round_no=1,
        side="bull",
        claim_type="opening",
        thesis=(
            "Revenue growth and maintained guidance support a constructive "
            "operating outlook."
        ),
        confidence=0.64,
        evidence_ids=[evidence_id],
        target_claim_ids=[],
        status="active",
    )

    output = BearTurnOutput(
        rationale=(
            "The Bull claim is not disproven, but the supplied evidence lacks "
            "the valuation, margin, and cash-flow support needed to validate "
            "durable economics."
        ),
        confidence=0.68,
        claims=[
            BearClaimOutput(
                thesis=(
                    "The supplied record does not establish durable economics "
                    "because valuation, margin, and cash-flow support are absent."
                ),
                confidence=0.67,
                evidence_ids=[evidence_id],
                target_claim_ids=[bull_claim_id],
                information_gaps=[
                    "No margin, valuation, or cash-flow evidence was supplied."
                ],
            )
        ],
        information_gaps=[
            "No margin, valuation, or cash-flow evidence was supplied."
        ],
    )
    fake_llm = FakeLLMClient(output)
    risk_agent = RiskAgentService(llm_client=fake_llm)

    action, claim, control_checks = await risk_agent.open_case(
        world_state=make_world_state(),
        evidence_items=evidence_items,
        opposing_claims=[bull_claim],
    )

    assert len(fake_llm.calls) == 1
    assert fake_llm.calls[0]["response_model"] is BearTurnOutput

    assert action.agent_name == "risk_agent"
    assert action.action_type == "advance_bear_case"
    assert action.evidence_ids == [evidence_id]
    assert action.confidence == 0.68

    assert claim is not None
    assert claim.side == "bear"
    assert claim.claim_type == "opening"
    assert claim.target_claim_ids == [bull_claim_id]
    assert claim.evidence_ids == [evidence_id]
    assert claim.confidence == 0.67
    assert claim.status == "active"

    assert control_checks == [
        {
            "check_type": "evidence_citation",
            "status": "pass",
            "severity": "info",
            "details": {
                "generated_claim_count": 1,
                "cited_evidence_count": 1,
                "invalid_evidence_ids": [],
            },
        },
        {
            "check_type": "counterclaim_targeting",
            "status": "pass",
            "severity": "info",
            "details": {
                "targeted_bull_claim_ids": [str(bull_claim_id)],
                "targeted_bull_claim_count": 1,
                "invalid_target_claim_ids": [],
            },
        },
        {
            "check_type": "uncertainty_disclosure",
            "status": "pass",
            "severity": "info",
            "details": {
                "information_gaps": [
                    "No margin, valuation, or cash-flow evidence was supplied."
                ],
            },
        },
    ]


@pytest.mark.asyncio
async def test_risk_agent_rebuttal_rejects_evidence_outside_supplied_packet() -> None:
    supplied_evidence_id = uuid4()
    unsupplied_evidence_id = uuid4()
    bull_rebuttal_claim_id = uuid4()

    evidence_items = [
        make_evidence_item(
            evidence_id=supplied_evidence_id,
        ),
    ]
    bull_rebuttal = Claim(
        claim_id=bull_rebuttal_claim_id,
        round_no=3,
        side="bull",
        claim_type="rebuttal",
        thesis=(
            "Maintained guidance supports the operating trajectory despite "
            "the acknowledged data gaps."
        ),
        confidence=0.61,
        evidence_ids=[supplied_evidence_id],
        target_claim_ids=[uuid4()],
        status="active",
    )

    output = BearRebuttalOutput(
        rationale=(
            "The cited information does not resolve the margin, valuation, "
            "and cash-flow gaps identified by the Bear case."
        ),
        confidence=0.66,
        claims=[
            BearRebuttalClaimOutput(
                thesis=(
                    "The constructive rebuttal remains unproven because "
                    "durable economics are not established by the record."
                ),
                confidence=0.65,
                evidence_ids=[unsupplied_evidence_id],
                target_claim_ids=[bull_rebuttal_claim_id],
                response_type="challenge",
                information_gaps=[
                    "No valuation or margin evidence was supplied."
                ],
            )
        ],
        information_gaps=[
            "No valuation or margin evidence was supplied."
        ],
    )
    fake_llm = FakeLLMClient(output)
    risk_agent = RiskAgentService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Bear rebuttal cited evidence outside the supplied session packet",
    ) as exc_info:
        await risk_agent.rebut(
            world_state=make_world_state(),
            evidence_items=evidence_items,
            opposing_claims=[bull_rebuttal],
        )

    assert str(unsupplied_evidence_id) in str(exc_info.value)
    assert len(fake_llm.calls) == 1
    assert fake_llm.calls[0]["response_model"] is BearRebuttalOutput