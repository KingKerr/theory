from core_api.models.domain import SecurityRef, WorldState
from core_api.services.massive.client import MassiveClient


class WorldStateBuilder:
    def __init__(self) -> None:
        self.massive = MassiveClient()

    async def build(self, ticker: str, as_of_date=None) -> WorldState:
        snapshot = await self.massive.get_snapshot(ticker)
        news = await self.massive.get_news(ticker, limit=5)

        results = snapshot.get("results") or snapshot
        news_items = news.get("results", [])

        market_state = {
            "last_snapshot": results,
            "liquidity_regime": "unknown",
            "trend_profile": "unknown",
            "volatility_profile": "unknown",
        }

        event_state = {
            "news_count": len(news_items),
            "top_headlines": [
                {
                    "title": item.get("title", ""),
                    "published_utc": item.get("published_utc"),
                    "sentiment": item.get("insights", []),
                }
                for item in news_items[:3]
            ],
            "raw_news_items": news_items,
            "event_risk_level": "medium" if news_items else "low",
        }

        fundamental_state = {
            "balance_sheet": {
                "period_end": "",
                "assets": "",
                "liabilities": "",
                "equity": "",
                "cash_and_equivalents": "",
                "debt": "",
                "current_ratio": "",
            },
            "cash_flow": {
                "period_end": "...",
                "operating_cash_flow": "...",
                "investing_cash_flow": "...",
                "financing_cash_flow": "...",
                "free_cash_flow_proxy": "...",
            },
            "short_interest": {
                "settlement_date": "...",
                "short_interest": "...",
                "days_to_cover": "...",
                "percent_of_float": "...",
            },
            "quality_profile": "unknown",
            "valuation_profile": "unknown",
        }

        peer_state = {
            "peer_set_ready": False,
        }

        return WorldState(
            security=SecurityRef(ticker=ticker.upper(), as_of_date=as_of_date),
            market_state=market_state,
            fundamental_state=fundamental_state,
            event_state=event_state,
            peer_state=peer_state,
            state_version="v1",
        )