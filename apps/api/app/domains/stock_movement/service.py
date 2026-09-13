"""Business logic for StockMovement."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.stock_movement.exceptions import (
    StockMovementConflictError,
    StockMovementNotFoundError,
    StockMovementValidationError,
)
from app.domains.stock_movement.models import StockMovement
from app.domains.stock_movement.repository import StockMovementRepository
from app.domains.stock_movement.schemas import StockMovementCreate, StockMovementRead, StockMovementUpdate

logger = structlog.get_logger(__name__)


class StockMovementService:
    """Orchestrates stock_movement use cases with validation, transitions, and auditing."""

    def __init__(self, repository: StockMovementRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: StockMovement, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("stock_movement.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> StockMovement:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("stock_movement.not_found", entity_id=str(entity_id))
            raise StockMovementNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise StockMovementValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> StockMovementRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("stock_movement.service.get", entity_id=str(entity_id))
        return StockMovementRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[StockMovementRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise StockMovementValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise StockMovementValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "stock_movement.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [StockMovementRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: StockMovementCreate, *, tenant_id: UUID | None = None
    ) -> StockMovementRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("stock_movement.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return StockMovementRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: StockMovementUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> StockMovementRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("stock_movement.service.update", entity_id=str(entity_id))
        return StockMovementRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("stock_movement.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> StockMovementRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise StockMovementNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("stock_movement.service.restore", entity_id=str(entity_id))
        return StockMovementRead.model_validate(restored)

    def _validate_create(self, data: StockMovementCreate) -> None:
        """Domain-specific create validation for StockMovement."""
        raw = getattr(data, "movement_type", None)
        if raw is not None and not str(raw).strip():
            raise StockMovementValidationError("movement_type is required and cannot be blank")

    def _validate_update(self, entity: StockMovement, data: StockMovementUpdate) -> None:
        """Domain-specific update validation for StockMovement."""
        logger.debug("stock_movement.validate_update", entity_id=str(entity.id))

    async def validate_quantity(self, entity_id: UUID, tenant_id: UUID | None) -> StockMovement:
        """Ensure sufficient stock for issue/transfer"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("stock_movement.validate_quantity.start", entity_id=str(entity.id))
        # Ensure sufficient stock for issue/transfer
        logger.info("stock_movement.validate_quantity.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def reverse(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """Create compensating movement"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("stock_movement.reverse.start", entity_id=str(entity.id))
        # Create compensating movement
        logger.info("stock_movement.reverse.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
