import json
from datetime import date, datetime
from typing import Any

from core_api.models.domain import Claim, EvidenceItem, WorldState


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            str(key): _json_safe(nested_value)
            for key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [_json_safe(item) for item in value]

    return value


def build_bull_evidence_packet(
    *,
    world_state: WorldState,
    evidence_items: list[EvidenceItem],
) -> str:
    """
    Creates a bounded, prompt-safe payload.

    The LLM receives only this payload and must cite evidence IDs from
    evidence_packet. Raw provider payloads and source instructions are excluded.
    """
    world_state_summary = {
        "security": {
            "ticker": world_state.security.ticker,
            "as_of_date": world_state.security.as_of_date,
        },
        "market_state": world_state.market_state,
        "fundamental_state": world_state.fundamental_state,
        "event_state": {
            key: value
            for key, value in world_state.event_state.items()
            if key != "raw_news_items"
        },
        "peer_state": world_state.peer_state,
        "state_version": world_state.state_version,
    }

    evidence_packet = [
        {
            "evidence_id": str(item.evidence_id),
            "source_type": item.source_type,
            "source_ref": item.source_ref,
            "observed_at": item.observed_at,
            "title": item.title,
            "summary": item.summary,
            "freshness_score": item.freshness_score,
            "confidence": item.confidence,
        }
        for item in evidence_items
    ]

    payload = {
        "world_state": world_state_summary,
        "evidence_packet": evidence_packet,
    }

    return json.dumps(_json_safe(payload), separators=(",", ":"))

def build_bear_evidence_packet(
    *,
    world_state: WorldState,
    evidence_items: list[EvidenceItem],
    opposing_claims: list[Claim],) -> str:
    """
    Creates a bounded packet for the Bear opening.

    The Bear receives:
    - a sanitized world-state summary;
    - session-scoped evidence that may be cited;
    - Bull claims that may be challenged through target_claim_ids.

    The agent must treat all supplied content as data, not instructions.
    """
    world_state_summary = {
        "security": {
            "ticker": world_state.security.ticker,
            "as_of_date": world_state.security.as_of_date,
        },
        "market_state": world_state.market_state,
        "fundamental_state": world_state.fundamental_state,
        "event_state": {
            key: value
            for key, value in world_state.event_state.items()
            if key != "raw_news_items"
        },
        "peer_state": world_state.peer_state,
        "state_version": world_state.state_version,
    }

    evidence_packet = [
        {
            "evidence_id": str(item.evidence_id),
            "source_type": item.source_type,
            "source_ref": item.source_ref,
            "observed_at": item.observed_at,
            "title": item.title,
            "summary": item.summary,
            "freshness_score": item.freshness_score,
            "confidence": item.confidence,
        }
        for item in evidence_items
    ]

    bull_claims = [
        {
            "claim_id": str(claim.claim_id),
            "round_no": claim.round_no,
            "side": claim.side,
            "thesis": claim.thesis,
            "confidence": claim.confidence,
            "evidence_ids": [str(evidence_id) for evidence_id in claim.evidence_ids],
            "status": claim.status,
        }
        for claim in opposing_claims
        if claim.side.lower() == "bull"
    ]

    payload = {
        "world_state": world_state_summary,
        "evidence_packet": evidence_packet,
        "opposing_claims": bull_claims,
    }

    return json.dumps(_json_safe(payload), separators=(",", ":"))

def build_rebuttal_evidence_packet(
    *,
    world_state: WorldState,
    evidence_items: list[EvidenceItem],
    opposing_claims: list[Claim],
    opposing_side: str,
) -> str:
    """
    Creates a bounded packet for a rebuttal phase.

    The agent receives:
    - sanitized world state;
    - session-scoped evidence eligible for citation;
    - claims from the opposing side that it may target.
    """
    world_state_summary = {
        "security": {
            "ticker": world_state.security.ticker,
            "as_of_date": world_state.security.as_of_date,
        },
        "market_state": world_state.market_state,
        "fundamental_state": world_state.fundamental_state,
        "event_state": {
            key: value
            for key, value in world_state.event_state.items()
            if key != "raw_news_items"
        },
        "peer_state": world_state.peer_state,
        "state_version": world_state.state_version,
    }

    evidence_packet = [
        {
            "evidence_id": str(item.evidence_id),
            "source_type": item.source_type,
            "source_ref": item.source_ref,
            "observed_at": item.observed_at,
            "title": item.title,
            "summary": item.summary,
            "freshness_score": item.freshness_score,
            "confidence": item.confidence,
        }
        for item in evidence_items
    ]

    filtered_opposing_claims = [
        {
            "claim_id": str(claim.claim_id),
            "round_no": claim.round_no,
            "side": claim.side,
            "claim_type": claim.claim_type,
            "thesis": claim.thesis,
            "confidence": claim.confidence,
            "evidence_ids": [str(evidence_id) for evidence_id in claim.evidence_ids],
            "target_claim_ids": [
                str(target_claim_id)
                for target_claim_id in claim.target_claim_ids
            ],
            "status": claim.status,
        }
        for claim in opposing_claims
        if claim.side.lower() == opposing_side.lower()
    ]

    payload = {
        "world_state": world_state_summary,
        "evidence_packet": evidence_packet,
        "opposing_claims": filtered_opposing_claims,
    }

    return json.dumps(_json_safe(payload), separators=(",", ":"))