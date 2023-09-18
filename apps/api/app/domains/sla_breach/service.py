"""Business logic for SlaBreach."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.sla_breach.exceptions import (
    SlaBreachConflictError,
    SlaBreachNotFoundError,
    SlaBreachValidationError,
)
from app.domains.sla_breach.models import SlaBreach
from app.domains.sla_breach.repository import SlaBreachRepository
from app.domains.sla_breach.schemas import SlaBreachCreate, SlaBreachRead, SlaBreachUpdate

logger = structlog.get_logger(__name__)


class SlaBreachService:
    """Orchestrates sla_breach use cases with validation, transitions, and auditing."""

    def __init__(self, repository: SlaBreachRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: SlaBreach, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("sla_breach.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> SlaBreach:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("sla_breach.not_found", entity_id=str(entity_id))
            raise SlaBreachNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise SlaBreachValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> SlaBreachRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("sla_breach.service.get", entity_id=str(entity_id))
        return SlaBreachRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[SlaBreachRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise SlaBreachValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise SlaBreachValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "sla_breach.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [SlaBreachRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: SlaBreachCreate, *, tenant_id: UUID | None = None
    ) -> SlaBreachRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("sla_breach.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return SlaBreachRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: SlaBreachUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> SlaBreachRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("sla_breach.service.update", entity_id=str(entity_id))
        return SlaBreachRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("sla_breach.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> SlaBreachRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise SlaBreachNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("sla_breach.service.restore", entity_id=str(entity_id))
        return SlaBreachRead.model_validate(restored)

    def _validate_create(self, data: SlaBreachCreate) -> None:
        """Domain-specific create validation for SlaBreach."""
        raw = getattr(data, "breach_type", None)
        if raw is not None and not str(raw).strip():
            raise SlaBreachValidationError("breach_type is required and cannot be blank")

    def _validate_update(self, entity: SlaBreach, data: SlaBreachUpdate) -> None:
        """Domain-specific update validation for SlaBreach."""
        logger.debug("sla_breach.validate_update", entity_id=str(entity.id))

    async def acknowledge(self, entity_id: UUID, tenant_id: UUID | None):
        """Mark breach reviewed"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        entity.acknowledged = True
        logger.info("sla_breach.acknowledge", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def escalate(self, entity_id: UUID, tenant_id: UUID | None):
        """Increment escalation level and notify"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        entity.escalation_level += 1
        logger.info("sla_breach.escalate", entity_id=str(entity.id), level=entity.escalation_level)
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
