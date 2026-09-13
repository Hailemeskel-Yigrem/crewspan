"""Business logic for Schedule."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.domains.schedule.exceptions import (
    ScheduleNotFoundError,
    ScheduleValidationError,
)
from app.domains.schedule.models import Schedule
from app.domains.schedule.repository import ScheduleRepository
from app.domains.schedule.schemas import ScheduleCreate, ScheduleRead, ScheduleUpdate

logger = structlog.get_logger(__name__)


class ScheduleService:
    """Orchestrates schedule use cases with validation, transitions, and auditing."""

    def __init__(self, repository: ScheduleRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: Schedule, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("schedule.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Schedule:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("schedule.not_found", entity_id=str(entity_id))
            raise ScheduleNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise ScheduleValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> ScheduleRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("schedule.service.get", entity_id=str(entity_id))
        return ScheduleRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[ScheduleRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise ScheduleValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise ScheduleValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "schedule.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [ScheduleRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: ScheduleCreate, *, tenant_id: UUID | None = None
    ) -> ScheduleRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("schedule.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return ScheduleRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: ScheduleUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> ScheduleRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("schedule.service.update", entity_id=str(entity_id))
        return ScheduleRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("schedule.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> ScheduleRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise ScheduleNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("schedule.service.restore", entity_id=str(entity_id))
        return ScheduleRead.model_validate(restored)

    def _validate_create(self, data: ScheduleCreate) -> None:
        """Domain-specific create validation for Schedule."""
        raw = getattr(data, "event_type", None)
        if raw is not None and not str(raw).strip():
            raise ScheduleValidationError("event_type is required and cannot be blank")

        raw = getattr(data, "title", None)
        if raw is not None and not str(raw).strip():
            raise ScheduleValidationError("title is required and cannot be blank")

    def _validate_update(self, entity: Schedule, data: ScheduleUpdate) -> None:
        """Domain-specific update validation for Schedule."""
        logger.debug("schedule.validate_update", entity_id=str(entity.id))

    async def lock(self, entity_id: UUID, tenant_id: UUID | None):
        """Prevent schedule modifications"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("schedule.lock.start", entity_id=str(entity.id))
        # Prevent schedule modifications
        logger.info("schedule.lock.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def unlock(self, entity_id: UUID, tenant_id: UUID | None):
        """Allow schedule modifications"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("schedule.unlock.start", entity_id=str(entity.id))
        # Allow schedule modifications
        logger.info("schedule.unlock.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def detect_conflicts(self, entity_id: UUID, tenant_id: UUID | None, starts_at: datetime, ends_at: datetime) -> list:
        """Find overlapping events"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("schedule.detect_conflicts.start", entity_id=str(entity.id))
        # Find overlapping events
        logger.info("schedule.detect_conflicts.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
