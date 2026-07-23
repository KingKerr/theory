import httpx
from typing import Any
from core_api.core.config import get_settings


settings = get_settings()


class MassiveClient:
    def __init__(self) -> None:
        self.base_url = settings.massive_base_url.rstrip("/")
        self.api_key = settings.MASSIVE_API_KEY
        self.client = httpx.AsyncClient(
            timeout=20.0,
            headers={"Accept": "application/json"},
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.client.get(
            f"{self.base_url}{path}",
            params=params or {},
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def get_snapshot(self, ticker: str) -> dict[str, Any]:
        return await self._get(
            "/v3/snapshot",
            {"ticker": ticker.upper()},
        )

    async def get_news(self, ticker: str, limit: int = 10) -> dict[str, Any]:
        return await self._get(
            "/v2/reference/news",
            {
                "ticker": ticker.upper(),
                "limit": limit,
            },
        )

    async def get_float(self, ticker: str, limit: int = 1) -> dict[str, Any]:
        return await self._get(
            "/stocks/vX/float",
            {
                "ticker": ticker.upper(),
                "limit": limit, 
                "sort": "ticker.asc",
            },
        )
    
    async def get_short_volume(self, ticker: str, limit: int = 10) -> dict[str, Any]: 
        return await self._get(
            "/stocks/v1/short-volume",
            {
                "ticker": ticker.upper(),
                "limit": limit, 
                "sort": "date.desc",
            },
        )

#    async def get_balance_sheets(self, ticker: str, limit: int = 2) -> dict[str, Any]:
#        return await self._get(
#            "/stocks/financials/v1/balance-sheets",
#            {
#                "ticker": ticker.upper(),
#                "limit": limit,
#                "order": "desc",
#            },
#        )

#    async def get_cash_flow_statements(self, ticker: str, limit: int = 2) -> dict[str, Any]:
#        return await self._get(
#            "/stocks/financials/v1/cash-flow-statements",
#            {
#                "ticker": ticker.upper(),
#                "limit": limit,
#                "order": "desc",
#            },
#        )

    async def get_short_interest(self, ticker: str, limit: int = 4) -> dict[str, Any]:
        return await self._get(
            "/stocks/v1/short-interest",
            {
                "ticker": ticker.upper(),
                "limit": limit,
                "order": "desc",
            },
        )