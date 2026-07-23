from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field
from .domain import SessionState, AgentAction, Claim, EvidenceItem, WorldState


class SessionMetadata(BaseModel):
    session_id: UUID
    ticker: str
    as_of_date: str | None = None
    window_days: int 
    mode: str 
    status: str 
    created_at: datetime
    updated_at: datetime | None = None

class QualityMetrics(BaseModel):
    debate_quality_score: float = 0.0 
    evidence_diversity_score: float = 0.0 
    repetition_risk_score: float = 0.0 
    judge_check_count: int = 0

class SessionDetailResponse(BaseModel):
    metadata: SessionMetadata
    world_state: WorldState
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    actions: list[AgentAction] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    controls: dict = Field(default_factory=dict)
    memory_summary: dict = Field(default_factory=dict)


class CreateSessionRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=10)
    as_of_date: date | None = None
    window_days: int = Field(default=180, ge=30, le=730)
    mode: str = "debate"


class CreateSessionResponse(BaseModel):
    session_id: UUID
    status: str
    session: SessionState

class StepSessionRequest(BaseModel):
    requested_by: str = "planner"
    max_evidence_items: int = Field(default=3, ge=1, le=10)

class StepSessionResponse(BaseModel):
    session_id: UUID 
    step_status: str 
    action: AgentAction
    claim: Claim | None = None
    controls: dict = Field(default_factory=dict)
    stepped_at: datetime

class SessionListItemResponse(BaseModel):
    session_id: UUID
    ticker: str
    mode: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    total_actions: int
    total_claims: int
    total_episodes: int

class SessionListResponse(BaseModel):
    sessions: list[SessionListItemResponse]