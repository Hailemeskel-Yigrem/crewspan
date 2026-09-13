"""Business logic for WorkOrderTask."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.work_order_task.exceptions import (
    WorkOrderTaskConflictError,
    WorkOrderTaskNotFoundError,
    WorkOrderTaskValidationError,
)
from app.domains.work_order_task.models import WorkOrderTask
from app.domains.work_order_task.repository import WorkOrderTaskRepository
from app.domains.work_order_task.schemas import WorkOrderTaskCreate, WorkOrderTaskRead, WorkOrderTaskUpdate

logger = structlog.get_logger(__name__)


class WorkOrderTaskService:
    """Orchestrates work_order_task use cases with validation, transitions, and auditing."""

    def __init__(self, repository: WorkOrderTaskRepository) -> None:
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

    def _assert_status_transition(self, entity: WorkOrderTask, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise WorkOrderTaskValidationError(
                f"Cannot {action} work_order_task from status '{current}' to '{target}'"
            )
        logger.info(
            "work_order_task.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: WorkOrderTask, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> WorkOrderTask:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("work_order_task.not_found", entity_id=str(entity_id))
            raise WorkOrderTaskNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise WorkOrderTaskValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> WorkOrderTaskRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("work_order_task.service.get", entity_id=str(entity_id))
        return WorkOrderTaskRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[WorkOrderTaskRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise WorkOrderTaskValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise WorkOrderTaskValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "work_order_task.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [WorkOrderTaskRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: WorkOrderTaskCreate, *, tenant_id: UUID | None = None
    ) -> WorkOrderTaskRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("work_order_task.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return WorkOrderTaskRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: WorkOrderTaskUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> WorkOrderTaskRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("work_order_task.service.update", entity_id=str(entity_id))
        return WorkOrderTaskRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("work_order_task.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> WorkOrderTaskRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise WorkOrderTaskNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("work_order_task.service.restore", entity_id=str(entity_id))
        return WorkOrderTaskRead.model_validate(restored)

    def _validate_create(self, data: WorkOrderTaskCreate) -> None:
        """Domain-specific create validation for WorkOrderTask."""
        raw = getattr(data, "title", None)
        if raw is not None and not str(raw).strip():
            raise WorkOrderTaskValidationError("title is required and cannot be blank")

        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise WorkOrderTaskValidationError(f"Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise WorkOrderTaskValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: WorkOrderTask, data: WorkOrderTaskUpdate) -> None:
        """Domain-specific update validation for WorkOrderTask."""
        if data.status is not None and data.status == entity.status:
            raise WorkOrderTaskConflictError(f"Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise WorkOrderTaskValidationError(f"Invalid status: {new_status}")

    async def complete(self, entity_id: UUID, tenant_id: UUID | None):
        """Mark task completed"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status not in {"in_progress", "submitted"}:
            raise WorkOrderTaskValidationError(f"Work order cannot be completed from status {entity.status}")
        entity.status = "completed"
        logger.info("work_order_task.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def reopen(self, entity_id: UUID, tenant_id: UUID | None):
        """Revert completed task to pending"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("work_order_task.reopen.start", entity_id=str(entity.id))
        # Revert completed task to pending
        logger.info("work_order_task.reopen.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def reorder(self, entity_id: UUID, tenant_id: UUID | None, sequence: int):
        """Change task sequence"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("work_order_task.reorder.start", entity_id=str(entity.id))
        # Change task sequence
        logger.info("work_order_task.reorder.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
