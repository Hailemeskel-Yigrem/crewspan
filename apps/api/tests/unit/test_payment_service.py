"""Unit tests for Payment service layer."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.payment.exceptions import PaymentNotFoundError, PaymentValidationError
from app.domains.payment.service import PaymentService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.invoice_id = uuid4()
    entity.amount = Decimal('10.00')
    entity.payment_method = "sample-payment_method"
    entity.payment_date = date.today()
    entity.reference_number = "sample-reference_number"
    entity.status = "draft"
    entity.processor_response = {}
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
    return PaymentService(repository=mock_repo)


class TestPaymentServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(PaymentValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(PaymentValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestPaymentServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PaymentNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestPaymentServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestPaymentServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestPaymentServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestPaymentDomainMethods:
    @pytest.mark.asyncio
    async def test_refund_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PaymentNotFoundError):
            await service.refund(entity_id=uuid4(), tenant_id=uuid4(), amount=Decimal("10.00"), reason="sample")

    @pytest.mark.asyncio
    async def test_refund_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.refund(entity_id=entity.id, tenant_id=uuid4(), amount=Decimal("10.00"), reason="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_reconcile_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PaymentNotFoundError):
            await service.reconcile(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_reconcile_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.reconcile(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
