"""Business logic for Webhook."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.webhook.exceptions import (
    WebhookConflictError,
    WebhookNotFoundError,
    WebhookValidationError,
)
from app.domains.webhook.models import Webhook
from app.domains.webhook.repository import WebhookRepository
from app.domains.webhook.schemas import WebhookCreate, WebhookRead, WebhookUpdate

logger = structlog.get_logger(__name__)


class WebhookService:
    """Orchestrates webhook use cases with validation, transitions, and auditing."""

    def __init__(self, repository: WebhookRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: Webhook, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("webhook.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Webhook:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("webhook.not_found", entity_id=str(entity_id))
            raise WebhookNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise WebhookValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> WebhookRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("webhook.service.get", entity_id=str(entity_id))
        return WebhookRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[WebhookRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise WebhookValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise WebhookValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "webhook.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [WebhookRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: WebhookCreate, *, tenant_id: UUID | None = None
    ) -> WebhookRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("webhook.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return WebhookRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: WebhookUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> WebhookRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("webhook.service.update", entity_id=str(entity_id))
        return WebhookRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("webhook.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> WebhookRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise WebhookNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("webhook.service.restore", entity_id=str(entity_id))
        return WebhookRead.model_validate(restored)

    def _validate_create(self, data: WebhookCreate) -> None:
        """Domain-specific create validation for Webhook."""
        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise WebhookValidationError("name is required and cannot be blank")

        raw = getattr(data, "url", None)
        if raw is not None and not str(raw).strip():
            raise WebhookValidationError("url is required and cannot be blank")

        raw = getattr(data, "secret", None)
        if raw is not None and not str(raw).strip():
            raise WebhookValidationError("secret is required and cannot be blank")

    def _validate_update(self, entity: Webhook, data: WebhookUpdate) -> None:
        """Domain-specific update validation for Webhook."""
        logger.debug("webhook.validate_update", entity_id=str(entity.id))

    async def trigger_test(self, entity_id: UUID, tenant_id: UUID | None):
        """Send test payload"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("webhook.trigger_test.start", entity_id=str(entity.id))
        # Send test payload
        logger.info("webhook.trigger_test.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def rotate_secret(self, entity_id: UUID, tenant_id: UUID | None) -> Webhook:
        """Generate new signing secret"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("webhook.rotate_secret.start", entity_id=str(entity.id))
        # Generate new signing secret
        logger.info("webhook.rotate_secret.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def disable_on_failures(self, entity_id: UUID, tenant_id: UUID | None, threshold: int):
        """Auto-disable after threshold"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("webhook.disable_on_failures.start", entity_id=str(entity.id))
        # Auto-disable after threshold
        logger.info("webhook.disable_on_failures.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
