"""Unit tests for SlaPolicy service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.sla_policy.exceptions import SlaPolicyNotFoundError, SlaPolicyValidationError
from app.domains.sla_policy.service import SlaPolicyService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.name = "sample-name"
    entity.description = "sample-description"
    entity.priority = "sample-priority"
    entity.response_minutes = 1
    entity.resolution_minutes = 1
    entity.business_hours_only = True
    entity.escalation_rules = "sample-escalation_rules"
    entity.is_active = True
    entity.created_at = datetime.now(timezone.utc)
    entity.updated_at = datetime.now(timezone.utc)
    entity.deleted_at = None
    repo.get_by_id.return_value = entity
    repo.list.return_value = ([entity], 1)
    repo.count.return_value = 1
    repo.exists.return_value = True
    repo.create.return_value = entity
    repo.update.return_value = entity
    return repo


@pytest.fixture
def service(mock_repo):
    return SlaPolicyService(repository=mock_repo)


class TestSlaPolicyServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(SlaPolicyValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestSlaPolicyServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SlaPolicyNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestSlaPolicyServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestSlaPolicyServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestSlaPolicyServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestSlaPolicyDomainMethods:
    @pytest.mark.asyncio
    async def test_evaluate_deadlines_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SlaPolicyNotFoundError):
            await service.evaluate_deadlines(entity_id=uuid4(), tenant_id=uuid4(), opened_at=None)

    @pytest.mark.asyncio
    async def test_evaluate_deadlines_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.evaluate_deadlines(entity_id=entity.id, tenant_id=uuid4(), opened_at=None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_clone_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(SlaPolicyNotFoundError):
            await service.clone(entity_id=uuid4(), tenant_id=uuid4(), new_name="sample")

    @pytest.mark.asyncio
    async def test_clone_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.clone(entity_id=entity.id, tenant_id=uuid4(), new_name="sample")
        assert result is not None
