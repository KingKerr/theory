from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from core_api.core.config import get_settings


T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.CHAT_MODEL

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
    ) -> T:
        completion = await self.client.chat.completions.parse(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format=response_model,
        )

        message = completion.choices[0].message

        if message.refusal:
            raise RuntimeError(f"OpenAI refused the request: {message.refusal}")

        if message.parsed is None:
            raise RuntimeError("OpenAI returned no parsed structured response.")

        return message.parsed