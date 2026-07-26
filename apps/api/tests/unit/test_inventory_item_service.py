"""Unit tests for InventoryItem service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.inventory_item.exceptions import InventoryItemNotFoundError, InventoryItemValidationError
from app.domains.inventory_item.service import InventoryItemService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.sku = "sample-sku"
    entity.name = "sample-name"
    entity.description = "sample-description"
    entity.unit_of_measure = "sample-unit_of_measure"
    entity.unit_cost = Decimal('10.00')
    entity.reorder_point = 1
    entity.reorder_quantity = 1
    entity.is_active = True
    entity.category = "sample-category"
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
    return InventoryItemService(repository=mock_repo)


class TestInventoryItemServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(InventoryItemValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestInventoryItemServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InventoryItemNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestInventoryItemServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestInventoryItemServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestInventoryItemServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestInventoryItemDomainMethods:
    @pytest.mark.asyncio
    async def test_adjust_reorder_levels_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InventoryItemNotFoundError):
            await service.adjust_reorder_levels(entity_id=uuid4(), tenant_id=uuid4(), point=1, quantity=1)

    @pytest.mark.asyncio
    async def test_adjust_reorder_levels_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.adjust_reorder_levels(entity_id=entity.id, tenant_id=uuid4(), point=1, quantity=1)
        assert result is not None

    @pytest.mark.asyncio
    async def test_deactivate_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InventoryItemNotFoundError):
            await service.deactivate(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_deactivate_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.deactivate(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_calculate_stock_value_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InventoryItemNotFoundError):
            await service.calculate_stock_value(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_calculate_stock_value_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.calculate_stock_value(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
