"""Unit tests for Dispatch service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.dispatch.exceptions import DispatchNotFoundError, DispatchValidationError
from app.domains.dispatch.service import DispatchService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.work_order_id = uuid4()
    entity.technician_id = uuid4()
    entity.dispatched_at = datetime.now(timezone.utc)
    entity.accepted_at = datetime.now(timezone.utc)
    entity.status = "draft"
    entity.dispatch_notes = "sample-dispatch_notes"
    entity.route_eta_minutes = 1
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
    return DispatchService(repository=mock_repo)


class TestDispatchServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(DispatchValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(DispatchValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestDispatchServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(DispatchNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestDispatchServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestDispatchServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestDispatchServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestDispatchDomainMethods:
    @pytest.mark.asyncio
    async def test_accept_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(DispatchNotFoundError):
            await service.accept(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_accept_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.accept(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_decline_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(DispatchNotFoundError):
            await service.decline(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_decline_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.decline(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_en_route_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(DispatchNotFoundError):
            await service.en_route(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_en_route_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.en_route(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_arrive_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(DispatchNotFoundError):
            await service.arrive(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_arrive_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.arrive(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
