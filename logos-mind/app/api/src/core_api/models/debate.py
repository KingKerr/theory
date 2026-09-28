from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DebateClaimOutput(BaseModel):
    thesis: str = Field(
        min_length=20,
        max_length=800,
        description=(
            "A concrete, falsifiable constructive claim grounded only in "
            "the supplied evidence."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the cited evidence.",
    )
    evidence_ids: list[UUID] = Field(
        min_length=1,
        max_length=4,
        description="Evidence IDs from the provided evidence packet only.",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Material missing information that limits this claim.",
    )

    @field_validator("thesis")
    @classmethod
    def normalize_thesis(cls, value: str) -> str:
        return " ".join(value.split())


class BullTurnOutput(BaseModel):
    action_type: Literal["advance_bull_case"] = "advance_bull_case"
    rationale: str = Field(
        min_length=30,
        max_length=1600,
        description="Evidence-grounded explanation of the constructive case.",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the complete supplied packet.",
    )
    claims: list[DebateClaimOutput] = Field(
        min_length=1,
        max_length=3,
        description="One to three concrete cited constructive claims.",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Material unknowns that limit the overall conclusion.",
    )

class BearClaimOutput(BaseModel):
    thesis: str = Field(
        min_length=20,
        max_length=800,
        description=(
            "A specific, falsifiable downside or countervailing claim grounded "
            "only in the supplied evidence."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the cited evidence.",
    )
    evidence_ids: list[UUID] = Field(
        min_length=1,
        max_length=4,
        description="Evidence IDs from the supplied session evidence packet only.",
    )
    target_claim_ids: list[UUID] = Field(
        min_length=1,
        max_length=3,
        description=(
            "Existing Bull claim IDs directly challenged by this Bear claim. "
            "Use only IDs included in the supplied opposing-claims payload."
        ),
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Material missing information that limits this counterclaim.",
    )

    @field_validator("thesis")
    @classmethod
    def normalize_thesis(cls, value: str) -> str:
        return " ".join(value.split())


class BearTurnOutput(BaseModel):
    action_type: Literal["advance_bear_case"] = "advance_bear_case"
    rationale: str = Field(
        min_length=30,
        max_length=1600,
        description=(
            "An evidence-grounded explanation of the downside case and the "
            "material weaknesses or untested assumptions in the Bull case."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the complete supplied packet.",
    )
    claims: list[BearClaimOutput] = Field(
        min_length=1,
        max_length=3,
        description="One to three cited Bear claims that target Bull claims.",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Material unknowns that limit confidence in the downside case or "
            "prevent resolution of the Bull/Bear disagreement."
        ),
    )
class BearRebuttalClaimOutput(BaseModel):
    thesis: str = Field(
        min_length=20,
        max_length=800,
        description=(
            "A specific response to a Bull rebuttal claim, grounded only in "
            "the supplied evidence."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the supplied evidence.",
    )
    evidence_ids: list[UUID] = Field(
        min_length=1,
        max_length=4,
        description="Evidence IDs from the supplied session evidence packet only.",
    )
    target_claim_ids: list[UUID] = Field(
        min_length=1,
        max_length=3,
        description=(
            "Bull rebuttal claim IDs directly challenged, narrowed, "
            "or conceded."
        ),
    )
    response_type: Literal["challenge", "narrow", "concede"] = Field(
        description=(
            "Whether the Bear response challenges the Bull rebuttal, narrows "
            "it, or concedes a point supported by the evidence."
        ),
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Material missing information limiting this response.",
    )

    @field_validator("thesis")
    @classmethod
    def normalize_thesis(cls, value: str) -> str:
        return " ".join(value.split())


class BearRebuttalOutput(BaseModel):
    action_type: Literal["rebut_bull_case"] = "rebut_bull_case"
    rationale: str = Field(
        min_length=30,
        max_length=1600,
        description=(
            "Evidence-grounded explanation of the Bear response to the Bull "
            "rebuttal."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)
    claims: list[BearRebuttalClaimOutput] = Field(
        min_length=1,
        max_length=3,
        description="One to three cited, targeted Bear rebuttal claims.",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Material unresolved uncertainties after the rebuttal.",
    )

class BullRebuttalClaimOutput(BaseModel):
    thesis: str = Field(
        min_length=20,
        max_length=800,
        description=(
            "A specific, falsifiable response to a Bear claim, grounded only "
            "in the supplied evidence."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the cited evidence.",
    )
    evidence_ids: list[UUID] = Field(
        min_length=1,
        max_length=4,
        description="Evidence IDs from the supplied session evidence packet only.",
    )
    target_claim_ids: list[UUID] = Field(
        min_length=1,
        max_length=3,
        description=(
            "Bear claim IDs directly answered, narrowed, defended against, "
            "or conceded."
        ),
    )
    response_type: Literal["defend", "narrow", "concede"] = Field(
        description=(
            "Whether the Bull response defends the original case, narrows it, "
            "or concedes a valid Bear point."
        ),
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Material missing information that limits this rebuttal.",
    )

    @field_validator("thesis")
    @classmethod
    def normalize_thesis(cls, value: str) -> str:
        return " ".join(value.split())


class BullRebuttalOutput(BaseModel):
    action_type: Literal["rebut_bear_case"] = "rebut_bear_case"
    rationale: str = Field(
        min_length=30,
        max_length=1600,
        description=(
            "Evidence-grounded explanation of the Bull response to the "
            "Bear's strongest counterarguments."
        ),
    )
    confidence: float = Field(ge=0.0, le=1.0)
    claims: list[BullRebuttalClaimOutput] = Field(
        min_length=1,
        max_length=3,
        description="One to three cited, targeted Bull rebuttal claims.",
    )
    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Material unresolved uncertainties after the rebuttal.",
    )

class JudgeVerdictOutput(BaseModel):
    action_type: Literal["evaluate_debate"] = "evaluate_debate"

    verdict: Literal[
        "bull_better_supported",
        "bear_better_supported",
        "inconclusive",
    ]

    rationale: str = Field(
        min_length=50,
        max_length=1800,
        description=(
            "A neutral, evidence-grounded assessment of the completed debate. "
            "Do not provide investment advice."
        ),
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence calibrated to the supplied debate record.",
    )

    supporting_claim_ids: list[UUID] = Field(
        default_factory=list,
        max_length=3,
        description=(
            "Claim IDs from the supplied record that most support the verdict."
        ),
    )

    unresolved_claim_ids: list[UUID] = Field(
        default_factory=list,
        max_length=4,
        description=(
            "Claim IDs from the supplied record that remain materially unresolved."
        ),
    )

    decisive_evidence_ids: list[UUID] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Evidence IDs cited by supplied debate claims that materially "
            "inform the verdict."
        ),
    )

    information_gaps: list[str] = Field(
        default_factory=list,
        max_length=5,
        description=(
            "Material evidence gaps that limit the verdict."
        ),
    )