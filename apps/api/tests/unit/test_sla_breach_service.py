"""Unit tests for SlaBreach service layer."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.sla_breach.exceptions import SlaBreachNotFoundError, SlaBreachValidationError
from app.domains.sla_breach.service import SlaBreachService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.status = "draft"
    repo.get_by_id.return_value = entity
    repo.list.return_value = ([entity], 1)
    repo.count.return_value = 1
    repo.exists.return_value = True
    return repo


@pytest.fixture
def service(mock_repo):
    return SlaBreachService(repository=mock_repo)


class TestSlaBreachServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(SlaBreachValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestSlaBreachServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SlaBreachNotFoundError):
            await service.get(tenant_id=uuid4(), entity_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(tenant_id=uuid4(), entity_id=uuid4())
        assert result is not None


class TestSlaBreachServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestSlaBreachServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestSlaBreachServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestSlaBreachDomainMethods:
    @pytest.mark.asyncio
    async def test_acknowledge_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SlaBreachNotFoundError):
            await service.acknowledge(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_acknowledge_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.acknowledge(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_escalate_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SlaBreachNotFoundError):
            await service.escalate(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_escalate_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.escalate(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
