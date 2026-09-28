from uuid import UUID, uuid4

import pytest

from core_api.models.debate import JudgeVerdictOutput
from core_api.models.domain import AgentAction, Claim
from core_api.services.agents.judge_agent import JudgeAgentService


class FakeLLMClient:
    def __init__(self, output: JudgeVerdictOutput) -> None:
        self.output = output
        self.calls: list[dict] = []

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[JudgeVerdictOutput],
    ) -> JudgeVerdictOutput:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_model": response_model,
            }
        )
        return self.output


def make_claim(
    *,
    claim_id: UUID,
    round_no: int,
    side: str,
    claim_type: str,
    evidence_id: UUID,
    target_claim_ids: list[UUID] | None = None,
    status: str = "active",
) -> Claim:
    return Claim(
        claim_id=claim_id,
        round_no=round_no,
        side=side,
        claim_type=claim_type,
        thesis=(
            f"Round {round_no} {side} {claim_type} claim grounded in the "
            "supplied evidence and debate record."
        ),
        confidence=0.65,
        evidence_ids=[evidence_id],
        target_claim_ids=target_claim_ids or [],
        status=status,
    )


def make_complete_debate() -> tuple[list[Claim], list[AgentAction], UUID]:
    evidence_id = uuid4()

    bull_opening = make_claim(
        claim_id=uuid4(),
        round_no=1,
        side="bull",
        claim_type="opening",
        evidence_id=evidence_id,
    )
    bear_opening = make_claim(
        claim_id=uuid4(),
        round_no=2,
        side="bear",
        claim_type="opening",
        evidence_id=evidence_id,
        target_claim_ids=[bull_opening.claim_id],
    )
    bull_rebuttal = make_claim(
        claim_id=uuid4(),
        round_no=3,
        side="bull",
        claim_type="rebuttal",
        evidence_id=evidence_id,
        target_claim_ids=[bear_opening.claim_id],
    )
    bear_rebuttal = make_claim(
        claim_id=uuid4(),
        round_no=4,
        side="bear",
        claim_type="rebuttal",
        evidence_id=evidence_id,
        target_claim_ids=[bull_rebuttal.claim_id],
    )

    actions = [
        AgentAction(
            round_no=1,
            agent_name="planner",
            action_type="make_bull_case",
            rationale="Bull opening action.",
            evidence_ids=[evidence_id],
            confidence=0.65,
        ),
        AgentAction(
            round_no=2,
            agent_name="risk_agent",
            action_type="make_bear_case",
            rationale="Bear opening action.",
            evidence_ids=[evidence_id],
            confidence=0.65,
        ),
        AgentAction(
            round_no=3,
            agent_name="planner",
            action_type="rebut_bear_case",
            rationale="Bull rebuttal action.",
            evidence_ids=[evidence_id],
            confidence=0.65,
        ),
        AgentAction(
            round_no=4,
            agent_name="risk_agent",
            action_type="rebut_bull_case",
            rationale="Bear rebuttal action.",
            evidence_ids=[evidence_id],
            confidence=0.65,
        ),
    ]

    return [
        bull_opening,
        bear_opening,
        bull_rebuttal,
        bear_rebuttal,
    ], actions, evidence_id


def make_verdict_output(
    *,
    evidence_id: UUID,
    supporting_claim_ids: list[UUID],
    unresolved_claim_ids: list[UUID],
) -> JudgeVerdictOutput:
    return JudgeVerdictOutput(
        verdict="inconclusive",
        rationale=(
            "The Bull case has evidence of operating momentum, while the Bear "
            "case identifies material unresolved valuation, margin, and "
            "conversion gaps that the supplied record cannot settle."
        ),
        confidence=0.56,
        supporting_claim_ids=supporting_claim_ids,
        unresolved_claim_ids=unresolved_claim_ids,
        decisive_evidence_ids=[evidence_id],
        information_gaps=[
            "The supplied record does not contain valuation, margin, or conversion data."
        ],
    )


