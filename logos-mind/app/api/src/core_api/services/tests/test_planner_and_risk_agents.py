from uuid import uuid4

from models.domain import Claim, EvidenceItem
from services.agents.planner import PlannerService
from services.agents.risk_agent import RiskAgentService


def make_evidence(source_type: str, payload: dict, confidence: float = 0.8, freshness: float = 0.7):
    return EvidenceItem(
        evidence_id=uuid4(),
        source_type=source_type,
        title=f"{source_type} evidence",
        summary=f"{source_type} summary",
        payload=payload,
        confidence=confidence,
        freshness_score=freshness,
    )


def test_planner_prefers_supportive_fundamental_evidence():
    planner = PlannerService()

    news = make_evidence("news", {})
    balance = make_evidence(
        "balance_sheet",
        {
            "current_ratio": 1.8,
            "cash_and_equivalents": 1000,
            "debt": 100,
        },
    )
    cash_flow = make_evidence(
        "cash_flow_statement",
        {
            "operating_cash_flow": 500,
            "free_cash_flow_proxy": 300,
        },
    )

    action, claim, _ = planner.step_from_evidence([news, balance, cash_flow])

    assert claim.side == "bull"
    assert cash_flow.evidence_id in claim.evidence_ids
    assert balance.evidence_id in claim.evidence_ids
    assert action.agent_name == "planner"


def test_risk_agent_prefers_non_overlapping_rebuttal_evidence():
    risk = RiskAgentService()

    bull_balance = make_evidence(
        "balance_sheet",
        {
            "current_ratio": 1.9,
            "cash_and_equivalents": 1200,
            "debt": 50,
        },
    )
    short_interest = make_evidence(
        "short_interest",
        {
            "percent_of_float": 14,
            "days_to_cover": 5,
        },
    )
    weak_cash_flow = make_evidence(
        "cash_flow_statement",
        {
            "operating_cash_flow": -200,
            "free_cash_flow_proxy": -300,
        },
    )

    latest_claim = Claim(
        side="bull",
        thesis="Bull thesis",
        evidence_ids=[bull_balance.evidence_id],
        confidence=0.7,
        status="active",
    )

    action, claim, checks = risk.step_from_context(
        evidence_items=[bull_balance, short_interest, weak_cash_flow],
        latest_claim=latest_claim,
    )

    assert claim.side == "bear"
    assert bull_balance.evidence_id not in claim.evidence_ids
    assert weak_cash_flow.evidence_id in claim.evidence_ids
    assert short_interest.evidence_id in claim.evidence_ids
    assert checks[0]["check_type"] == "risk_agent_rebuttal_targeting"


def test_risk_agent_falls_back_when_all_evidence_overlaps():
    risk = RiskAgentService()

    shared_news = make_evidence("news", {})
    latest_claim = Claim(
        side="bull",
        thesis="Bull thesis",
        evidence_ids=[shared_news.evidence_id],
        confidence=0.7,
        status="active",
    )

    action, claim, _ = risk.step_from_context(
        evidence_items=[shared_news],
        latest_claim=latest_claim,
    )

    assert action.agent_name == "risk_agent"
    assert claim.side == "bear"
    assert len(claim.evidence_ids) == 1