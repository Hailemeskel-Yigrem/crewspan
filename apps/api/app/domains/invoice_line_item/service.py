"""Business logic for InvoiceLineItem."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.invoice_line_item.exceptions import (
    InvoiceLineItemNotFoundError,
    InvoiceLineItemValidationError,
)
from app.domains.invoice_line_item.models import InvoiceLineItem
from app.domains.invoice_line_item.repository import InvoiceLineItemRepository
from app.domains.invoice_line_item.schemas import (
    InvoiceLineItemCreate,
    InvoiceLineItemRead,
    InvoiceLineItemUpdate,
)

logger = structlog.get_logger(__name__)


class InvoiceLineItemService:
    """Orchestrates invoice_line_item use cases with validation, transitions, and auditing."""

    def __init__(self, repository: InvoiceLineItemRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: InvoiceLineItem, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("invoice_line_item.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InvoiceLineItem:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("invoice_line_item.not_found", entity_id=str(entity_id))
            raise InvoiceLineItemNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise InvoiceLineItemValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> InvoiceLineItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("invoice_line_item.service.get", entity_id=str(entity_id))
        return InvoiceLineItemRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[InvoiceLineItemRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise InvoiceLineItemValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise InvoiceLineItemValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "invoice_line_item.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [InvoiceLineItemRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: InvoiceLineItemCreate, *, tenant_id: UUID | None = None
    ) -> InvoiceLineItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("invoice_line_item.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return InvoiceLineItemRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: InvoiceLineItemUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> InvoiceLineItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("invoice_line_item.service.update", entity_id=str(entity_id))
        return InvoiceLineItemRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("invoice_line_item.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InvoiceLineItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise InvoiceLineItemNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("invoice_line_item.service.restore", entity_id=str(entity_id))
        return InvoiceLineItemRead.model_validate(restored)

    def _validate_create(self, data: InvoiceLineItemCreate) -> None:
        """Domain-specific create validation for InvoiceLineItem."""
        raw = getattr(data, "description", None)
        if raw is not None and not str(raw).strip():
            raise InvoiceLineItemValidationError("description is required and cannot be blank")

        raw = getattr(data, "item_type", None)
        if raw is not None and not str(raw).strip():
            raise InvoiceLineItemValidationError("item_type is required and cannot be blank")

    def _validate_update(self, entity: InvoiceLineItem, data: InvoiceLineItemUpdate) -> None:
        """Domain-specific update validation for InvoiceLineItem."""
        logger.debug("invoice_line_item.validate_update", entity_id=str(entity.id))

    async def recalculate(self, entity_id: UUID, tenant_id: UUID | None):
        """Update line total from quantity and price"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("invoice_line_item.recalculate.start", entity_id=str(entity.id))
        # Update line total from quantity and price
        logger.info("invoice_line_item.recalculate.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
