"""Unit tests for Schedule service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.schedule.exceptions import ScheduleNotFoundError, ScheduleValidationError
from app.domains.schedule.service import ScheduleService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.technician_id = uuid4()
    entity.work_order_id = uuid4()
    entity.event_type = "sample-event_type"
    entity.starts_at = datetime.now(timezone.utc)
    entity.ends_at = datetime.now(timezone.utc)
    entity.title = "sample-title"
    entity.notes = "sample-notes"
    entity.is_locked = True
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
    return ScheduleService(repository=mock_repo)


class TestScheduleServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(ScheduleValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestScheduleServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ScheduleNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestScheduleServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestScheduleServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestScheduleServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestScheduleDomainMethods:
    @pytest.mark.asyncio
    async def test_lock_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ScheduleNotFoundError):
            await service.lock(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_lock_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.lock(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_unlock_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ScheduleNotFoundError):
            await service.unlock(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_unlock_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.unlock(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_detect_conflicts_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ScheduleNotFoundError):
            await service.detect_conflicts(entity_id=uuid4(), tenant_id=uuid4(), starts_at=None, ends_at=None)

    @pytest.mark.asyncio
    async def test_detect_conflicts_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.detect_conflicts(entity_id=entity.id, tenant_id=uuid4(), starts_at=None, ends_at=None)
        assert result is not None
