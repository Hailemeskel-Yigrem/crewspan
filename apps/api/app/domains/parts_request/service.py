"""Business logic for PartsRequest."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.parts_request.exceptions import (
    PartsRequestConflictError,
    PartsRequestNotFoundError,
    PartsRequestValidationError,
)
from app.domains.parts_request.models import PartsRequest
from app.domains.parts_request.repository import PartsRequestRepository
from app.domains.parts_request.schemas import PartsRequestCreate, PartsRequestRead, PartsRequestUpdate

logger = structlog.get_logger(__name__)


class PartsRequestService:
    """Orchestrates parts_request use cases with validation, transitions, and auditing."""

    def __init__(self, repository: PartsRequestRepository) -> None:
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

    def _assert_status_transition(self, entity: PartsRequest, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise PartsRequestValidationError(
                f"Cannot {action} parts_request from status '{current}' to '{target}'"
            )
        logger.info(
            "parts_request.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: PartsRequest, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> PartsRequest:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("parts_request.not_found", entity_id=str(entity_id))
            raise PartsRequestNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise PartsRequestValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> PartsRequestRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("parts_request.service.get", entity_id=str(entity_id))
        return PartsRequestRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[PartsRequestRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise PartsRequestValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise PartsRequestValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "parts_request.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [PartsRequestRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: PartsRequestCreate, *, tenant_id: UUID | None = None
    ) -> PartsRequestRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("parts_request.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return PartsRequestRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: PartsRequestUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> PartsRequestRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("parts_request.service.update", entity_id=str(entity_id))
        return PartsRequestRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("parts_request.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> PartsRequestRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise PartsRequestNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("parts_request.service.restore", entity_id=str(entity_id))
        return PartsRequestRead.model_validate(restored)

    def _validate_create(self, data: PartsRequestCreate) -> None:
        """Domain-specific create validation for PartsRequest."""
        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise PartsRequestValidationError("Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise PartsRequestValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: PartsRequest, data: PartsRequestUpdate) -> None:
        """Domain-specific update validation for PartsRequest."""
        if data.status is not None and data.status == entity.status:
            raise PartsRequestConflictError("Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise PartsRequestValidationError("Invalid status: {new_status}")

    async def approve(self, entity_id: UUID, tenant_id: UUID | None):
        """Approve parts request"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._set_status(entity, "approved", action="approve")
        logger.info("parts_request.approve", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def fulfill(self, entity_id: UUID, tenant_id: UUID | None):
        """Issue parts and update inventory"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status != "approved":
            raise PartsRequestValidationError("Only approved requests may be fulfilled")
        entity.status = "fulfilled"
        logger.info("parts_request.fulfill", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def reject(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """Reject with reason"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status not in {"pending", "approved"}:
            raise PartsRequestValidationError("Request cannot be rejected in current state")
        entity.status = "rejected"
        logger.info("parts_request.reject", entity_id=str(entity.id), reason=reason)
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
# history-note: evolutionary edit 54
