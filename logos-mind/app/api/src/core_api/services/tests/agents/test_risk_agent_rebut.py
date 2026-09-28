from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from core_api.models.debate import (
    BearRebuttalClaimOutput,
    BearRebuttalOutput,
)
from core_api.models.domain import (
    Claim,
    EvidenceItem,
    WorldState,
)
from core_api.services.agents.risk_agent import RiskAgentService


class FakeLLMClient:
    def __init__(self, output: BearRebuttalOutput) -> None:
        self.output = output
        self.calls: list[dict] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BearRebuttalOutput],
    ) -> BearRebuttalOutput:
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
        state_version="test-risk-rebuttal-v1",
    )


def make_evidence_item(*, evidence_id: UUID) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_type="test",
        source_ref="test://risk-agent-rebuttal-evidence",
        observed_at=datetime(2026, 9, 26, tzinfo=timezone.utc),
        title="Test evidence",
        summary=(
            "Revenue grew year over year and guidance was maintained. "
            "The packet does not contain valuation, margin, or conversion details."
        ),
        freshness_score=0.95,
        confidence=0.95,
    )


def make_bull_rebuttal_claim(
    *,
    claim_id: UUID,
    evidence_id: UUID,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        round_no=3,
        side="bull",
        claim_type="rebuttal",
        thesis=(
            "Maintained guidance and year-over-year revenue growth support "
            "the operating trajectory, although missing margin and valuation "
            "evidence limits the scope of the constructive conclusion."
        ),
        confidence=0.62,
        evidence_ids=[evidence_id],
        target_claim_ids=[uuid4()],
        status="active",
    )


def make_bull_opening_claim(
    *,
    claim_id: UUID,
    evidence_id: UUID,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        round_no=1,
        side="bull",
        claim_type="opening",
        thesis=(
            "Revenue growth and maintained guidance support a constructive "
            "operating outlook."
        ),
        confidence=0.70,
        evidence_ids=[evidence_id],
        target_claim_ids=[],
        status="active",
    )


def make_rebuttal_output(
    *,
    evidence_id: UUID,
    bull_claim_id: UUID,
) -> BearRebuttalOutput:
    return BearRebuttalOutput(
        rationale=(
            "Maintained guidance and revenue growth support a limited "
            "operating conclusion, but they do not resolve the missing "
            "valuation, margin, or customer-conversion evidence."
        ),
        confidence=0.66,
        claims=[
            BearRebuttalClaimOutput(
                thesis=(
                    "The Bull rebuttal appropriately narrows its conclusion, "
                    "but the remaining evidence still does not establish that "
                    "growth translates into durable or attractively valued "
                    "economics."
                ),
                confidence=0.66,
                evidence_ids=[evidence_id],
                target_claim_ids=[bull_claim_id],
                response_type="challenge",
                information_gaps=[
                    "The packet does not include margin, valuation, or conversion data."
                ],
            )
        ],
        information_gaps=[
            "The packet does not include margin, valuation, or conversion data."
        ],
    )


@pytest.mark.asyncio
async def test_rebut_returns_bear_claim_targeting_supplied_bull_rebuttal() -> None:
    evidence_id = uuid4()
    bull_rebuttal_claim_id = uuid4()

    evidence_items = [make_evidence_item(evidence_id=evidence_id)]
    bull_rebuttal_claim = make_bull_rebuttal_claim(
        claim_id=bull_rebuttal_claim_id,
        evidence_id=evidence_id,
    )

    llm_client = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bull_claim_id=bull_rebuttal_claim_id,
        )
    )
    service = RiskAgentService(llm_client=llm_client)

    action, claim, control_checks = await service.rebut(
        world_state=make_world_state(),
        evidence_items=evidence_items,
        opposing_claims=[bull_rebuttal_claim],
    )

    assert len(llm_client.calls) == 1

    assert action.agent_name == "risk_agent"
    assert action.action_type == "rebut_bull_case"
    assert action.evidence_ids == [evidence_id]
    assert action.confidence == 0.66

    assert claim is not None
    assert claim.side == "bear"
    assert claim.claim_type == "rebuttal"
    assert claim.evidence_ids == [evidence_id]
    assert claim.target_claim_ids == [bull_rebuttal_claim_id]
    assert claim.status == "active"

    assert [check["check_type"] for check in control_checks] == [
        "evidence_citation",
        "counterclaim_targeting",
        "rebuttal_posture",
        "uncertainty_disclosure",
    ]

    targeting_check = next(
        check
        for check in control_checks
        if check["check_type"] == "counterclaim_targeting"
    )
    assert targeting_check["status"] == "pass"
    assert targeting_check["details"]["targeted_bull_claim_ids"] == [
        str(bull_rebuttal_claim_id)
    ]

    posture_check = next(
        check
        for check in control_checks
        if check["check_type"] == "rebuttal_posture"
    )
    assert posture_check["details"]["response_types"] == ["challenge"]


