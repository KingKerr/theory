from uuid import UUID

from core_api.models.debate import BearTurnOutput


bull_claim_id = UUID("22222222-2222-2222-2222-222222222222")
evidence_id = UUID("11111111-1111-1111-1111-111111111111")


result = BearTurnOutput(
    rationale=(
        "The available evidence does not establish that the commercial trend "
        "will translate into durable company-level revenue or margin gains."
    ),
    confidence=0.62,
    claims=[
        {
            "thesis": (
                "The Bull thesis may overstate the revenue implications of "
                "brand exposure because the supplied evidence does not quantify "
                "company-level conversion, revenue, or margin impact."
            ),
            "confidence": 0.68,
            "evidence_ids": [evidence_id],
            "target_claim_ids": [bull_claim_id],
            "information_gaps": [
                "No company-specific conversion or segment-revenue data is supplied."
            ],
        }
    ],
    information_gaps=[
        "The packet lacks direct profitability and valuation context."
    ],
)

print(result.model_dump_json(indent=2))