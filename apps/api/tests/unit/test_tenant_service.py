"""Unit tests for Tenant service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.tenant.exceptions import TenantNotFoundError, TenantValidationError
from app.domains.tenant.service import TenantService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.slug = "sample-slug"
    entity.display_name = "sample-display_name"
    entity.legal_name = "sample-legal_name"
    entity.subscription_tier = "sample-subscription_tier"
    entity.timezone = "sample-timezone"
    entity.is_active = True
    entity.feature_flags = {}
    entity.settings = {}
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
    return TenantService(repository=mock_repo)


class TestTenantServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(TenantValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestTenantServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TenantNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestTenantServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestTenantServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestTenantServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestTenantDomainMethods:
    @pytest.mark.asyncio
    async def test_activate_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TenantNotFoundError):
            await service.activate(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_activate_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        entity.is_active = False
        result = await service.activate(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_deactivate_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TenantNotFoundError):
            await service.deactivate(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_deactivate_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.deactivate(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_update_settings_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(TenantNotFoundError):
            await service.update_settings(entity_id=uuid4(), tenant_id=uuid4(), settings=None)

    @pytest.mark.asyncio
    async def test_update_settings_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.update_settings(entity_id=entity.id, tenant_id=uuid4(), settings=None)
        assert result is not None
