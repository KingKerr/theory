import pytest
import asyncio
from datetime import date, datetime, timezone
from uuid import UUID

from core_api.models.debate import BearTurnOutput
from core_api.models.domain import Claim, EvidenceItem, WorldState
from core_api.services.agents.risk_agent import RiskAgentService


EVIDENCE_ID = UUID("11111111-1111-1111-1111-111111111111")
BULL_CLAIM_ID = UUID("22222222-2222-2222-2222-222222222222")


class FakeLLMClient:
    def __init__(self, output: BearTurnOutput) -> None:
        self.output = output

    async def generate_structured(self, **kwargs) -> BearTurnOutput:
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
        state_version="v1",
    )


def make_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            evidence_id=EVIDENCE_ID,
            source_type="demo",
            source_ref=None,
            observed_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
            title="Demonstration evidence",
            summary=(
                "Revenue grew year over year and guidance was maintained, "
                "but margin, valuation, and conversion information was absent."
            ),
            payload={},
            freshness_score=0.95,
            confidence=0.90,
        )
    ]


def make_bull_claims() -> list[Claim]:
    return [
        Claim(
            claim_id=BULL_CLAIM_ID,
            round_no=1,
            side="bull",
            thesis=(
                "Maintained guidance and revenue growth support a constructive "
                "near-term operating outlook."
            ),
            confidence=0.70,
            evidence_ids=[EVIDENCE_ID],
            status="active",
        )
    ]


def make_valid_output() -> BearTurnOutput:
    return BearTurnOutput(
        rationale=(
            "The current evidence supports growth and maintained guidance, but "
            "does not establish valuation support, margin durability, or direct "
            "company-level conversion from that growth."
        ),
        confidence=0.64,
        claims=[
            {
                "thesis": (
                    "The Bull case may overstate the durability of the operating "
                    "outlook because the supplied evidence lacks margin, valuation, "
                    "and conversion data needed to connect growth to durable economics."
                ),
                "confidence": 0.67,
                "evidence_ids": [EVIDENCE_ID],
                "target_claim_ids": [BULL_CLAIM_ID],
                "information_gaps": [
                    "No margin, valuation, or conversion data is in the packet."
                ],
            }
        ],
        information_gaps=[
            "The packet does not include profitability or valuation context."
        ],
    )

@pytest.mark.asyncio
async def test_valid_bear_turn() -> None:
    service = RiskAgentService(
        llm_client=FakeLLMClient(make_valid_output())
    )

    action, claim, controls = await service.open_case(
        world_state=make_world_state(),
        evidence_items=make_evidence(),
        opposing_claims=make_bull_claims(),
    )

    assert action.agent_name == "risk_agent"
    assert action.action_type == "advance_bear_case"
    assert action.evidence_ids == [EVIDENCE_ID]

    assert claim is not None
    assert claim.side == "bear"
    assert claim.evidence_ids == [EVIDENCE_ID]

    assert len(controls) == 3
    assert controls[0]["check_type"] == "evidence_citation"
    assert controls[1]["check_type"] == "counterclaim_targeting"
    assert controls[1]["details"]["targeted_bull_claim_ids"] == [str(BULL_CLAIM_ID)]

    print("PASS: valid Bear turn creates a cited Bear action, claim, and controls.")

@pytest.mark.asyncio
async def test_invalid_evidence_rejected() -> None:
    invalid_evidence_id = UUID("33333333-3333-3333-3333-333333333333")
    invalid_output = make_valid_output()
    invalid_output.claims[0].evidence_ids = [invalid_evidence_id]

    service = RiskAgentService(llm_client=FakeLLMClient(invalid_output))

    try:
        await service.open_case(
            world_state=make_world_state(),
            evidence_items=make_evidence(),
            opposing_claims=make_bull_claims(),
        )
    except ValueError as error:
        assert "evidence outside the supplied session packet" in str(error)
        print("PASS: invalid evidence ID is rejected.")
        return

    raise AssertionError("Expected invalid evidence ID to be rejected.")

@pytest.mark.asyncio
async def test_invalid_target_claim_rejected() -> None:
    invalid_claim_id = UUID("44444444-4444-4444-4444-444444444444")
    invalid_output = make_valid_output()
    invalid_output.claims[0].target_claim_ids = [invalid_claim_id]

    service = RiskAgentService(llm_client=FakeLLMClient(invalid_output))

    try:
        await service.open_case(
            world_state=make_world_state(),
            evidence_items=make_evidence(),
            opposing_claims=make_bull_claims(),
        )
    except ValueError as error:
        assert "targeted claims outside the supplied Bull claim set" in str(error)
        print("PASS: invalid target claim ID is rejected.")
        return

    raise AssertionError("Expected invalid target claim ID to be rejected.")


async def main() -> None:
    await test_valid_bear_turn()
    await test_invalid_evidence_rejected()
    await test_invalid_target_claim_rejected()
    print("Bear validation boundary passed.")


if __name__ == "__main__":
    asyncio.run(main())