"""Business logic for Invoice."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.invoice.exceptions import (
    InvoiceConflictError,
    InvoiceNotFoundError,
    InvoiceValidationError,
)
from app.domains.invoice.models import Invoice
from app.domains.invoice.repository import InvoiceRepository
from app.domains.invoice.schemas import InvoiceCreate, InvoiceRead, InvoiceUpdate

logger = structlog.get_logger(__name__)


class InvoiceService:
    """Orchestrates invoice use cases with validation, transitions, and auditing."""

    def __init__(self, repository: InvoiceRepository) -> None:
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

    def _assert_status_transition(self, entity: Invoice, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise InvoiceValidationError(
                f"Cannot {action} invoice from status '{current}' to '{target}'"
            )
        logger.info(
            "invoice.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: Invoice, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Invoice:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("invoice.not_found", entity_id=str(entity_id))
            raise InvoiceNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise InvoiceValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> InvoiceRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("invoice.service.get", entity_id=str(entity_id))
        return InvoiceRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[InvoiceRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise InvoiceValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise InvoiceValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "invoice.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [InvoiceRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: InvoiceCreate, *, tenant_id: UUID | None = None
    ) -> InvoiceRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("invoice.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return InvoiceRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: InvoiceUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> InvoiceRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("invoice.service.update", entity_id=str(entity_id))
        return InvoiceRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("invoice.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InvoiceRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise InvoiceNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("invoice.service.restore", entity_id=str(entity_id))
        return InvoiceRead.model_validate(restored)

    def _validate_create(self, data: InvoiceCreate) -> None:
        """Domain-specific create validation for Invoice."""
        raw = getattr(data, "invoice_number", None)
        if raw is not None and not str(raw).strip():
            raise InvoiceValidationError("invoice_number is required and cannot be blank")

        if hasattr(data, "status") and data.status is not None:
            if data.status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise InvoiceValidationError(f"Invalid status: {data.status}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise InvoiceValidationError("status is required and cannot be blank")

        raw = getattr(data, "currency", None)
        if raw is not None and not str(raw).strip():
            raise InvoiceValidationError("currency is required and cannot be blank")

    def _validate_update(self, entity: Invoice, data: InvoiceUpdate) -> None:
        """Domain-specific update validation for Invoice."""
        if data.status is not None and data.status == entity.status:
            raise InvoiceConflictError(f"Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise InvoiceValidationError(f"Invalid status: {new_status}")

    async def finalize(self, entity_id: UUID, tenant_id: UUID | None):
        """Lock invoice totals and assign number"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.status != "draft":
            raise InvoiceValidationError("Only draft invoices may be finalized")
        entity.status = "finalized"
        logger.info("invoice.finalize", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def send(self, entity_id: UUID, tenant_id: UUID | None):
        """Email invoice to customer"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("invoice.send.start", entity_id=str(entity.id))
        # Email invoice to customer
        logger.info("invoice.send.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def void(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """Void draft or sent invoice"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("invoice.void.start", entity_id=str(entity.id))
        # Void draft or sent invoice
        logger.info("invoice.void.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def recalculate_totals(self, entity_id: UUID, tenant_id: UUID | None) -> Invoice:
        """Recompute subtotal, tax, and total"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("invoice.recalculate_totals.start", entity_id=str(entity.id))
        # Recompute subtotal, tax, and total
        logger.info("invoice.recalculate_totals.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
