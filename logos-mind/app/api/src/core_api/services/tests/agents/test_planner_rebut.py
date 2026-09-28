from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest

from core_api.models.debate import (
    BullRebuttalClaimOutput,
    BullRebuttalOutput,
)
from core_api.models.domain import (
    Claim,
    EvidenceItem,
    WorldState,
)


from core_api.services.agents.planner import PlannerService


class FakeLLMClient:
    def __init__(self, output: BullRebuttalOutput) -> None:
        self.output = output
        self.calls: list[dict] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BullRebuttalOutput],
    ) -> BullRebuttalOutput:
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
            "as_of_date": date(2026, 9, 26),
        },
        market_state={},
        fundamental_state={},
        event_state={},
        peer_state={},
        state_version="test-state-v1",
    )


def make_evidence_item(*, evidence_id: UUID) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        source_type="test",
        source_ref="test://rebuttal-evidence",
        observed_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
        title="Test evidence",
        summary=(
            "Revenue grew year over year and guidance was maintained. "
            "The packet does not contain valuation or margin details."
        ),
        freshness_score=0.95,
        confidence=0.95,
    )


def make_bear_claim(*, claim_id: UUID, evidence_id: UUID) -> Claim:
    return Claim(
        claim_id=claim_id,
        round_no=2,
        side="bear",
        claim_type="opening",
        thesis=(
            "The constructive outlook may overstate durability because the "
            "packet lacks valuation, margin, and conversion evidence."
        ),
        confidence=0.67,
        evidence_ids=[evidence_id],
        target_claim_ids=[uuid4()],
        status="active",
    )


def make_rebuttal_output(
    *,
    evidence_id: UUID,
    bear_claim_id: UUID,
) -> BullRebuttalOutput:
    return BullRebuttalOutput(
        rationale=(
            "Maintained guidance and year-over-year revenue growth support "
            "the operating trajectory, while the missing margin and valuation "
            "information limits the scope of the constructive conclusion."
        ),
        confidence=0.62,
        claims=[
            BullRebuttalClaimOutput(
                thesis=(
                    "Maintained guidance and year-over-year revenue growth "
                    "support the operating trajectory, though the investment "
                    "case should remain limited until margin and valuation "
                    "evidence is available."
                ),
                confidence=0.62,
                evidence_ids=[evidence_id],
                target_claim_ids=[bear_claim_id],
                response_type="narrow",
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
async def test_rebut_returns_bull_claim_targeting_supplied_bear_claim() -> None:
    evidence_id = uuid4()
    bear_claim_id = uuid4()

    evidence_items = [make_evidence_item(evidence_id=evidence_id)]
    bear_claim = make_bear_claim(
        claim_id=bear_claim_id,
        evidence_id=evidence_id,
    )

    llm_client = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bear_claim_id=bear_claim_id,
        )
    )
    service = PlannerService(llm_client=llm_client)

    action, claim, control_checks = await service.rebut(
        world_state=make_world_state(),
        evidence_items=evidence_items,
        opposing_claims=[bear_claim],
    )

    assert len(llm_client.calls) == 1

    assert action.agent_name == "planner"
    assert action.action_type == "rebut_bear_case"
    assert action.evidence_ids == [evidence_id]
    assert action.confidence == 0.62

    assert claim is not None
    assert claim.side == "bull"
    assert claim.claim_type == "rebuttal"
    assert claim.evidence_ids == [evidence_id]
    assert claim.target_claim_ids == [bear_claim_id]
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
    assert targeting_check["details"]["targeted_bear_claim_ids"] == [
        str(bear_claim_id)
    ]

    posture_check = next(
        check
        for check in control_checks
        if check["check_type"] == "rebuttal_posture"
    )
    assert posture_check["details"]["response_types"] == ["narrow"]


@pytest.mark.asyncio
async def test_rebut_rejects_evidence_not_in_supplied_packet() -> None:
    valid_evidence_id = uuid4()
    invalid_evidence_id = uuid4()
    bear_claim_id = uuid4()

    bear_claim = make_bear_claim(
        claim_id=bear_claim_id,
        evidence_id=valid_evidence_id,
    )
    output = make_rebuttal_output(
        evidence_id=invalid_evidence_id,
        bear_claim_id=bear_claim_id,
    )

    service = PlannerService(llm_client=FakeLLMClient(output))

    with pytest.raises(
        ValueError,
        match="Bull rebuttal cited evidence outside the supplied session packet",
    ) as exc_info:
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[make_evidence_item(evidence_id=valid_evidence_id)],
            opposing_claims=[bear_claim],
        )

    assert str(invalid_evidence_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_rebut_rejects_target_not_in_supplied_bear_claim_set() -> None:
    evidence_id = uuid4()
    valid_bear_claim_id = uuid4()
    invalid_target_claim_id = uuid4()

    bear_claim = make_bear_claim(
        claim_id=valid_bear_claim_id,
        evidence_id=evidence_id,
    )
    output = make_rebuttal_output(
        evidence_id=evidence_id,
        bear_claim_id=invalid_target_claim_id,
    )

    service = PlannerService(llm_client=FakeLLMClient(output))

    with pytest.raises(
        ValueError,
        match="Bull rebuttal targeted claims outside the supplied Bear claim set",
    ) as exc_info:
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[make_evidence_item(evidence_id=evidence_id)],
            opposing_claims=[bear_claim],
        )

    assert str(invalid_target_claim_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_rebut_requires_evidence_before_calling_llm() -> None:
    evidence_id = uuid4()
    bear_claim_id = uuid4()
    fake_llm = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bear_claim_id=bear_claim_id,
        )
    )
    service = PlannerService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Bull rebuttal requires at least one evidence item",
    ):
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[],
            opposing_claims=[
                make_bear_claim(
                    claim_id=bear_claim_id,
                    evidence_id=evidence_id,
                )
            ],
        )

    assert fake_llm.calls == []


@pytest.mark.asyncio
async def test_rebut_requires_bear_claim_before_calling_llm() -> None:
    evidence_id = uuid4()
    bear_claim_id = uuid4()
    fake_llm = FakeLLMClient(
        make_rebuttal_output(
            evidence_id=evidence_id,
            bear_claim_id=bear_claim_id,
        )
    )
    service = PlannerService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Bull rebuttal requires at least one Bear claim",
    ):
        await service.rebut(
            world_state=make_world_state(),
            evidence_items=[make_evidence_item(evidence_id=evidence_id)],
            opposing_claims=[],
        )

    assert fake_llm.calls == []