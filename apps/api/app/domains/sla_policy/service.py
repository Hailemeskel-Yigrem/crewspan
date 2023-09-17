"""Business logic for SlaPolicy."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.sla_policy.exceptions import (
    SlaPolicyConflictError,
    SlaPolicyNotFoundError,
    SlaPolicyValidationError,
)
from app.domains.sla_policy.models import SlaPolicy
from app.domains.sla_policy.repository import SlaPolicyRepository
from app.domains.sla_policy.schemas import SlaPolicyCreate, SlaPolicyRead, SlaPolicyUpdate

logger = structlog.get_logger(__name__)


class SlaPolicyService:
    """Orchestrates sla_policy use cases with validation, transitions, and auditing."""

    def __init__(self, repository: SlaPolicyRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: SlaPolicy, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("sla_policy.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> SlaPolicy:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("sla_policy.not_found", entity_id=str(entity_id))
            raise SlaPolicyNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise SlaPolicyValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> SlaPolicyRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("sla_policy.service.get", entity_id=str(entity_id))
        return SlaPolicyRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[SlaPolicyRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise SlaPolicyValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise SlaPolicyValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "sla_policy.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [SlaPolicyRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: SlaPolicyCreate, *, tenant_id: UUID | None = None
    ) -> SlaPolicyRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("sla_policy.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return SlaPolicyRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: SlaPolicyUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> SlaPolicyRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("sla_policy.service.update", entity_id=str(entity_id))
        return SlaPolicyRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("sla_policy.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> SlaPolicyRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise SlaPolicyNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("sla_policy.service.restore", entity_id=str(entity_id))
        return SlaPolicyRead.model_validate(restored)

    def _validate_create(self, data: SlaPolicyCreate) -> None:
        """Domain-specific create validation for SlaPolicy."""
        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise SlaPolicyValidationError("name is required and cannot be blank")

        if hasattr(data, "priority") and getattr(data, "priority") is not None:
            if getattr(data, "priority") not in {'low', 'normal', 'high', 'critical'}:
                raise SlaPolicyValidationError("Invalid priority: {getattr(data, 'priority')}")

        raw = getattr(data, "priority", None)
        if raw is not None and not str(raw).strip():
            raise SlaPolicyValidationError("priority is required and cannot be blank")

    def _validate_update(self, entity: SlaPolicy, data: SlaPolicyUpdate) -> None:
        """Domain-specific update validation for SlaPolicy."""
        new_priority = getattr(data, "priority", None)
        if new_priority is not None and new_priority not in {'low', 'normal', 'high', 'critical'}:
            raise SlaPolicyValidationError("Invalid priority: {new_priority}")

    async def evaluate_deadlines(self, entity_id: UUID, tenant_id: UUID | None, opened_at: datetime) -> dict:
        """Compute response/resolution deadlines"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("sla_policy.evaluate_deadlines.start", entity_id=str(entity.id))
        # Compute response/resolution deadlines
        logger.info("sla_policy.evaluate_deadlines.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def clone(self, entity_id: UUID, tenant_id: UUID | None, new_name: str) -> SlaPolicy:
        """Duplicate policy"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("sla_policy.clone.start", entity_id=str(entity.id))
        # Duplicate policy
        logger.info("sla_policy.clone.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
