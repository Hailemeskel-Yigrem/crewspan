"""Unit tests for WorkOrderTask service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.work_order_task.exceptions import WorkOrderTaskNotFoundError, WorkOrderTaskValidationError
from app.domains.work_order_task.service import WorkOrderTaskService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.work_order_id = uuid4()
    entity.sequence = 1
    entity.title = "sample-title"
    entity.instructions = "sample-instructions"
    entity.is_required = True
    entity.status = "draft"
    entity.completed_at = datetime.now(timezone.utc)
    entity.completed_by_id = uuid4()
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
    return WorkOrderTaskService(repository=mock_repo)


class TestWorkOrderTaskServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(WorkOrderTaskValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(WorkOrderTaskValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestWorkOrderTaskServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderTaskNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestWorkOrderTaskServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestWorkOrderTaskServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestWorkOrderTaskServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestWorkOrderTaskDomainMethods:
    @pytest.mark.asyncio
    async def test_complete_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderTaskNotFoundError):
            await service.complete(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_complete_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        entity.status = "in_progress"
        result = await service.complete(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_reopen_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderTaskNotFoundError):
            await service.reopen(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_reopen_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.reopen(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_reorder_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderTaskNotFoundError):
            await service.reorder(entity_id=uuid4(), tenant_id=uuid4(), sequence=1)

    @pytest.mark.asyncio
    async def test_reorder_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.reorder(entity_id=entity.id, tenant_id=uuid4(), sequence=1)
        assert result is not None
