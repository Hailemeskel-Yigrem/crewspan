"""Unit tests for SlaBreach repository layer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.sla_breach.repository import SlaBreachRepository


@pytest.fixture
def mock_session():
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalar_one.return_value = 0
    result.scalars.return_value.all.return_value = []
    session.execute.return_value = result
    return session


@pytest.fixture
def repository(mock_session):
    return SlaBreachRepository(mock_session)


class TestSlaBreachRepositoryQueries:
    @pytest.mark.asyncio
    async def test_get_by_id_executes_query(self, repository, mock_session):
        entity_id = uuid4()
        await repository.get_by_id(entity_id, tenant_id=uuid4(),)
        mock_session.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_list_returns_tuple(self, repository):
        rows, total = await repository.list(tenant_id=uuid4(), page=1, page_size=10)
        assert isinstance(rows, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_exists_returns_bool(self, repository):
        result = await repository.exists(uuid4(), tenant_id=uuid4(),)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_count_returns_int(self, repository):
        result = await repository.count(tenant_id=uuid4(),)
        assert isinstance(result, int)
