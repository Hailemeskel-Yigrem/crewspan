"""Unit tests for Notification service layer."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.notification.exceptions import NotificationNotFoundError, NotificationValidationError
from app.domains.notification.service import NotificationService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.recipient_id = uuid4()
    entity.recipient_email = "sample-recipient_email"
    entity.channel = "sample-channel"
    entity.template_key = "sample-template_key"
    entity.subject = "sample-subject"
    entity.body = "sample-body"
    entity.status = "draft"
    entity.sent_at = datetime.now(timezone.utc)
    entity.payload_meta = {}
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
    return NotificationService(repository=mock_repo)


class TestNotificationServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(NotificationValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)
    @pytest.mark.asyncio
    async def test_list_rejects_oversized_page(self, service):
        with pytest.raises(NotificationValidationError):
            await service.list(tenant_id=uuid4(), page=1, page_size=999)


class TestNotificationServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotificationNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestNotificationServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestNotificationServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestNotificationServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestNotificationDomainMethods:
    @pytest.mark.asyncio
    async def test_mark_sent_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotificationNotFoundError):
            await service.mark_sent(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_mark_sent_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.mark_sent(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_mark_failed_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotificationNotFoundError):
            await service.mark_failed(entity_id=uuid4(), tenant_id=uuid4(), error="sample")

    @pytest.mark.asyncio
    async def test_mark_failed_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.mark_failed(entity_id=entity.id, tenant_id=uuid4(), error="sample")
        assert result is not None

    @pytest.mark.asyncio
    async def test_retry_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(NotificationNotFoundError):
            await service.retry(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_retry_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        entity.status = "failed"
        result = await service.retry(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None