@pytest.mark.asyncio
async def test_evaluate_debate_returns_structured_judge_verdict() -> None:
    claims, actions, evidence_id = make_complete_debate()

    llm_client = FakeLLMClient(
        make_verdict_output(
            evidence_id=evidence_id,
            supporting_claim_ids=[
                claims[0].claim_id,
                claims[3].claim_id,
            ],
            unresolved_claim_ids=[claims[2].claim_id],
        )
    )
    service = JudgeAgentService(llm_client=llm_client)

    action, claim, control_checks = await service.evaluate_debate(
        recent_claims=claims,
        recent_actions=actions,
    )

    assert len(llm_client.calls) == 1

    assert action.agent_name == "judge_agent"
    assert action.action_type == "evaluate_debate"
    assert action.evidence_ids == [evidence_id]
    assert action.confidence == 0.56

    assert claim is not None
    assert claim.side == "judge"
    assert claim.claim_type == "verdict"
    assert claim.confidence == 0.56
    assert claim.evidence_ids == [evidence_id]
    assert claim.status == "active"
    assert claim.thesis.startswith("inconclusive:")

    assert claim.target_claim_ids == sorted(
        {
            claims[0].claim_id,
            claims[2].claim_id,
            claims[3].claim_id,
        },
        key=str,
    )

    assert [check["check_type"] for check in control_checks] == [
        "distinct_evidence",
        "contradiction_quality",
        "unsupported_repetition",
        "judge_verdict",
    ]

    verdict_check = next(
        check
        for check in control_checks
        if check["check_type"] == "judge_verdict"
    )
    assert verdict_check["status"] == "pass"
    assert verdict_check["details"]["verdict"] == "inconclusive"
    assert verdict_check["details"]["supporting_claim_ids"] == [
        str(claims[0].claim_id),
        str(claims[3].claim_id),
    ]
    assert verdict_check["details"]["unresolved_claim_ids"] == [
        str(claims[2].claim_id)
    ]


@pytest.mark.asyncio
async def test_evaluate_debate_requires_complete_active_four_turn_debate() -> None:
    claims, actions, evidence_id = make_complete_debate()
    incomplete_claims = claims[:-1]

    fake_llm = FakeLLMClient(
        make_verdict_output(
            evidence_id=evidence_id,
            supporting_claim_ids=[claims[0].claim_id],
            unresolved_claim_ids=[],
        )
    )
    service = JudgeAgentService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Judge requires a complete active four-turn debate",
    ) as exc_info:
        await service.evaluate_debate(
            recent_claims=incomplete_claims,
            recent_actions=actions,
        )

    assert "bear round 4 rebuttal" in str(exc_info.value)
    assert fake_llm.calls == []


@pytest.mark.asyncio
async def test_evaluate_debate_rejects_claim_ids_outside_debate_record() -> None:
    claims, actions, evidence_id = make_complete_debate()
    invalid_claim_id = uuid4()

    output = make_verdict_output(
        evidence_id=evidence_id,
        supporting_claim_ids=[invalid_claim_id],
        unresolved_claim_ids=[],
    )
    service = JudgeAgentService(llm_client=FakeLLMClient(output))

    with pytest.raises(
        ValueError,
        match="Judge verdict referenced claims outside the supplied debate record",
    ) as exc_info:
        await service.evaluate_debate(
            recent_claims=claims,
            recent_actions=actions,
        )

    assert str(invalid_claim_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_evaluate_debate_rejects_evidence_ids_outside_debate_record() -> None:
    claims, actions, _ = make_complete_debate()
    invalid_evidence_id = uuid4()

    output = make_verdict_output(
        evidence_id=invalid_evidence_id,
        supporting_claim_ids=[claims[0].claim_id],
        unresolved_claim_ids=[],
    )
    service = JudgeAgentService(llm_client=FakeLLMClient(output))

    with pytest.raises(
        ValueError,
        match="Judge verdict cited evidence outside the supplied debate record",
    ) as exc_info:
        await service.evaluate_debate(
            recent_claims=claims,
            recent_actions=actions,
        )

    assert str(invalid_evidence_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_evaluate_debate_defaults_verdict_targets_to_all_four_claims() -> None:
    claims, actions, evidence_id = make_complete_debate()

    output = make_verdict_output(
        evidence_id=evidence_id,
        supporting_claim_ids=[],
        unresolved_claim_ids=[],
    )
    service = JudgeAgentService(llm_client=FakeLLMClient(output))

    _, claim, _ = await service.evaluate_debate(
        recent_claims=claims,
        recent_actions=actions,
    )

    assert claim is not None
    assert claim.target_claim_ids == sorted(
        [item.claim_id for item in claims],
        key=str,
    )


@pytest.mark.asyncio
async def test_evaluate_debate_ignores_inactive_required_turn() -> None:
    claims, actions, evidence_id = make_complete_debate()

    inactive_bear_rebuttal = claims[3].model_copy(
        update={"status": "superseded"},
    )
    claims_with_inactive_turn = [
        claims[0],
        claims[1],
        claims[2],
        inactive_bear_rebuttal,
    ]

    fake_llm = FakeLLMClient(
        make_verdict_output(
            evidence_id=evidence_id,
            supporting_claim_ids=[claims[0].claim_id],
            unresolved_claim_ids=[],
        )
    )
    service = JudgeAgentService(llm_client=fake_llm)

    with pytest.raises(
        ValueError,
        match="Judge requires a complete active four-turn debate",
    ):
        await service.evaluate_debate(
            recent_claims=claims_with_inactive_turn,
            recent_actions=actions,
        )

    assert fake_llm.calls == []