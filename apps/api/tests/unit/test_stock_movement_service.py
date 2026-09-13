"""Unit tests for StockMovement service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.stock_movement.exceptions import (
    StockMovementNotFoundError,
    StockMovementValidationError,
)
from app.domains.stock_movement.service import StockMovementService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.item_id = uuid4()
    entity.from_location_id = uuid4()
    entity.to_location_id = uuid4()
    entity.quantity = Decimal('10.00')
    entity.movement_type = "sample-movement_type"
    entity.reference_type = "sample-reference_type"
    entity.reference_id = uuid4()
    entity.performed_by_id = uuid4()
    entity.notes = "sample-notes"
    entity.created_at = datetime.now(UTC)
    entity.updated_at = datetime.now(UTC)
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
    return StockMovementService(repository=mock_repo)


class TestStockMovementServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(StockMovementValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestStockMovementServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(StockMovementNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestStockMovementServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestStockMovementServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestStockMovementServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestStockMovementDomainMethods:
    @pytest.mark.asyncio
    async def test_validate_quantity_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(StockMovementNotFoundError):
            await service.validate_quantity(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_validate_quantity_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.validate_quantity(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_reverse_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(StockMovementNotFoundError):
            await service.reverse(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_reverse_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.reverse(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None
