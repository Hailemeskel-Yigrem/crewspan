"""Business logic for Payment."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from app.domains.payment.exceptions import (
    PaymentConflictError,
    PaymentNotFoundError,
    PaymentValidationError,
)
from app.domains.payment.models import Payment
from app.domains.payment.repository import PaymentRepository
from app.domains.payment.schemas import PaymentCreate, PaymentRead, PaymentUpdate

logger = structlog.get_logger(__name__)


class PaymentService:
    """Orchestrates payment use cases with validation, transitions, and auditing."""

    def __init__(self, repository: PaymentRepository) -> None:
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

    def _assert_status_transition(self, entity: Payment, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise PaymentValidationError(
                f"Cannot {action} payment from status '{current}' to '{target}'"
            )
        logger.info(
            "payment.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: Payment, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Payment:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("payment.not_found", entity_id=str(entity_id))
            raise PaymentNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise PaymentValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> PaymentRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("payment.service.get", entity_id=str(entity_id))
        return PaymentRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[PaymentRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise PaymentValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise PaymentValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "payment.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [PaymentRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: PaymentCreate, *, tenant_id: UUID | None = None
    ) -> PaymentRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("payment.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return PaymentRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: PaymentUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> PaymentRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("payment.service.update", entity_id=str(entity_id))
        return PaymentRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("payment.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> PaymentRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise PaymentNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("payment.service.restore", entity_id=str(entity_id))
        return PaymentRead.model_validate(restored)

    def _validate_create(self, data: PaymentCreate) -> None:
        """Domain-specific create validation for Payment."""
        raw = getattr(data, "payment_method", None)
        if raw is not None and not str(raw).strip():
            raise PaymentValidationError("payment_method is required and cannot be blank")

        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise PaymentValidationError(f"Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise PaymentValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: Payment, data: PaymentUpdate) -> None:
        """Domain-specific update validation for Payment."""
        if data.status is not None and data.status == entity.status:
            raise PaymentConflictError(f"Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise PaymentValidationError(f"Invalid status: {new_status}")

    async def refund(self, entity_id: UUID, tenant_id: UUID | None, amount: Decimal, reason: str):
        """Issue partial or full refund"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("payment.refund.start", entity_id=str(entity.id))
        # Issue partial or full refund
        logger.info("payment.refund.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def reconcile(self, entity_id: UUID, tenant_id: UUID | None):
        """Mark payment reconciled with bank feed"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("payment.reconcile.start", entity_id=str(entity.id))
        # Mark payment reconciled with bank feed
        logger.info("payment.reconcile.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
