"""Unit tests for Technician service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.technician.exceptions import TechnicianNotFoundError, TechnicianValidationError
from app.domains.technician.service import TechnicianService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.user_id = uuid4()
    entity.employee_id = "sample-employee_id"
    entity.home_base_latitude = Decimal('10.00')
    entity.home_base_longitude = Decimal('10.00')
    entity.max_daily_hours = 1
    entity.status = "draft"
    entity.certifications = "sample-certifications"
    entity.vehicle_info = "sample-vehicle_info"
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
    return TechnicianService(repository=mock_repo)


class TestTechnicianServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(TechnicianValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(TechnicianValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestTechnicianServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestTechnicianServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestTechnicianServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestTechnicianServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestTechnicianDomainMethods:
    @pytest.mark.asyncio
    async def test_set_status_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianNotFoundError):
            await service.set_status(entity_id=uuid4(), tenant_id=uuid4(), status="sample")

    @pytest.mark.asyncio
    async def test_set_status_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.set_status(entity_id=entity.id, tenant_id=uuid4(), status="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_location_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianNotFoundError):
            await service.update_location(entity_id=uuid4(), tenant_id=uuid4(), lat=Decimal("10.00"), lng=Decimal("10.00"))

    @pytest.mark.asyncio
    async def test_update_location_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.update_location(entity_id=entity.id, tenant_id=uuid4(), lat=Decimal("10.00"), lng=Decimal("10.00"))
        assert result is not None

    @pytest.mark.asyncio
    async def test_calculate_utilization_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TechnicianNotFoundError):
            await service.calculate_utilization(entity_id=uuid4(), tenant_id=uuid4(), start=None, end=None)

    @pytest.mark.asyncio
    async def test_calculate_utilization_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.calculate_utilization(entity_id=entity.id, tenant_id=uuid4(), start=None, end=None)
        assert result is not None
