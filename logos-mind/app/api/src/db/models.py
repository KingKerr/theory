from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class SecuritySessionORM(Base):
    __tablename__ = "security_session"

    session_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticker: Mapped[str] = mapped_column(Text, nullable=False)
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    mode: Mapped[str] = mapped_column(Text, nullable=False, default="debate")
    status: Mapped[str] = mapped_column(Text, nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class WorldStateSnapshotORM(Base):
    __tablename__ = "world_state_snapshot"

    snapshot_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    state_version: Mapped[str] = mapped_column(Text, nullable=False)
    market_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    fundamental_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    event_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    peer_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EvidenceItemORM(Base):
    __tablename__ = "evidence_item"

    evidence_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    freshness_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AgentActionORM(Base):
    __tablename__ = "agent_action"

    action_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    round_no: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    action_type: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AgentClaimORM(Base):
    __tablename__ = "agent_claim"

    claim_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    round_no: Mapped[int] = mapped_column(Integer, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    thesis: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    evidence_ids: Mapped[list[str]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

class SessionMemoryEpisodeORM(Base):
    __tablename__ = "session_memory_episode"
    episode_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_session.session_id", ondelete="CASCADE"),
        nullable=False,
    )
    episode_type: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
    nullable=False, server_default=func.now())

class ControlCheckORM(Base):
    __tablename__ = "control_check"
    control_check_id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("security_session.session_id", ondelete="CASCADE"),
    nullable=False,)
    check_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False, default="info")
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())