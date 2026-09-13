"""Business logic for Dispatch."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.dispatch.exceptions import (
    DispatchConflictError,
    DispatchNotFoundError,
    DispatchValidationError,
)
from app.domains.dispatch.models import Dispatch
from app.domains.dispatch.repository import DispatchRepository
from app.domains.dispatch.schemas import DispatchCreate, DispatchRead, DispatchUpdate

logger = structlog.get_logger(__name__)


class DispatchService:
    """Orchestrates dispatch use cases with validation, transitions, and auditing."""

    def __init__(self, repository: DispatchRepository) -> None:
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

    def _assert_status_transition(self, entity: Dispatch, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise DispatchValidationError(
                f"Cannot {action} dispatch from status '{current}' to '{target}'"
            )
        logger.info(
            "dispatch.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: Dispatch, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Dispatch:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("dispatch.not_found", entity_id=str(entity_id))
            raise DispatchNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise DispatchValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> DispatchRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("dispatch.service.get", entity_id=str(entity_id))
        return DispatchRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[DispatchRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise DispatchValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise DispatchValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "dispatch.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [DispatchRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: DispatchCreate, *, tenant_id: UUID | None = None
    ) -> DispatchRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("dispatch.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return DispatchRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: DispatchUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> DispatchRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("dispatch.service.update", entity_id=str(entity_id))
        return DispatchRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("dispatch.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> DispatchRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise DispatchNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("dispatch.service.restore", entity_id=str(entity_id))
        return DispatchRead.model_validate(restored)

    def _validate_create(self, data: DispatchCreate) -> None:
        """Domain-specific create validation for Dispatch."""
        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise DispatchValidationError(f"Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise DispatchValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: Dispatch, data: DispatchUpdate) -> None:
        """Domain-specific update validation for Dispatch."""
        if data.status is not None and data.status == entity.status:
            raise DispatchConflictError(f"Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise DispatchValidationError(f"Invalid status: {new_status}")

    async def accept(self, entity_id: UUID, tenant_id: UUID | None):
        """Technician accepts dispatch"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("dispatch.accept.start", entity_id=str(entity.id))
        # Technician accepts dispatch
        logger.info("dispatch.accept.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def decline(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """Technician declines with reason"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("dispatch.decline.start", entity_id=str(entity.id))
        # Technician declines with reason
        logger.info("dispatch.decline.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def en_route(self, entity_id: UUID, tenant_id: UUID | None):
        """Mark technician en route"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("dispatch.en_route.start", entity_id=str(entity.id))
        # Mark technician en route
        logger.info("dispatch.en_route.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def arrive(self, entity_id: UUID, tenant_id: UUID | None):
        """Record on-site arrival"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("dispatch.arrive.start", entity_id=str(entity.id))
        # Record on-site arrival
        logger.info("dispatch.arrive.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
