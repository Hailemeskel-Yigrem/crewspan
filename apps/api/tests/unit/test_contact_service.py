"""Unit tests for Contact service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.contact.exceptions import ContactNotFoundError, ContactValidationError
from app.domains.contact.service import ContactService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.customer_id = uuid4()
    entity.site_id = uuid4()
    entity.first_name = "sample-first_name"
    entity.last_name = "sample-last_name"
    entity.email = "ops@example.com"
    entity.phone = "sample-phone"
    entity.role_title = "sample-role_title"
    entity.is_primary = True
    entity.notify_on_dispatch = True
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
    return ContactService(repository=mock_repo)


class TestContactServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(ContactValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestContactServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ContactNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestContactServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestContactServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestContactServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestContactDomainMethods:
    @pytest.mark.asyncio
    async def test_set_primary_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ContactNotFoundError):
            await service.set_primary(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_set_primary_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.set_primary(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_opt_out_notifications_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(ContactNotFoundError):
            await service.opt_out_notifications(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_opt_out_notifications_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.opt_out_notifications(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
