"""Unit tests for PartsRequest service layer."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.parts_request.exceptions import PartsRequestNotFoundError, PartsRequestValidationError
from app.domains.parts_request.service import PartsRequestService


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
    return PartsRequestService(repository=mock_repo)


class TestPartsRequestServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(PartsRequestValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(PartsRequestValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestPartsRequestServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PartsRequestNotFoundError):
            await service.get(tenant_id=uuid4(), entity_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(tenant_id=uuid4(), entity_id=uuid4())
        assert result is not None


class TestPartsRequestServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestPartsRequestServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestPartsRequestServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestPartsRequestDomainMethods:
    @pytest.mark.asyncio
    async def test_approve_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PartsRequestNotFoundError):
            await service.approve(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_approve_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.approve(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_fulfill_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PartsRequestNotFoundError):
            await service.fulfill(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_fulfill_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.fulfill(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_reject_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(PartsRequestNotFoundError):
            await service.reject(entity_id=uuid4(), tenant_id=uuid4(), reason="sample")

    @pytest.mark.asyncio
    async def test_reject_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.reject(entity_id=entity.id, tenant_id=uuid4(), reason="sample")
        assert result is not None
