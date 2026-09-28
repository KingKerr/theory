from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from core_api.models.domain import Claim
from repositories.sessions import SessionRepository


@pytest.mark.asyncio
async def test_get_recent_claims_filters_to_round_2_active_bear_openings() -> None:
    session_id = uuid4()
    evidence_id = uuid4()

    eligible_bear_opening = Claim(
        claim_id=uuid4(),
        round_no=2,
        side="bear",
        claim_type="opening",
        thesis=(
            "The available evidence does not establish enough support for "
            "the constructive case to be considered durable."
        ),
        confidence=0.68,
        evidence_ids=[evidence_id],
        target_claim_ids=[uuid4()],
        status="active",
    )

    session = AsyncMock()
    result = Mock()
    result.scalars.return_value.all.return_value = [eligible_bear_opening]
    session.execute.return_value = result

    repository = SessionRepository(session)

    claims = await repository.get_recent_claims(
        session_id=session_id,
        side="bear",
        round_no=2,
        claim_type="opening",
        status="active",
        limit=3,
    )

    assert [claim.claim_id for claim in claims] == [
        eligible_bear_opening.claim_id
    ]

    session.execute.assert_awaited_once()

    statement = session.execute.await_args.args[0]
    compiled = statement.compile()
    parameter_values = set(compiled.params.values())

    assert session_id in parameter_values
    assert "bear" in parameter_values
    assert 2 in parameter_values
    assert "opening" in parameter_values
    assert "active" in parameter_values
    assert 3 in parameter_values