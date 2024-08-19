"""Unit tests for CustomerSite service layer."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.customer_site.exceptions import CustomerSiteNotFoundError, CustomerSiteValidationError
from app.domains.customer_site.service import CustomerSiteService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.status = "draft"
    repo.get_by_id.return_value = entity
    repo.list.return_value = ([entity], 1)
    repo.count.return_value = 1
    repo.exists.return_value = True
    return repo


@pytest.fixture
def service(mock_repo):
    return CustomerSiteService(repository=mock_repo)


class TestCustomerSiteServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(CustomerSiteValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestCustomerSiteServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerSiteNotFoundError):
            await service.get(tenant_id=uuid4(), entity_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(tenant_id=uuid4(), entity_id=uuid4())
        assert result is not None


class TestCustomerSiteServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestCustomerSiteServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestCustomerSiteServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestCustomerSiteDomainMethods:
    @pytest.mark.asyncio
    async def test_geocode_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerSiteNotFoundError):
            await service.geocode(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_geocode_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.geocode(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_validate_access_window_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerSiteNotFoundError):
            await service.validate_access_window(entity_id=uuid4(), tenant_id=uuid4(), at=None)

    @pytest.mark.asyncio
    async def test_validate_access_window_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.validate_access_window(entity_id=entity.id, tenant_id=uuid4(), at=None)
        assert result is not None
