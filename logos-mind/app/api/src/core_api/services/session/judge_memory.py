from uuid import uuid4

from core_api.models.domain import AgentAction, Claim


def build_judge_summary_episode(
    action: AgentAction,
    claim: Claim | None,
    control_checks: list[dict],
) -> dict:
    distinct_evidence = next(
        (check for check in control_checks if check["check_type"] == "distinct_evidence"),
        None,
    )
    contradiction_quality = next(
        (check for check in control_checks if check["check_type"] == "contradiction_quality"),
        None,
    )
    unsupported_repetition = next(
        (check for check in control_checks if check["check_type"] == "unsupported_repetition"),
        None,
    )

    verdict = claim.thesis if claim else "No verdict claim was produced."

    summary = (
        f"JudgeAgent issued a debate verdict with confidence "
        f"{action.confidence:.2f}. Verdict: {verdict} "
        f"Distinct evidence: "
        f"{distinct_evidence['status'] if distinct_evidence else 'n/a'}. "
        f"Contradiction quality: "
        f"{contradiction_quality['status'] if contradiction_quality else 'n/a'}. "
        f"Unsupported repetition: "
        f"{unsupported_repetition['status'] if unsupported_repetition else 'n/a'}."
    )

    

    return {
        "episode_id": uuid4(),
        "episode_type": "judge_summary",
        "summary": summary,
        "payload": {
            "judge_confidence": action.confidence,
            "judge_claim": claim.thesis if claim else None,
            "checks": control_checks,
        },
    }