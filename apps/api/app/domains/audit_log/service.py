"""Business logic for AuditLog."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.audit_log.exceptions import (
    AuditLogNotFoundError,
    AuditLogValidationError,
)
from app.domains.audit_log.models import AuditLog
from app.domains.audit_log.repository import AuditLogRepository
from app.domains.audit_log.schemas import AuditLogCreate, AuditLogRead, AuditLogUpdate

logger = structlog.get_logger(__name__)


class AuditLogService:
    """Orchestrates audit_log use cases with validation, transitions, and auditing."""

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: AuditLog, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("audit_log.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> AuditLog:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("audit_log.not_found", entity_id=str(entity_id))
            raise AuditLogNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise AuditLogValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> AuditLogRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("audit_log.service.get", entity_id=str(entity_id))
        return AuditLogRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[AuditLogRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise AuditLogValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise AuditLogValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "audit_log.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [AuditLogRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: AuditLogCreate, *, tenant_id: UUID | None = None
    ) -> AuditLogRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("audit_log.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return AuditLogRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: AuditLogUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> AuditLogRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("audit_log.service.update", entity_id=str(entity_id))
        return AuditLogRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("audit_log.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> AuditLogRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise AuditLogNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("audit_log.service.restore", entity_id=str(entity_id))
        return AuditLogRead.model_validate(restored)

    def _validate_create(self, data: AuditLogCreate) -> None:
        """Domain-specific create validation for AuditLog."""
        raw = getattr(data, "action", None)
        if raw is not None and not str(raw).strip():
            raise AuditLogValidationError("action is required and cannot be blank")

        raw = getattr(data, "resource_type", None)
        if raw is not None and not str(raw).strip():
            raise AuditLogValidationError("resource_type is required and cannot be blank")

    def _validate_update(self, entity: AuditLog, data: AuditLogUpdate) -> None:
        """Domain-specific update validation for AuditLog."""
        logger.debug("audit_log.validate_update", entity_id=str(entity.id))

    async def search_by_resource(self, entity_id: UUID, tenant_id: UUID | None, resource_type: str, resource_id: UUID) -> list:
        """Find audit entries for resource"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("audit_log.search_by_resource.start", entity_id=str(entity.id))
        # Find audit entries for resource
        logger.info("audit_log.search_by_resource.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
