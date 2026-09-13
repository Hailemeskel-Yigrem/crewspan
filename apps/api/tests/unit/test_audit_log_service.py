"""Unit tests for AuditLog service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.audit_log.exceptions import AuditLogNotFoundError, AuditLogValidationError
from app.domains.audit_log.service import AuditLogService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.actor_id = uuid4()
    entity.action = "sample-action"
    entity.resource_type = "sample-resource_type"
    entity.resource_id = uuid4()
    entity.changes = {}
    entity.ip_address = "sample-ip_address"
    entity.user_agent = "sample-user_agent"
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
    return AuditLogService(repository=mock_repo)


class TestAuditLogServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(AuditLogValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestAuditLogServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(AuditLogNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestAuditLogServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestAuditLogServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestAuditLogServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestAuditLogDomainMethods:
    @pytest.mark.asyncio
    async def test_search_by_resource_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(AuditLogNotFoundError):
            await service.search_by_resource(entity_id=uuid4(), tenant_id=uuid4(), resource_type="sample", resource_id=uuid4())

    @pytest.mark.asyncio
    async def test_search_by_resource_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.search_by_resource(entity_id=entity.id, tenant_id=uuid4(), resource_type="sample", resource_id=uuid4())
        assert result is not None
