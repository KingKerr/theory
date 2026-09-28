from datetime import date, datetime, timezone
from uuid import UUID

from core_api.models.domain import Claim, EvidenceItem, WorldState
from core_api.services.debate.evidence_packet import build_bear_evidence_packet


world_state = WorldState(
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

evidence_id = UUID("11111111-1111-1111-1111-111111111111")
claim_id = UUID("22222222-2222-2222-2222-222222222222")

evidence_items = [
    EvidenceItem(
        evidence_id=evidence_id,
        source_type="demo",
        source_ref=None,
        observed_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
        title="Demonstration evidence",
        summary="Revenue grew year over year while guidance was maintained.",
        payload={},
        freshness_score=0.95,
        confidence=0.90,
    )
]

opposing_claims = [
    Claim(
        claim_id=claim_id,
        round_no=1,
        side="bull",
        thesis=(
            "Maintained guidance and revenue growth support a constructive "
            "near-term operating outlook."
        ),
        confidence=0.70,
        evidence_ids=[evidence_id],
        status="active",
    )
]

print(
    build_bear_evidence_packet(
        world_state=world_state,
        evidence_items=evidence_items,
        opposing_claims=opposing_claims,
    )
)