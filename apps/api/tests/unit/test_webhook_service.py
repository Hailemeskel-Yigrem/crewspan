"""Unit tests for Webhook service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domains.webhook.exceptions import WebhookNotFoundError, WebhookValidationError
from app.domains.webhook.service import WebhookService


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    entity = MagicMock()
    entity.id = uuid4()
    entity.tenant_id = uuid4()
    entity.name = "sample-name"
    entity.url = "sample-url"
    entity.secret = "sample-secret"
    entity.event_types = []
    entity.is_active = True
    entity.failure_count = 1
    entity.last_triggered_at = datetime.now(UTC)
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
    return WebhookService(repository=mock_repo)


class TestWebhookServiceList:
    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, service, mock_repo):
        items, total = await service.list(tenant_id=uuid4(), page=1, page_size=10)
        assert total == 1
        assert len(items) == 1
        mock_repo.list.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_rejects_invalid_page(self, service):
        with pytest.raises(WebhookValidationError):
            await service.list(tenant_id=uuid4(), page=0, page_size=10)



class TestWebhookServiceGet:
    @pytest.mark.asyncio
    async def test_get_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WebhookNotFoundError):
            await service.get(uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_returns_read_model(self, service):
        result = await service.get(uuid4(), tenant_id=uuid4())
        assert result is not None


class TestWebhookServiceCount:
    @pytest.mark.asyncio
    async def test_count_delegates(self, service, mock_repo):
        total = await service.count(tenant_id=uuid4())
        assert total == 1
        mock_repo.count.assert_awaited_once()


class TestWebhookServiceExists:
    @pytest.mark.asyncio
    async def test_exists_true(self, service):
        assert await service.exists(uuid4(), tenant_id=uuid4()) is True


class TestWebhookServiceDelete:
    @pytest.mark.asyncio
    async def test_delete_soft_deletes(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        await service.delete(entity.id, tenant_id=uuid4())
        mock_repo.soft_delete.assert_awaited_once()


class TestWebhookDomainMethods:
    @pytest.mark.asyncio
    async def test_trigger_test_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WebhookNotFoundError):
            await service.trigger_test(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_trigger_test_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.trigger_test(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_rotate_secret_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WebhookNotFoundError):
            await service.rotate_secret(entity_id=uuid4(), tenant_id=uuid4())

    @pytest.mark.asyncio
    async def test_rotate_secret_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.rotate_secret(entity_id=entity.id, tenant_id=uuid4())
        assert result is not None

    @pytest.mark.asyncio
    async def test_disable_on_failures_raises_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(WebhookNotFoundError):
            await service.disable_on_failures(entity_id=uuid4(), tenant_id=uuid4(), threshold=1)

    @pytest.mark.asyncio
    async def test_disable_on_failures_with_entity(self, service, mock_repo):
        entity = mock_repo.get_by_id.return_value
        result = await service.disable_on_failures(entity_id=entity.id, tenant_id=uuid4(), threshold=1)
        assert result is not None
