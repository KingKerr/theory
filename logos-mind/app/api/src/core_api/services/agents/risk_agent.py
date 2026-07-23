from core_api.models.domain import AgentAction, Claim, EvidenceItem


class RiskAgentService:
    def _score_evidence(self, item: EvidenceItem) -> float:
        score = float(item.confidence) + float(item.freshness_score)

        if item.source_type == "short_interest":
            pct = item.payload.get("percent_of_float")
            days = item.payload.get("days_to_cover")
            shares = item.payload.get("short_interest")

            if isinstance(pct, (int, float)) and pct >= 10:
                score += 2.5
            if isinstance(days, (int, float)) and days >= 3:
                score += 2.0
            if isinstance(shares, (int, float)) and shares > 0:
                score += 0.75

        elif item.source_type == "short_volume":
            ratio = item.payload.get("short_volume_ratio")
            short_volume = item.payload.get("short_volume")
            total_volume = item.payload.get("total_volume")

            if isinstance(ratio, (int, float)) and ratio >= 0.5:
                score += 2.0
            if isinstance(short_volume, (int, float)) and short_volume > 0:
                score += 0.75
            if isinstance(total_volume, (int, float)) and total_volume > 0:
                score += 0.5

        elif item.source_type == "float":
            float_shares = item.payload.get("float_shares")
            outstanding = item.payload.get("shares_outstanding")

            if isinstance(float_shares, (int, float)) and float_shares > 0:
                score += 1.0
            if (
                isinstance(float_shares, (int, float))
                and isinstance(outstanding, (int, float))
                and outstanding > 0
            ):
                float_ratio = float_shares / outstanding
                if float_ratio <= 0.7:
                    score += 1.25

        elif item.source_type == "news":
            score += 1.0

        return score

    def _dominant_source_type(
        self,
        latest_claim,
        evidence_items: list[EvidenceItem],
    ) -> str | None:
        if latest_claim is None:
            return None

        evidence_lookup = {item.evidence_id: item for item in evidence_items}
        for evidence_id in latest_claim.evidence_ids:
            item = evidence_lookup.get(evidence_id)
            if item is not None:
                return item.source_type

        return None

    def _build_bear_thesis(self, selected: list[EvidenceItem], latest_claim) -> str:
        evidence_types = {item.source_type for item in selected}

        if latest_claim and latest_claim.side == "bull":
            if "short_interest" in evidence_types:
                return (
                    "Bear case: Elevated short interest suggests the market is pricing in "
                    "meaningful downside risk and remains skeptical of the bullish thesis."
                )

            if "short_volume" in evidence_types:
                return (
                    "Bear case: Recent short-volume activity points to active near-term "
                    "selling pressure rather than broad conviction in the upside case."
                )

            if "float" in evidence_types:
                return (
                    "Bear case: Float dynamics can amplify downside moves and make the stock "
                    "more vulnerable when sentiment deteriorates."
                )

            if "news" in evidence_types:
                return (
                    "Bear case: Recent developments introduce uncertainty that weakens "
                    "confidence in the prior bullish thesis."
                )

        return (
            "Bear case: The security still faces material downside risk, and the current "
            "evidence does not justify a confident bullish stance."
        )

    def step_from_context(
        self,
        evidence_items: list[EvidenceItem],
        latest_claim,
    ) -> tuple[AgentAction, Claim, list[dict]]:
        latest_evidence_ids = set(latest_claim.evidence_ids) if latest_claim else set()
        dominant_type = self._dominant_source_type(latest_claim, evidence_items)

        ranked = sorted(
            evidence_items,
            key=self._score_evidence,
            reverse=True,
        )

        preferred = [
            item
            for item in ranked
            if item.evidence_id not in latest_evidence_ids
            and item.source_type != dominant_type
        ]

        fallback = [
            item
            for item in ranked
            if item.evidence_id not in latest_evidence_ids
        ]

        selected = preferred[:3] or fallback[:3] or ranked[:3]
        evidence_ids = [item.evidence_id for item in selected]

        thesis = self._build_bear_thesis(selected, latest_claim)

        action = AgentAction(
            agent_name="risk_agent",
            action_type="rebut_bull_case",
            rationale=(
                "RiskAgent selected higher-risk or contradictory evidence, prioritizing "
                "source types that differ from the latest claim to produce a meaningful rebuttal."
            ),
            evidence_ids=evidence_ids,
            confidence=0.76,
        )

        claim = Claim(
            side="bear",
            thesis=thesis,
            confidence=0.76,
            evidence_ids=evidence_ids,
            status="active",
        )

        control_checks = [
            {
                "check_type": "risk_agent_rebuttal_targeting",
                "status": "pass",
                "severity": "info",
                "details": {
                    "latest_claim_side": getattr(latest_claim, "side", None),
                    "latest_claim_evidence_count": len(latest_evidence_ids),
                    "selected_source_types": [item.source_type for item in selected],
                    "dominant_source_type": dominant_type,
                },
            }
        ]

        return action, claim, control_checks