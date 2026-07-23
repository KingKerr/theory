from sqlalchemy import select, desc, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from db.models import (
    SessionMemoryEpisodeORM,
    ControlCheckORM,
    SecuritySessionORM,
    WorldStateSnapshotORM,
    AgentActionORM,
    AgentClaimORM,
    EvidenceItemORM,
)
from core_api.models.domain import SessionState, WorldState, AgentAction, Claim, EvidenceItem
from core_api.models.api import (
    QualityMetrics,
    SessionDetailResponse,
    SessionMetadata,
    SessionListItemResponse,
)


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, session: SessionState, window_days: int, mode: str) -> SessionState:
        session_row = SecuritySessionORM(
            session_id=session.session_id,
            ticker=session.world_state.security.ticker,
            as_of_date=session.world_state.security.as_of_date,
            window_days=window_days,
            mode=mode,
            status="created",
        )

        snapshot_row = WorldStateSnapshotORM(
            session_id=session.session_id,
            state_version=session.world_state.state_version,
            market_state=session.world_state.market_state,
            fundamental_state=session.world_state.fundamental_state,
            event_state=session.world_state.event_state,
            peer_state=session.world_state.peer_state,
        )

        self.db.add(session_row)
        self.db.add(snapshot_row)
        await self.db.flush()
        return session

    async def insert_evidence_items(self, session_id, items: list[EvidenceItem]) -> None:
        if not items:
            return
        values = [
            {
                "evidence_id": item.evidence_id,
                "session_id": session_id,
                "source_type": item.source_type,
                "source_ref": item.source_ref,
                "observed_at": item.observed_at,
                "title": item.title,
                "summary": item.summary,
                "payload": item.payload,
                "freshness_score": item.freshness_score,
                "confidence": item.confidence,
            }
            for item in items
        ]
        stmt = insert(EvidenceItemORM).values(values)
        await self.db.execute(stmt)

    async def insert_memory_episodes(self, session_id, episodes: list[dict]) -> None:
        if not episodes:
            return
        values = [
            {
                "episode_id": episode["episode_id"],
                "session_id": session_id,
                "episode_type": episode["episode_type"],
                "summary": episode["summary"],
                "payload": episode.get("payload", {}),
            }
            for episode in episodes
        ]
        stmt = insert(SessionMemoryEpisodeORM).values(values)
        await self.db.execute(stmt)

    async def insert_control_checks(self, session_id, checks: list[dict]) -> None:
        if not checks:
            return
        values = []
        for check in checks:
            if "check_type" not in check or "status" not in check:
                raise ValueError(f"Malformed control check payload: {check}")
            values.append(
                {
                    "control_check_id": check.get("control_check_id", uuid4()),
                    "session_id": session_id,
                    "check_type": check["check_type"],
                    "status": check["status"],
                    "severity": check.get("severity", "info"),
                    "details": check.get("details", {}),
                }
            )
        stmt = insert(ControlCheckORM).values(values)
        await self.db.execute(stmt)

    async def commit(self) -> None:
        await self.db.commit()

    def _build_quality_metrics(self, control_rows) -> QualityMetrics:
        if not control_rows:
            return QualityMetrics()
        distinct_checks = [row for row in control_rows if row.check_type == "distinct_evidence"]
        contradiction_checks = [row for row in control_rows if row.check_type == "contradiction_quality"]
        repetition_checks = [row for row in control_rows if row.check_type == "unsupported_repetition"]

        def pass_ratio(rows, invert: bool = False) -> float:
            if not rows:
                return 0.0
            passed = sum(1 for row in rows if row.status == "pass")
            ratio = passed / len(rows)
            if invert:
                return round(1.0 - ratio, 2)
            return round(ratio, 2)

        evidence_diversity_score = pass_ratio(distinct_checks)
        contradiction_score = pass_ratio(contradiction_checks)
        repetition_risk_score = pass_ratio(repetition_checks, invert=True)

        components = [value for value in [evidence_diversity_score, contradiction_score] if value > 0]

        debate_quality_score = round(sum(components) / len(components), 2) if components else 0.0
        judge_check_count = len(distinct_checks) + len(contradiction_checks) + len(repetition_checks)

        return QualityMetrics(
            debate_quality_score=debate_quality_score,
            evidence_diversity_score=evidence_diversity_score,
            repetition_risk_score=repetition_risk_score,
            judge_check_count=judge_check_count,
        )

    async def list_sessions(self, limit: int = 20) -> list[SessionListItemResponse]:
        action_counts_sq = (
            select(
                AgentActionORM.session_id.label("session_id"),
                func.count(AgentActionORM.session_id).label("total_actions"),
            )
            .group_by(AgentActionORM.session_id)
            .subquery()
        )

        claim_counts_sq = (
            select(
                AgentClaimORM.session_id.label("session_id"),
                func.count(AgentClaimORM.claim_id).label("total_claims"),
            )
            .group_by(AgentClaimORM.session_id)
            .subquery()
        )

        memory_counts_sq = (
            select(
                SessionMemoryEpisodeORM.session_id.label("session_id"),
                func.count(SessionMemoryEpisodeORM.episode_id).label("total_episodes"),
            )
            .group_by(SessionMemoryEpisodeORM.session_id)
            .subquery()
        )

        stmt = (
            select(
                SecuritySessionORM.session_id,
                SecuritySessionORM.ticker,
                SecuritySessionORM.mode,
                SecuritySessionORM.status,
                SecuritySessionORM.created_at,
                SecuritySessionORM.updated_at,
                func.coalesce(action_counts_sq.c.total_actions, 0).label("total_actions"),
                func.coalesce(claim_counts_sq.c.total_claims, 0).label("total_claims"),
                func.coalesce(memory_counts_sq.c.total_episodes, 0).label("total_episodes"),
            )
            .outerjoin(
                action_counts_sq,
                action_counts_sq.c.session_id == SecuritySessionORM.session_id,
            )
            .outerjoin(
                claim_counts_sq,
                claim_counts_sq.c.session_id == SecuritySessionORM.session_id,
            )
            .outerjoin(
                memory_counts_sq,
                memory_counts_sq.c.session_id == SecuritySessionORM.session_id,
            )
            .order_by(
                desc(func.coalesce(SecuritySessionORM.updated_at, SecuritySessionORM.created_at))
            )
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            SessionListItemResponse(
                session_id=row.session_id,
                ticker=row.ticker,
                mode=row.mode,
                status=row.status,
                created_at=row.created_at,
                updated_at=row.updated_at,
                total_actions=row.total_actions,
                total_claims=row.total_claims,
                total_episodes=row.total_episodes,
            )
            for row in rows
        ]

    async def get_session_detail(self, session_id) -> SessionDetailResponse | None:
        session_stmt = select(SecuritySessionORM).where(SecuritySessionORM.session_id == session_id)
        session_result = await self.db.execute(session_stmt)
        session_row = session_result.scalar_one_or_none()

        if session_row is None:
            return None

        snapshot_stmt = (
            select(WorldStateSnapshotORM)
            .where(WorldStateSnapshotORM.session_id == session_id)
            .order_by(desc(WorldStateSnapshotORM.created_at))
            .limit(1)
        )
        snapshot_result = await self.db.execute(snapshot_stmt)
        snapshot_row = snapshot_result.scalar_one_or_none()

        evidence_stmt = (
            select(EvidenceItemORM)
            .where(EvidenceItemORM.session_id == session_id)
            .order_by(desc(EvidenceItemORM.observed_at), desc(EvidenceItemORM.created_at))
        )
        evidence_result = await self.db.execute(evidence_stmt)
        evidence_rows = list(evidence_result.scalars().all())

        actions_stmt = (
            select(AgentActionORM)
            .where(AgentActionORM.session_id == session_id)
            .order_by(AgentActionORM.round_no.asc(), AgentActionORM.created_at.asc())
        )
        actions_result = await self.db.execute(actions_stmt)
        action_rows = list(actions_result.scalars().all())

        claims_stmt = (
            select(AgentClaimORM)
            .where(AgentClaimORM.session_id == session_id)
            .order_by(AgentClaimORM.round_no.asc(), AgentClaimORM.created_at.asc())
        )
        claims_result = await self.db.execute(claims_stmt)
        claim_rows = list(claims_result.scalars().all())

        control_rows_stmt = (
            select(ControlCheckORM)
            .where(ControlCheckORM.session_id == session_id)
            .order_by(ControlCheckORM.created_at.asc())
        )
        control_rows_result = await self.db.execute(control_rows_stmt)
        control_rows = list(control_rows_result.scalars().all())

        quality_metrics = self._build_quality_metrics(control_rows)

        control_counts_stmt = (
            select(ControlCheckORM.status, func.count(ControlCheckORM.control_check_id))
            .where(ControlCheckORM.session_id == session_id)
            .group_by(ControlCheckORM.status)
        )
        control_counts_result = await self.db.execute(control_counts_stmt)
        control_counts = {status: count for status, count in control_counts_result.all()}

        severity_counts_stmt = (
            select(ControlCheckORM.severity, func.count(ControlCheckORM.control_check_id))
            .where(ControlCheckORM.session_id == session_id)
            .group_by(ControlCheckORM.severity)
        )
        severity_counts_result = await self.db.execute(severity_counts_stmt)
        severity_counts = {severity: count for severity, count in severity_counts_result.all()}

        memory_rows_stmt = (
            select(SessionMemoryEpisodeORM)
            .where(SessionMemoryEpisodeORM.session_id == session_id)
            .order_by(SessionMemoryEpisodeORM.created_at.asc())
        )
        memory_rows_result = await self.db.execute(memory_rows_stmt)
        memory_rows = list(memory_rows_result.scalars().all())

        memory_counts_stmt = (
            select(SessionMemoryEpisodeORM.episode_type, func.count(SessionMemoryEpisodeORM.episode_id))
            .where(SessionMemoryEpisodeORM.session_id == session_id)
            .group_by(SessionMemoryEpisodeORM.episode_type)
        )
        memory_counts_result = await self.db.execute(memory_counts_stmt)
        memory_counts = {episode_type: count for episode_type, count in memory_counts_result.all()}

        world_state = WorldState(
            security={
                "ticker": session_row.ticker,
                "as_of_date": session_row.as_of_date,
            },
            market_state=snapshot_row.market_state if snapshot_row else {},
            fundamental_state=snapshot_row.fundamental_state if snapshot_row else {},
            event_state=snapshot_row.event_state if snapshot_row else {},
            peer_state=snapshot_row.peer_state if snapshot_row else {},
            state_version=snapshot_row.state_version if snapshot_row else "v1",
        )
        evidence_items = [
            EvidenceItem(
                evidence_id=row.evidence_id,
                source_type=row.source_type,
                source_ref=row.source_ref,
                observed_at=row.observed_at,
                title=row.title,
                summary=row.summary,
                payload=row.payload,
                freshness_score=row.freshness_score,
                confidence=row.confidence,
            )
            for row in evidence_rows
        ]

        actions = [
            AgentAction(
                agent_name=row.agent_name,
                action_type=row.action_type,
                rationale=row.rationale,
                evidence_ids=row.evidence_ids or [],
                confidence=row.confidence,
            )
            for row in action_rows
        ]

        claims = [
            Claim(
                claim_id=row.claim_id,
                side=row.side,
                thesis=row.thesis,
                confidence=row.confidence,
                evidence_ids=row.evidence_ids or [],
                status=row.status,
            )
            for row in claim_rows
        ]

        return SessionDetailResponse(
            metadata=SessionMetadata(
                session_id=session_row.session_id,
                ticker=session_row.ticker,
                as_of_date=session_row.as_of_date.isoformat() if session_row.as_of_date else None,
                window_days=session_row.window_days,
                mode=session_row.mode,
                status=session_row.status,
                created_at=session_row.created_at,
                updated_at=session_row.updated_at,
            ),
            world_state=world_state,
            evidence_items=evidence_items,
            actions=actions,
            claims=claims,
            controls={
                "summary": {
                    "total_checks": len(control_rows),
                    "by_status": control_counts,
                    "by_severity": severity_counts,
                },
                "checks": [
                    {
                        "check_type": row.check_type,
                        "status": row.status,
                        "severity": row.severity,
                        "details": row.details,
                        "created_at": row.created_at,
                    }
                    for row in control_rows
                ],
            },
            memory_summary={
                "total_episodes": len(memory_rows),
                "by_type": memory_counts,
                "episodes": [
                    {
                        "episode_type": row.episode_type,
                        "summary": row.summary,
                        "payload": row.payload,
                        "created_at": row.created_at,
                    }
                    for row in memory_rows
                ],
            },
            quality_metrics=quality_metrics,
        )

    async def get_session_row(self, session_id) -> SessionDetailResponse | None:
        session_stmt = select(SecuritySessionORM).where(SecuritySessionORM.session_id == session_id)
        session_result = await self.db.execute(session_stmt)
        session_row = session_result.scalar_one_or_none()

        if session_row is None:
            return None

        snapshot_stmt = (
            select(WorldStateSnapshotORM)
            .where(WorldStateSnapshotORM.session_id == session_id)
            .order_by(desc(WorldStateSnapshotORM.created_at))
            .limit(1)
        )
        snapshot_result = await self.db.execute(snapshot_stmt)
        snapshot_row = snapshot_result.scalar_one_or_none()

        evidence_stmt = (
            select(EvidenceItemORM)
            .where(EvidenceItemORM.session_id == session_id)
            .order_by(desc(EvidenceItemORM.created_at))
        )
        evidence_result = await self.db.execute(evidence_stmt)
        evidence_rows = list(evidence_result.scalars().all())

        actions_stmt = (
            select(AgentActionORM)
            .where(AgentActionORM.session_id == session_id)
            .order_by(AgentActionORM.round_no.asc(), AgentActionORM.created_at.asc())
        )
        actions_result = await self.db.execute(actions_stmt)
        action_rows = list(actions_result.scalars().all())

        claims_stmt = (
            select(AgentClaimORM)
            .where(AgentClaimORM.session_id == session_id)
            .order_by(AgentClaimORM.round_no.asc(), AgentClaimORM.created_at.asc())
        )
        claims_result = await self.db.execute(claims_stmt)
        claim_rows = list(claims_result.scalars().all())

        world_state = WorldState(
            security={
                "ticker": session_row.ticker,
                "as_of_date": session_row.as_of_date,
            },
            market_state=snapshot_row.market_state if snapshot_row else {},
            fundamental_state=snapshot_row.fundamental_state if snapshot_row else {},
            event_state=snapshot_row.event_state if snapshot_row else {},
            peer_state=snapshot_row.peer_state if snapshot_row else {},
            state_version=snapshot_row.state_version if snapshot_row else "v1",
        )

        evidence_items = [
            EvidenceItem(
                evidence_id=row.evidence_id,
                source_type=row.source_type,
                source_ref=row.source_ref,
                observed_at=row.observed_at,
                title=row.title,
                summary=row.summary,
                payload=row.payload,
                freshness_score=row.freshness_score,
                confidence=row.confidence,
            )
            for row in evidence_rows
        ]

        actions = [
            AgentAction(
                round_no=row.round_no,
                agent_name=row.agent_name,
                action_type=row.action_type,
                rationale=row.rationale,
                evidence_ids=row.evidence_ids or [],
                confidence=row.confidence,
            )
            for row in action_rows
        ]

        claims = [
            Claim(
                claim_id=row.claim_id,
                round_no=row.round_no,
                side=row.side,
                thesis=row.thesis,
                confidence=row.confidence,
                evidence_ids=row.evidence_ids or [],
                status=row.status,
            )
            for row in claim_rows
        ]

        return SessionDetailResponse(
            metadata=SessionMetadata(
                session_id=session_row.session_id,
                ticker=session_row.ticker,
                as_of_date=session_row.as_of_date.isoformat() if session_row.as_of_date else None,
                window_days=session_row.window_days,
                mode=session_row.mode,
                status=session_row.status,
                created_at=session_row.created_at,
                updated_at=session_row.updated_at,
            ),
            world_state=world_state,
            evidence_items=evidence_items,
            actions=actions,
            claims=claims,
            controls={
                "grounding_ok": True,
                "contradictions": [],
            },
            memory_summary={
                "episodes_found": 0,
                "patterns_found": 0,
            },
        )

    async def get_next_round_no(self, session_id) -> int:
        stmt = select(func.max(AgentActionORM.round_no)).where(AgentActionORM.session_id == session_id)
        result = await self.db.execute(stmt)
        max_round = result.scalar_one_or_none()
        return 1 if max_round is None else max_round + 1

    async def get_recent_evidence_items(self, session_id, limit: int = 3) -> list[EvidenceItem]:
        stmt = (
            select(EvidenceItemORM)
            .where(EvidenceItemORM.session_id == session_id)
            .order_by(desc(EvidenceItemORM.observed_at), desc(EvidenceItemORM.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        return [
            EvidenceItem(
                evidence_id=row.evidence_id,
                source_type=row.source_type,
                source_ref=row.source_ref,
                observed_at=row.observed_at,
                title=row.title,
                summary=row.summary,
                payload=row.payload,
                freshness_score=row.freshness_score,
                confidence=row.confidence,
            )
            for row in rows
        ]

    async def insert_agent_action(self, session_id, round_no: int, action: AgentAction) -> None:
        row = AgentActionORM(
            session_id=session_id,
            round_no=round_no,
            agent_name=action.agent_name,
            action_type=action.action_type,
            rationale=action.rationale,
            evidence_ids=action.evidence_ids,
            confidence=action.confidence,
        )
        self.db.add(row)

    async def insert_agent_claim(self, session_id, round_no: int, claim: Claim) -> None:
        row = AgentClaimORM(
            claim_id=claim.claim_id,
            session_id=session_id,
            round_no=round_no,
            side=claim.side,
            thesis=claim.thesis,
            confidence=claim.confidence,
            evidence_ids=claim.evidence_ids,
            status=claim.status,
        )
        self.db.add(row)

    async def get_latest_claim(self, session_id) -> Claim | None:
        stmt = (
            select(AgentClaimORM)
            .where(AgentClaimORM.session_id == session_id)
            .order_by(desc(AgentClaimORM.round_no), desc(AgentClaimORM.created_at))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return Claim(
            claim_id=row.claim_id,
            side=row.side,
            thesis=row.thesis,
            confidence=row.confidence,
            evidence_ids=row.evidence_ids or [],
            status=row.status,
        )

    async def get_recent_claims(self, session_id, limit: int = 2) -> list[Claim]:
        stmt = (
            select(AgentClaimORM)
            .where(AgentClaimORM.session_id == session_id)
            .order_by(desc(AgentClaimORM.round_no), desc(AgentClaimORM.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        return [
            Claim(
                claim_id=row.claim_id,
                round_no=row.round_no,
                side=row.side,
                thesis=row.thesis,
                confidence=row.confidence,
                evidence_ids=row.evidence_ids or [],
                status=row.status,
            )
            for row in rows
        ]

    async def get_recent_actions(self, session_id, limit: int = 6) -> list[AgentAction]:
        stmt = (
            select(AgentActionORM)
            .where(AgentActionORM.session_id == session_id)
            .order_by(desc(AgentActionORM.round_no), desc(AgentActionORM.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        return [
            AgentAction(
                round_no=row.round_no,
                agent_name=row.agent_name,
                action_type=row.action_type,
                rationale=row.rationale,
                evidence_ids=row.evidence_ids or [],
                confidence=row.confidence,
            )
            for row in rows
        ]