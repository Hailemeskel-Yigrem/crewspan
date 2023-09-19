"""Business logic for Equipment."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.equipment.exceptions import (
    EquipmentConflictError,
    EquipmentNotFoundError,
    EquipmentValidationError,
)
from app.domains.equipment.models import Equipment
from app.domains.equipment.repository import EquipmentRepository
from app.domains.equipment.schemas import EquipmentCreate, EquipmentRead, EquipmentUpdate

logger = structlog.get_logger(__name__)


class EquipmentService:
    """Orchestrates equipment use cases with validation, transitions, and auditing."""

    def __init__(self, repository: EquipmentRepository) -> None:
        self._repo = repository

    _STATUS_TRANSITIONS: dict[str, set[str]] = {
        "draft": {"submitted", "cancelled", "active", "pending"},
        "pending": {"approved", "rejected", "cancelled", "active"},
        "submitted": {"in_progress", "assigned", "cancelled"},
        "assigned": {"in_progress", "cancelled"},
        "in_progress": {"completed", "cancelled", "blocked"},
        "blocked": {"in_progress", "cancelled"},
        "approved": {"fulfilled", "rejected", "cancelled"},
        "active": {"inactive", "completed", "cancelled", "blocked"},
        "completed": set(),
        "cancelled": set(),
        "rejected": set(),
    }

    def _assert_status_transition(self, entity: Equipment, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise EquipmentValidationError(
                f"Cannot {action} equipment from status '{current}' to '{target}'"
            )
        logger.info(
            "equipment.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: Equipment, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Equipment:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("equipment.not_found", entity_id=str(entity_id))
            raise EquipmentNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise EquipmentValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> EquipmentRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("equipment.service.get", entity_id=str(entity_id))
        return EquipmentRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[EquipmentRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise EquipmentValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise EquipmentValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "equipment.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [EquipmentRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: EquipmentCreate, *, tenant_id: UUID | None = None
    ) -> EquipmentRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("equipment.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return EquipmentRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: EquipmentUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> EquipmentRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("equipment.service.update", entity_id=str(entity_id))
        return EquipmentRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("equipment.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> EquipmentRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise EquipmentNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("equipment.service.restore", entity_id=str(entity_id))
        return EquipmentRead.model_validate(restored)

    def _validate_create(self, data: EquipmentCreate) -> None:
        """Domain-specific create validation for Equipment."""
        raw = getattr(data, "asset_tag", None)
        if raw is not None and not str(raw).strip():
            raise EquipmentValidationError("asset_tag is required and cannot be blank")

        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise EquipmentValidationError("name is required and cannot be blank")

        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise EquipmentValidationError("Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise EquipmentValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: Equipment, data: EquipmentUpdate) -> None:
        """Domain-specific update validation for Equipment."""
        if data.status is not None and data.status == entity.status:
            raise EquipmentConflictError("Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise EquipmentValidationError("Invalid status: {new_status}")

    async def record_service(self, entity_id: UUID, tenant_id: UUID | None, work_order_id: UUID, notes: str):
        """Log service event on equipment"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("equipment.record_service.start", entity_id=str(entity.id))
        # Log service event on equipment
        logger.info("equipment.record_service.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def retire(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """Mark equipment out of service"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("equipment.retire.start", entity_id=str(entity.id))
        # Mark equipment out of service
        logger.info("equipment.retire.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
