"""Unit tests for Customer service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.customer.exceptions import CustomerNotFoundError, CustomerValidationError
from app.domains.customer.service import CustomerService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.account_number = "sample-account_number"
    entity.name = "sample-name"
    entity.customer_type = "sample-customer_type"
    entity.billing_email = "sample-billing_email"
    entity.billing_address = {}
    entity.credit_limit = Decimal('10.00')
    entity.payment_terms_days = 1
    entity.notes = "sample-notes"
    entity.is_active = True
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
    return CustomerService(repository=mock_repo)


class TestCustomerServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(CustomerValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestCustomerServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestCustomerServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestCustomerServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestCustomerServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestCustomerDomainMethods:
    @pytest.mark.asyncio
    async def test_update_credit_limit_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerNotFoundError):
            await service.update_credit_limit(entity_id=uuid4(), tenant_id=uuid4(), limit=Decimal("10.00"))

    @pytest.mark.asyncio
    async def test_update_credit_limit_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.update_credit_limit(entity_id=entity.id, tenant_id=uuid4(), limit=Decimal("10.00"))
        assert result is not None

    @pytest.mark.asyncio
    async def test_merge_into_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerNotFoundError):
            await service.merge_into(entity_id=uuid4(), tenant_id=uuid4(), target_id=uuid4())

    @pytest.mark.asyncio
    async def test_merge_into_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.merge_into(entity_id=entity.id, tenant_id=uuid4(), target_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_archive_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(CustomerNotFoundError):
            await service.archive(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_archive_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.archive(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
