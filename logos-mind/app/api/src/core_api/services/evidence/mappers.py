from datetime import datetime
from typing import Any

from core_api.models.domain import EvidenceItem


def _safe_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def map_massive_news_to_evidence(news_item: dict[str, Any]) -> EvidenceItem:
    insights = news_item.get("insights", []) or []
    tickers = news_item.get("tickers", []) or []
    publisher = news_item.get("publisher", {}) or {}
    sentiment_labels = [
        insight.get("sentiment")
        for insight in insights
        if insight.get("sentiment")
    ]

    confidence = 0.6 if insights else 0.4

    return EvidenceItem(
        source_type="news",
        source_ref=news_item.get("article_url") or news_item.get("id"),
        observed_at=_safe_datetime(news_item.get("published_utc")),
        title=news_item.get("title", "Untitled article"),
        summary=news_item.get("description") or news_item.get("snippet") or "",
        payload={
            "tickers": tickers,
            "publisher": publisher,
            "keywords": news_item.get("keywords", []),
            "insights": insights,
            "sentiment_labels": sentiment_labels,
        },
        freshness_score=1.0,
        confidence=confidence,
    )


def map_float_results(raw: dict[str, Any]) -> tuple[dict, list[EvidenceItem]]:
    results = raw.get("results") or []
    if not results:
        return {}, []

    latest = results[0]

    free_float = _safe_int(latest.get("free_float"))
    free_float_percent = _safe_float(latest.get("free_float_percent"))

    normalized = {
        "ticker": latest.get("ticker"),
        "effective_date": latest.get("effective_date"),
        "free_float": free_float,
        "free_float_percent": free_float_percent,
    }

    evidence = [
        EvidenceItem(
            source_type="float",
            source_ref=_safe_str(latest.get("ticker") or latest.get("effective_date")),
            observed_at=_safe_datetime(latest.get("effective_date")),
            title="Float snapshot",
            summary=(
                f"Free float={free_float}, free float percent={free_float_percent}."
            ),
            payload=normalized,
            freshness_score=0.7,
            confidence=0.88,
        )
    ]

    return normalized, evidence


def map_short_interest_results(raw: dict[str, Any]) -> tuple[dict, list[EvidenceItem]]:
    results = raw.get("results") or []
    if not results:
        return {}, []

    latest = results[0]

    short_interest = _safe_float(latest.get("short_interest"))
    days_to_cover = _safe_float(latest.get("days_to_cover"))
    percent_of_float = _safe_float(latest.get("short_interest_percent_of_float"))

    normalized = {
        "settlement_date": latest.get("settlement_date"),
        "short_interest": short_interest,
        "days_to_cover": days_to_cover,
        "percent_of_float": percent_of_float,
    }

    evidence = [
        EvidenceItem(
            source_type="short_interest",
            source_ref=_safe_str(latest.get("settlement_date")),
            title="Short interest snapshot",
            summary=(
                f"Short interest={short_interest}, days to cover={days_to_cover}, "
                f"percent of float={percent_of_float}."
            ),
            payload=normalized,
            freshness_score=0.65,
            confidence=0.86,
        )
    ]

    return normalized, evidence


def map_short_volume_results(raw: dict[str, Any]) -> tuple[dict, list[EvidenceItem]]:
    results = raw.get("results") or []
    if not results:
        return {}, []

    latest = results[0]

    short_volume = _safe_float(latest.get("short_volume"))
    short_volume_ratio = _safe_float(latest.get("short_volume_ratio"))
    total_volume = _safe_float(latest.get("total_volume"))
    exempt_volume = _safe_float(latest.get("exempt_volume"))
    non_exempt_volume = _safe_float(latest.get("non_exempt_volume"))

    normalized = {
        "date": latest.get("date"),
        "short_volume": short_volume,
        "short_volume_ratio": short_volume_ratio,
        "total_volume": total_volume,
        "exempt_volume": exempt_volume,
        "non_exempt_volume": non_exempt_volume,
    }

    evidence = [
        EvidenceItem(
            source_type="short_volume",
            source_ref=_safe_str(latest.get("ticker") or latest.get("date")),
            observed_at=_safe_datetime(latest.get("date")),
            title="Short volume snapshot",
            summary=(
                f"Short volume={short_volume}, short volume ratio={short_volume_ratio}, "
                f"total volume={total_volume}."
            ),
            payload=normalized,
            freshness_score=0.9,
            confidence=0.9,
        )
    ]

    return normalized, evidence