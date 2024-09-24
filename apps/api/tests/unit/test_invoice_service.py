"""Unit tests for Invoice service layer."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.invoice.exceptions import InvoiceNotFoundError, InvoiceValidationError
from app.domains.invoice.service import InvoiceService


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
    return InvoiceService(repository=mock_repo)


class TestInvoiceServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(InvoiceValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(InvoiceValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestInvoiceServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InvoiceNotFoundError):
            await service.get(tenant_id=uuid4(), entity_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(tenant_id=uuid4(), entity_id=uuid4())
        assert result is not None


class TestInvoiceServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestInvoiceServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestInvoiceServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestInvoiceDomainMethods:
    @pytest.mark.asyncio
    async def test_finalize_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InvoiceNotFoundError):
            await service.finalize(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_finalize_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.finalize(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_send_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InvoiceNotFoundError):
            await service.send(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_send_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.send(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_void_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InvoiceNotFoundError):
            await service.void(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_void_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.void(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_recalculate_totals_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(InvoiceNotFoundError):
            await service.recalculate_totals(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_recalculate_totals_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.recalculate_totals(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
