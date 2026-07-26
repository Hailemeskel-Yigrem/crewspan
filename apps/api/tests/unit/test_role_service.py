"""Unit tests for Role service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.role.exceptions import RoleNotFoundError, RoleValidationError
from app.domains.role.service import RoleService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.name = "sample-name"
    entity.description = "sample-description"
    entity.permissions = "sample-permissions"
    entity.is_system = True
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
    return RoleService(repository=mock_repo)


class TestRoleServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(RoleValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestRoleServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(RoleNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestRoleServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestRoleServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestRoleServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestRoleDomainMethods:
    @pytest.mark.asyncio
    async def test_grant_permission_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(RoleNotFoundError):
            await service.grant_permission(entity_id=uuid4(), tenant_id=uuid4(), permission="sample")

    @pytest.mark.asyncio
    async def test_grant_permission_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.grant_permission(entity_id=entity.id, tenant_id=uuid4(), permission="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_revoke_permission_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(RoleNotFoundError):
            await service.revoke_permission(entity_id=uuid4(), tenant_id=uuid4(), permission="sample")

    @pytest.mark.asyncio
    async def test_revoke_permission_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.revoke_permission(entity_id=entity.id, tenant_id=uuid4(), permission="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_clone_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(RoleNotFoundError):
            await service.clone(entity_id=uuid4(), tenant_id=uuid4(), new_name="sample")

    @pytest.mark.asyncio
    async def test_clone_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.clone(entity_id=entity.id, tenant_id=uuid4(), new_name="sample")
        assert result is not None
