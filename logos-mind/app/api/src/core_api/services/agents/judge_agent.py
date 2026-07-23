from collections import Counter

from core_api.models.domain import AgentAction, Claim


class JudgeAgentService:
    def evaluate_debate(
        self,
        recent_claims: list[Claim],
        recent_actions: list[AgentAction],
    ) -> tuple[AgentAction, Claim | None, list[dict]]:
        if len(recent_claims) < 2:
            action = AgentAction(
                agent_name="judge_agent",
                action_type="insufficient_context",
                rationale="JudgeAgent could not evaluate debate quality because fewer than two claims exist.",
                evidence_ids=[],
                confidence=0.35,
            )

            controls = [
                {
                    "check_type": "judge_context_readiness",
                    "status": "warn",
                    "severity": "warning",
                    "details": {
                        "reason": "Need at least two claims for debate evaluation.",
                        "claim_count": len(recent_claims),
                    },
                }
            ]

            return action, None, controls

        latest = recent_claims[0]
        previous = recent_claims[1]

        latest_evidence = set(str(eid) for eid in latest.evidence_ids)
        previous_evidence = set(str(eid) for eid in previous.evidence_ids)
        distinct_evidence = len(latest_evidence.intersection(previous_evidence)) == 0

        contradiction_ok = latest.side != previous.side

        normalized_claim_texts = [
            claim.thesis.strip().lower()
            for claim in recent_claims
            if claim.thesis
        ]
        repeated_claim_text = len(set(normalized_claim_texts)) < len(normalized_claim_texts)

        recent_action_types = [action.action_type for action in recent_actions]
        repeated_action_pattern = any(
            count >= 3 for count in Counter(recent_action_types).values()
        )

        drift_detected = repeated_claim_text or repeated_action_pattern

        score_parts = {
            "distinct_evidence": 1.0 if distinct_evidence else 0.0,
            "contradiction_quality": 1.0 if contradiction_ok else 0.0,
            "repetition_drift": 0.0 if drift_detected else 1.0,
        }
        overall_score = round(sum(score_parts.values()) / len(score_parts), 2)

        rationale = (
            "JudgeAgent evaluated the latest debate turn for evidence distinctness, contradiction quality, "
            "and repetition drift across recent claims and actions."
        )

        action = AgentAction(
            agent_name="judge_agent",
            action_type="score_debate_turn",
            rationale=rationale,
            evidence_ids=list(latest.evidence_ids),
            confidence=overall_score,
        )

        claim = Claim(
            side="judge",
            thesis=(
                f"Judge score {overall_score:.2f}: "
                f"distinct_evidence={'yes' if distinct_evidence else 'no'}, "
                f"contradiction_quality={'yes' if contradiction_ok else 'no'}, "
                f"repetition_drift={'yes' if drift_detected else 'no'}."
            ),
            confidence=overall_score,
            evidence_ids=list(latest.evidence_ids),
            status="active",
        )

        controls = [
            {
                "check_type": "distinct_evidence",
                "status": "pass" if distinct_evidence else "warn",
                "severity": "info" if distinct_evidence else "warning",
                "details": {
                    "latest_claim_id": str(latest.claim_id),
                    "previous_claim_id": str(previous.claim_id),
                    "shared_evidence_ids": sorted(list(latest_evidence.intersection(previous_evidence))),
                },
            },
            {
                "check_type": "contradiction_quality",
                "status": "pass" if contradiction_ok else "warn",
                "severity": "info" if contradiction_ok else "warning",
                "details": {
                    "latest_side": latest.side,
                    "previous_side": previous.side,
                },
            },
            {
                "check_type": "unsupported_repetition",
                "status": "warn" if drift_detected else "pass",
                "severity": "warning" if drift_detected else "info",
                "details": {
                    "repeated_claim_text": repeated_claim_text,
                    "repeated_action_pattern": repeated_action_pattern,
                },
            },
        ]

        return action, claim, controls