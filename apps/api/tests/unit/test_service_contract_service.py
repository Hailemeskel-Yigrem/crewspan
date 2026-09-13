"""Unit tests for ServiceContract service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.service_contract.exceptions import ServiceContractNotFoundError, ServiceContractValidationError
from app.domains.service_contract.service import ServiceContractService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.customer_id = uuid4()
    entity.contract_number = "sample-contract_number"
    entity.name = "sample-name"
    entity.start_date = date.today()
    entity.end_date = date.today()
    entity.billing_frequency = "sample-billing_frequency"
    entity.annual_value = Decimal('10.00')
    entity.covered_sites = []
    entity.terms = {}
    entity.status = "draft"
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
    return ServiceContractService(repository=mock_repo)


class TestServiceContractServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(ServiceContractValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(ServiceContractValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestServiceContractServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ServiceContractNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestServiceContractServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestServiceContractServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestServiceContractServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestServiceContractDomainMethods:
    @pytest.mark.asyncio
    async def test_renew_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ServiceContractNotFoundError):
            await service.renew(entity_id=uuid4(), tenant_id=uuid4(), new_end_date=None)

    @pytest.mark.asyncio
    async def test_renew_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.renew(entity_id=entity.id, tenant_id=uuid4(), new_end_date=None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_terminate_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ServiceContractNotFoundError):
            await service.terminate(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_terminate_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.terminate(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_work_orders_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ServiceContractNotFoundError):
            await service.generate_work_orders(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_generate_work_orders_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.generate_work_orders(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
