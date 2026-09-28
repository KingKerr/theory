import asyncio

from core_api.models.debate import BearTurnOutput
from core_api.services.llm.client import LLMClient


SYSTEM_PROMPT = """
You are the Bear agent in Theory.

Use only the supplied payload. Every Bear claim must cite an evidence_id from
the evidence packet and target a claim_id from opposing_claims. Do not provide
investment advice. Return a complete schema-valid response.
"""


USER_PROMPT = """
{
  "world_state": {
    "security": {
      "ticker": "DEMO",
      "as_of_date": "2026-09-26"
    }
  },
  "evidence_packet": [
    {
      "evidence_id": "11111111-1111-1111-1111-111111111111",
      "source_type": "demo",
      "observed_at": "2026-09-25T00:00:00Z",
      "title": "Demonstration update",
      "summary": "Revenue grew year over year and annual guidance was maintained. The update does not include margin, valuation, or customer-conversion information.",
      "freshness_score": 0.95,
      "confidence": 0.95
    }
  ],
  "opposing_claims": [
    {
      "claim_id": "22222222-2222-2222-2222-222222222222",
      "round_no": 1,
      "side": "bull",
      "thesis": "Maintained guidance and revenue growth support a constructive near-term operating outlook.",
      "confidence": 0.70,
      "evidence_ids": [
        "11111111-1111-1111-1111-111111111111"
      ],
      "status": "active"
    }
  ]
}
"""


async def main() -> None:
    client = LLMClient()

    result = await client.generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        response_model=BearTurnOutput,
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())