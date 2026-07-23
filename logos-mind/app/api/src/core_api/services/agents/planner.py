from core_api.models.domain import AgentAction, Claim, EvidenceItem


class PlannerService:
    def _score_evidence(self, item: EvidenceItem) -> float:
        score = float(item.confidence) + float(item.freshness_score)

        if item.source_type == "news":
            sentiment = item.payload.get("sentiment")
            if isinstance(sentiment, (int, float)) and sentiment > 0:
                score += 2.0
            score += 1.0

        elif item.source_type == "short_interest":
            pct = item.payload.get("percent_of_float")
            days = item.payload.get("days_to_cover")

            if isinstance(pct, (int, float)) and pct >= 10:
                score += 2.0
            if isinstance(days, (int, float)) and days >= 3:
                score += 1.5

        elif item.source_type == "float":
            float_shares = item.payload.get("float_shares")
            outstanding = item.payload.get("shares_outstanding")

            if (
                isinstance(float_shares, (int, float))
                and isinstance(outstanding, (int, float))
                and outstanding > 0
            ):
                float_ratio = float_shares / outstanding
                if float_ratio <= 0.7:
                    score += 1.75

        elif item.source_type == "short_volume":
            ratio = item.payload.get("short_volume_ratio")
            if isinstance(ratio, (int, float)) and ratio >= 0.5:
                score += 1.25

        return score

    def _build_bull_thesis(self, selected: list[EvidenceItem]) -> str:
        evidence_types = {item.source_type for item in selected}

        if "news" in evidence_types and "short_interest" in evidence_types:
            return (
                "Bull case: Supportive recent developments combined with elevated short interest "
                "create room for upside if sentiment improves or a catalyst lands."
            )

        if "short_interest" in evidence_types and "float" in evidence_types:
            return (
                "Bull case: A tighter float combined with elevated short positioning can create "
                "upside asymmetry if the bearish consensus starts to unwind."
            )

        if "news" in evidence_types:
            return (
                "Bull case: Recent developments support a constructive view and improve the odds "
                "of favorable market reassessment."
            )

        if "short_interest" in evidence_types:
            return (
                "Bull case: Heavy short positioning can become fuel for upside if the company "
                "delivers even a modestly positive catalyst."
            )

        if "float" in evidence_types:
            return (
                "Bull case: Float dynamics suggest the stock could move sharply higher if demand "
                "improves and bearish positioning becomes crowded."
            )

        if "short_volume" in evidence_types:
            return (
                "Bull case: Current trading pressure may be overextended, leaving room for a "
                "sharp rebound if selling intensity fades."
            )

        return (
            "Bull case: Recent evidence supports a constructive view on the security, with "
            "positioning and narrative signals leaning favorable."
        )

    def step_from_evidence(
        self,
        evidence_items: list[EvidenceItem],
    ) -> tuple[AgentAction, Claim, list[dict]]:
        ranked = sorted(
            evidence_items,
            key=self._score_evidence,
            reverse=True,
        )
        selected = ranked[:3]
        evidence_ids = [item.evidence_id for item in selected]

        thesis = self._build_bull_thesis(selected)

        action = AgentAction(
            agent_name="planner",
            action_type="propose_bull_case",
            rationale=(
                "Planner selected the strongest supportive evidence across positioning and "
                "recent developments to form a bull thesis."
            ),
            evidence_ids=evidence_ids,
            confidence=0.74,
        )

        claim = Claim(
            side="bull",
            thesis=thesis,
            confidence=0.74,
            evidence_ids=evidence_ids,
            status="active",
        )

        control_checks = [
            {
                "check_type": "planner_evidence_selected",
                "status": "pass",
                "severity": "info",
                "details": {
                    "selected_source_types": [item.source_type for item in selected],
                    "selected_count": len(selected),
                },
            }
        ]

        return action, claim, control_checks