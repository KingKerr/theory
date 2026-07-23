from uuid import uuid4


def build_initial_memory_episodes(world_state: dict, evidence_count: int) -> list[dict]:
    ticker = world_state.security.ticker
    news_count = world_state.event_state.get("news_count", 0)

    episodes = [
        {
            "episode_id": uuid4(),
            "episode_type": "ingestion",
            "summary": f"Initialized session for {ticker} with {news_count} news items and {evidence_count} evidence rows.",
            "payload": {
                "ticker": ticker,
                "news_count": news_count,
                "evidence_count": evidence_count,
            },
        },
        {
            "episode_id": uuid4(),
            "episode_type": "world_state",
            "summary": f"Created initial world state {world_state.state_version} for {ticker}.",
            "payload": {
                "state_version": world_state.state_version,
                "event_risk_level": world_state.event_state.get("event_risk_level"),
            },
        },
    ]

    return episodes


def build_initial_control_checks(world_state: dict, evidence_count: int) -> list[dict]:
    news_count = world_state.event_state.get("news_count", 0)

    checks = [
        {
            "control_check_id": uuid4(),
            "check_type": "evidence_presence",
            "status": "pass" if evidence_count > 0 else "warn",
            "severity": "info" if evidence_count > 0 else "warning",
            "details": {
                "evidence_count": evidence_count,
            },
        },
        {
            "control_check_id": uuid4(),
            "check_type": "news_coverage",
            "status": "pass" if news_count > 0 else "warn",
            "severity": "info" if news_count > 0 else "warning",
            "details": {
                "news_count": news_count,
            },
        },
    ]

    return checks