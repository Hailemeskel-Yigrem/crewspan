"""Business logic for WorkOrder."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.work_order.exceptions import (
    WorkOrderConflictError,
    WorkOrderNotFoundError,
    WorkOrderValidationError,
)
from app.domains.work_order.models import WorkOrder
from app.domains.work_order.repository import WorkOrderRepository
from app.domains.work_order.schemas import WorkOrderCreate, WorkOrderRead, WorkOrderUpdate

logger = structlog.get_logger(__name__)


class WorkOrderService:
    """Orchestrates work_order use cases with validation, transitions, and auditing."""

    def __init__(self, repository: WorkOrderRepository) -> None:
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

    def _assert_status_transition(self, entity: WorkOrder, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise WorkOrderValidationError(
                f"Cannot {action} work_order from status '{current}' to '{target}'"
            )
        logger.info(
            "work_order.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: WorkOrder, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> WorkOrder:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("work_order.not_found", entity_id=str(entity_id))
            raise WorkOrderNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise WorkOrderValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> WorkOrderRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("work_order.service.get", entity_id=str(entity_id))
        return WorkOrderRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[WorkOrderRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise WorkOrderValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise WorkOrderValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "work_order.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [WorkOrderRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: WorkOrderCreate, *, tenant_id: UUID | None = None
    ) -> WorkOrderRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("work_order.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return WorkOrderRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: WorkOrderUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> WorkOrderRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("work_order.service.update", entity_id=str(entity_id))
        return WorkOrderRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("work_order.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> WorkOrderRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise WorkOrderNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("work_order.service.restore", entity_id=str(entity_id))
        return WorkOrderRead.model_validate(restored)

    def _validate_create(self, data: WorkOrderCreate) -> None:
        """Domain-specific create validation for WorkOrder."""
        raw = getattr(data, "order_number", None)
        if raw is not None and not str(raw).strip():
            raise WorkOrderValidationError("order_number is required and cannot be blank")

        raw = getattr(data, "title", None)
        if raw is not None and not str(raw).strip():
            raise WorkOrderValidationError("title is required and cannot be blank")

        if hasattr(data, "priority") and getattr(data, "priority") is not None:
            if getattr(data, "priority") not in {'low', 'normal', 'high', 'critical'}:
                raise WorkOrderValidationError(f"Invalid priority: {getattr(data, 'priority')}")

        raw = getattr(data, "priority", None)
        if raw is not None and not str(raw).strip():
            raise WorkOrderValidationError("priority is required and cannot be blank")

        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise WorkOrderValidationError(f"Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise WorkOrderValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: WorkOrder, data: WorkOrderUpdate) -> None:
        """Domain-specific update validation for WorkOrder."""
        if data.status is not None and data.status == entity.status:
            raise WorkOrderConflictError(f"Status is already {entity.status}")

        new_priority = getattr(data, "priority", None)
        if new_priority is not None and new_priority not in {'low', 'normal', 'high', 'critical'}:
            raise WorkOrderValidationError(f"Invalid priority: {new_priority}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise WorkOrderValidationError(f"Invalid status: {new_status}")

        start = data.scheduled_start if data.scheduled_start is not None else entity.scheduled_start
        end = data.scheduled_end if data.scheduled_end is not None else entity.scheduled_end
        if start is not None and end is not None and end < start:
            raise WorkOrderValidationError("scheduled_end must be on or after scheduled_start")

    async def submit(self, entity_id: UUID, tenant_id: UUID | None):
        """Transition draft work order to submitted queue"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status != "draft":
            raise WorkOrderValidationError("Only draft work orders may be submitted")
        entity.status = "submitted"
        logger.info("work_order.submit", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def assign_technician(self, entity_id: UUID, tenant_id: UUID | None, technician_id: UUID):
        """Assign technician with conflict check"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._set_status(entity, "assigned", action="assign_technician")
        entity.assigned_technician_id = technician_id
        logger.info("work_order.assign_technician", entity_id=str(entity.id), technician_id=str(technician_id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def start(self, entity_id: UUID, tenant_id: UUID | None):
        """Mark work order in progress"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._set_status(entity, "in_progress", action="start")
        logger.info("work_order.start", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def complete(self, entity_id: UUID, tenant_id: UUID | None, notes: str | None):
        """Complete work order with notes"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status not in {"in_progress", "submitted"}:
            raise WorkOrderValidationError(f"Work order cannot be completed from status {entity.status}")
        entity.status = "completed"
        if notes:
            entity.completion_notes = notes
        logger.info("work_order.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def cancel(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """Cancel with reason"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status == "completed":
            raise WorkOrderConflictError("Completed work orders cannot be cancelled")
        entity.status = "cancelled"
        logger.info("work_order.cancel", entity_id=str(entity.id), reason=reason)
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
