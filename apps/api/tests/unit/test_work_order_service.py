"""Unit tests for WorkOrder service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.work_order.exceptions import WorkOrderNotFoundError, WorkOrderValidationError
from app.domains.work_order.service import WorkOrderService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.order_number = "sample-order_number"
    entity.customer_id = uuid4()
    entity.site_id = uuid4()
    entity.title = "sample-title"
    entity.description = "sample-description"
    entity.priority = "sample-priority"
    entity.status = "draft"
    entity.scheduled_start = datetime.now(timezone.utc)
    entity.scheduled_end = datetime.now(timezone.utc)
    entity.assigned_technician_id = uuid4()
    entity.sla_policy_id = uuid4()
    entity.estimated_duration_minutes = 1
    entity.completion_notes = "sample-completion_notes"
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
    return WorkOrderService(repository=mock_repo)


class TestWorkOrderServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(WorkOrderValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(WorkOrderValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestWorkOrderServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestWorkOrderServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestWorkOrderServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestWorkOrderServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestWorkOrderDomainMethods:
    @pytest.mark.asyncio
    async def test_submit_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderNotFoundError):
            await service.submit(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_submit_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.submit(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_assign_technician_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderNotFoundError):
            await service.assign_technician(entity_id=uuid4(), tenant_id=uuid4(), technician_id=uuid4())

    @pytest.mark.asyncio
    async def test_assign_technician_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.assign_technician(entity_id=entity.id, tenant_id=uuid4(), technician_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_start_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderNotFoundError):
            await service.start(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_start_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.start(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_complete_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderNotFoundError):
            await service.complete(entity_id=uuid4(), tenant_id=uuid4(), notes="sample")

    @pytest.mark.asyncio
    async def test_complete_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.complete(entity_id=entity.id, tenant_id=uuid4(), notes="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_cancel_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WorkOrderNotFoundError):
            await service.cancel(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_cancel_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.cancel(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None
