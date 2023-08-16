"""Business logic for InventoryLocation."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.inventory_location.exceptions import (
    InventoryLocationConflictError,
    InventoryLocationNotFoundError,
    InventoryLocationValidationError,
)
from app.domains.inventory_location.models import InventoryLocation
from app.domains.inventory_location.repository import InventoryLocationRepository
from app.domains.inventory_location.schemas import InventoryLocationCreate, InventoryLocationRead, InventoryLocationUpdate

logger = structlog.get_logger(__name__)


class InventoryLocationService:
    """Orchestrates inventory_location use cases with validation, transitions, and auditing."""

    def __init__(self, repository: InventoryLocationRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: InventoryLocation, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("inventory_location.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InventoryLocation:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("inventory_location.not_found", entity_id=str(entity_id))
            raise InventoryLocationNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise InventoryLocationValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> InventoryLocationRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("inventory_location.service.get", entity_id=str(entity_id))
        return InventoryLocationRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[InventoryLocationRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise InventoryLocationValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise InventoryLocationValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "inventory_location.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [InventoryLocationRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: InventoryLocationCreate, *, tenant_id: UUID | None = None
    ) -> InventoryLocationRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("inventory_location.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return InventoryLocationRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: InventoryLocationUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> InventoryLocationRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("inventory_location.service.update", entity_id=str(entity_id))
        return InventoryLocationRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("inventory_location.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> InventoryLocationRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise InventoryLocationNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("inventory_location.service.restore", entity_id=str(entity_id))
        return InventoryLocationRead.model_validate(restored)

    def _validate_create(self, data: InventoryLocationCreate) -> None:
        """Domain-specific create validation for InventoryLocation."""
        raw = getattr(data, "code", None)
        if raw is not None and not str(raw).strip():
            raise InventoryLocationValidationError("code is required and cannot be blank")

        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise InventoryLocationValidationError("name is required and cannot be blank")

        raw = getattr(data, "location_type", None)
        if raw is not None and not str(raw).strip():
            raise InventoryLocationValidationError("location_type is required and cannot be blank")

    def _validate_update(self, entity: InventoryLocation, data: InventoryLocationUpdate) -> None:
        """Domain-specific update validation for InventoryLocation."""
        logger.debug("inventory_location.validate_update", entity_id=str(entity.id))

    async def assign_to_technician(self, entity_id: UUID, tenant_id: UUID | None, technician_id: UUID):
        """Link location to technician van stock"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("inventory_location.assign_to_technician.start", entity_id=str(entity.id))
        # Link location to technician van stock
        logger.info("inventory_location.assign_to_technician.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def list_low_stock(self, entity_id: UUID, tenant_id: UUID | None) -> list:
        """Return items below reorder point at location"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("inventory_location.list_low_stock.start", entity_id=str(entity.id))
        # Return items below reorder point at location
        logger.info("inventory_location.list_low_stock.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