@pytest.mark.asyncio
async def test_rebut_rejects_evidence_not_in_supplied_packet() -> None:
    valid_evidence_id = uuid4()
    invalid_evidence_id = uuid4()
    bull_claim_id = uuid4()

    bull_rebuttal_claim = make_bull_rebuttal_claim(
        claim_id=bull_claim_id,
        evidence_id=valid_evidence_id,
    )
    output = make_rebuttal_output(
        evidence_id=invalid_evidence_id,
        bull_claim_id=bull_claim_id,
    )

    service = RiskAgentService(llm_client=FakeLLMClient(output))

    with pytest.raises(
        ValueError,
        match="Bear rebuttal cited evidence outside the supplied session packet",
    ) as exc_info:
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[
                make_evidence_item(evidence_id=valid_evidence_id)
            ],
            opposing_claims=[bull_rebuttal_claim],
        )

    assert str(invalid_evidence_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_rebut_rejects_target_not_in_supplied_bull_claim_set() -> None:
    evidence_id = uuid4()
    valid_bull_claim_id = uuid4()
    invalid_target_claim_id = uuid4()

    bull_rebuttal_claim = make_bull_rebuttal_claim(
        claim_id=valid_bull_claim_id,
        evidence_id=evidence_id,
    )
    output = make_rebuttal_output(
        evidence_id=evidence_id,
        bull_claim_id=invalid_target_claim_id,
    )

    service = RiskAgentService(llm_client=FakeLLMClient(output))

    with pytest.raises(
        ValueError,
        match="Bear rebuttal targeted claims outside the supplied Bull claim set",
    ) as exc_info:
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[make_evidence_item(evidence_id=evidence_id)],
            opposing_claims=[bull_rebuttal_claim],
        )

    assert str(invalid_target_claim_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_rebut_requires_evidence_before_calling_llm() -> None:
    evidence_id = uuid4()
    bull_claim_id = uuid4()
    fake_llm = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bull_claim_id=bull_claim_id,
        )
    )
    service = RiskAgentService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Bear rebuttal requires at least one evidence item",
    ):
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[],
            opposing_claims=[
                make_bull_rebuttal_claim(
                    claim_id=bull_claim_id,
                    evidence_id=evidence_id,
                )
            ],
        )

    assert fake_llm.calls == []


@pytest.mark.asyncio
async def test_rebut_requires_bull_claim_before_calling_llm() -> None:
    evidence_id = uuid4()
    bull_claim_id = uuid4()
    fake_llm = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bull_claim_id=bull_claim_id,
        )
    )
    service = RiskAgentService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Bear rebuttal requires at least one active Round 3 Bull rebuttal claim",
    ):
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[make_evidence_item(evidence_id=evidence_id)],
            opposing_claims=[],
        )

    assert fake_llm.calls == []


@pytest.mark.asyncio
async def test_rebut_rejects_targeting_bull_opening_present_in_input() -> None:
    evidence_id = uuid4()
    bull_rebuttal_claim_id = uuid4()
    bull_opening_claim_id = uuid4()

    evidence_item = make_evidence_item(evidence_id=evidence_id)

    bull_rebuttal_claim = make_bull_rebuttal_claim(
        claim_id=bull_rebuttal_claim_id,
        evidence_id=evidence_id,
    )
    bull_opening_claim = make_bull_opening_claim(
        claim_id=bull_opening_claim_id,
        evidence_id=evidence_id,
    )

    fake_llm = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bull_claim_id=bull_opening_claim_id,
        )
    )
    service = RiskAgentService(llm_client=fake_llm)
    with pytest.raises(
        ValueError,
        match="outside the supplied Bull claim set",
    ) as exc_info:
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[evidence_item],
            opposing_claims=[
                bull_rebuttal_claim,
                bull_opening_claim,
            ],
        )
    assert str(bull_opening_claim_id) in str(exc_info.value)