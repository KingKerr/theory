from datetime import date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SecurityRef(BaseModel):
    ticker: str
    as_of_date: date | None = None


class WorldState(BaseModel):
    security: SecurityRef
    market_state: dict = Field(default_factory=dict)
    fundamental_state: dict = Field(default_factory=dict)
    event_state: dict = Field(default_factory=dict)
    peer_state: dict = Field(default_factory=dict)
    state_version: str = "v1"


class EvidenceItem(BaseModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    source_type: str
    source_ref: str | None = None
    observed_at: datetime | None = None
    title: str
    summary: str
    payload: dict = Field(default_factory=dict)
    freshness_score: float = 0.0
    confidence: float = 0.0


class AgentAction(BaseModel):
    round_no: int | None = None 
    agent_name: str
    action_type: str
    rationale: str
    evidence_ids: list[UUID] = Field(default_factory=list)
    confidence: float = 0.0


class Claim(BaseModel):
    claim_id: UUID = Field(default_factory=uuid4)
    round_no: int | None = None 
    side: str
    thesis: str
    confidence: float = 0.0
    evidence_ids: list[UUID] = Field(default_factory=list)
    status: str = "active"


class SessionState(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    world_state: WorldState
    actions: list[AgentAction] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    controls: dict = Field(default_factory=dict)
    memory_summary: dict = Field(default_factory=dict)