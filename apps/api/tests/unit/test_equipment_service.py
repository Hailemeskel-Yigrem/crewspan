"""Unit tests for Equipment service layer."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.equipment.exceptions import EquipmentNotFoundError, EquipmentValidationError
from app.domains.equipment.service import EquipmentService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.customer_id = uuid4()
    entity.site_id = uuid4()
    entity.asset_tag = "sample-asset_tag"
    entity.name = "sample-name"
    entity.manufacturer = "sample-manufacturer"
    entity.model_number = "sample-model_number"
    entity.serial_number = "sample-serial_number"
    entity.install_date = date.today()
    entity.warranty_expires = date.today()
    entity.specifications = {}
    entity.status = "draft"
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
    return EquipmentService(repository=mock_repo)


class TestEquipmentServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(EquipmentValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(EquipmentValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestEquipmentServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(EquipmentNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestEquipmentServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestEquipmentServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestEquipmentServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestEquipmentDomainMethods:
    @pytest.mark.asyncio
    async def test_record_service_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(EquipmentNotFoundError):
            await service.record_service(entity_id=uuid4(), tenant_id=uuid4(), work_order_id=uuid4(), notes="sample")

    @pytest.mark.asyncio
    async def test_record_service_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.record_service(entity_id=entity.id, tenant_id=uuid4(), work_order_id=uuid4(), notes="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_retire_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(EquipmentNotFoundError):
            await service.retire(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_retire_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.retire(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None
