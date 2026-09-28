import asyncio

from core_api.models.debate import BullTurnOutput
from core_api.services.llm.client import LLMClient


SYSTEM_PROMPT = """
You are the constructive-analysis agent in Theory.

Use only supplied evidence. Do not provide investment advice. Every claim must
cite the exact evidence_id included in the evidence packet. Return a complete,
schema-valid response.
"""


USER_PROMPT = """
{
  "world_state": {
    "security": {
      "ticker": "DEMO",
      "as_of_date": "2026-09-25"
    }
  },
  "evidence_packet": [
    {
      "evidence_id": "11111111-1111-1111-1111-111111111111",
      "source_type": "demo",
      "observed_at": "2026-09-24T00:00:00Z",
      "title": "Demonstration revenue update",
      "summary": "The company reported year-over-year revenue growth and maintained its annual guidance.",
      "freshness_score": 0.95,
      "confidence": 0.95
    }
  ]
}
"""


async def main() -> None:
    client = LLMClient()

    result = await client.generate_structured(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT,
        response_model=BullTurnOutput,
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())