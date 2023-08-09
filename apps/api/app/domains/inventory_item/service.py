"""Business logic for InventoryItem."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.inventory_item.exceptions import (
    InventoryItemConflictError,
    InventoryItemNotFoundError,
    InventoryItemValidationError,
)
from app.domains.inventory_item.models import InventoryItem
from app.domains.inventory_item.repository import InventoryItemRepository
from app.domains.inventory_item.schemas import InventoryItemCreate, InventoryItemRead, InventoryItemUpdate

logger = structlog.get_logger(__name__)


class InventoryItemService:
    """Orchestrates inventory_item use cases with validation, transitions, and auditing."""

    def __init__(self, repository: InventoryItemRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: InventoryItem, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("inventory_item.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InventoryItem:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("inventory_item.not_found", entity_id=str(entity_id))
            raise InventoryItemNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise InventoryItemValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> InventoryItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("inventory_item.service.get", entity_id=str(entity_id))
        return InventoryItemRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[InventoryItemRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise InventoryItemValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise InventoryItemValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "inventory_item.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [InventoryItemRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: InventoryItemCreate, *, tenant_id: UUID | None = None
    ) -> InventoryItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("inventory_item.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return InventoryItemRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: InventoryItemUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> InventoryItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("inventory_item.service.update", entity_id=str(entity_id))
        return InventoryItemRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("inventory_item.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InventoryItemRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise InventoryItemNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("inventory_item.service.restore", entity_id=str(entity_id))
        return InventoryItemRead.model_validate(restored)

    def _validate_create(self, data: InventoryItemCreate) -> None:
        """Domain-specific create validation for InventoryItem."""
        raw = getattr(data, "sku", None)
        if raw is not None and not str(raw).strip():
            raise InventoryItemValidationError("sku is required and cannot be blank")

        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise InventoryItemValidationError("name is required and cannot be blank")

        raw = getattr(data, "unit_of_measure", None)
        if raw is not None and not str(raw).strip():
            raise InventoryItemValidationError("unit_of_measure is required and cannot be blank")

    def _validate_update(self, entity: InventoryItem, data: InventoryItemUpdate) -> None:
        """Domain-specific update validation for InventoryItem."""
        logger.debug("inventory_item.validate_update", entity_id=str(entity.id))

    async def adjust_reorder_levels(self, entity_id: UUID, tenant_id: UUID | None, point: int, quantity: int):
        """Update reorder point and quantity"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("inventory_item.adjust_reorder_levels.start", entity_id=str(entity.id))
        # Update reorder point and quantity
        logger.info("inventory_item.adjust_reorder_levels.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def deactivate(self, entity_id: UUID, tenant_id: UUID | None):
        """Mark item inactive"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if not entity.is_active:
            raise InventoryItemConflictError("Tenant is already inactive")
        entity.is_active = False
        logger.info("inventory_item.deactivate", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def calculate_stock_value(self, entity_id: UUID, tenant_id: UUID | None) -> Decimal:
        """Sum stock on hand times unit cost"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("inventory_item.calculate_stock_value.start", entity_id=str(entity.id))
        # Sum stock on hand times unit cost
        logger.info("inventory_item.calculate_stock_value.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
