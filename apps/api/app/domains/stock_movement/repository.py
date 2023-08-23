"""Data access layer for StockMovement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.stock_movement.models import StockMovement
from app.domains.stock_movement.schemas import StockMovementCreate, StockMovementUpdate

logger = structlog.get_logger(__name__)


class StockMovementRepository:
    """Persistence operations for stock_movements with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": StockMovement.created_at,
        "updated_at": StockMovement.updated_at,
        "item_id": StockMovement.item_id,
        "from_location_id": StockMovement.from_location_id,
        "to_location_id": StockMovement.to_location_id,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[StockMovement]]:
        stmt: Select[tuple[StockMovement]] = select(StockMovement)
        if not include_deleted:
            stmt = stmt.where(StockMovement.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[StockMovement]], tenant_id: UUID | None) -> Select[tuple[StockMovement]]:
        if tenant_id is not None:
            stmt = stmt.where(StockMovement.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[StockMovement]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[StockMovement]], Select[tuple[int]]]:
        if filters.get("item_id") is not None:
            stmt = stmt.where(StockMovement.item_id == filters["item_id"])
            count_stmt = count_stmt.where(StockMovement.item_id == filters["item_id"])

        if filters.get("from_location_id") is not None:
            stmt = stmt.where(StockMovement.from_location_id == filters["from_location_id"])
            count_stmt = count_stmt.where(StockMovement.from_location_id == filters["from_location_id"])

        if filters.get("to_location_id") is not None:
            stmt = stmt.where(StockMovement.to_location_id == filters["to_location_id"])
            count_stmt = count_stmt.where(StockMovement.to_location_id == filters["to_location_id"])

        if filters.get("movement_type") is not None:
            stmt = stmt.where(StockMovement.movement_type == filters["movement_type"])
            count_stmt = count_stmt.where(StockMovement.movement_type == filters["movement_type"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(StockMovement.movement_type.ilike(pattern)))
            count_stmt = count_stmt.where(or_(StockMovement.movement_type.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[StockMovement]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[StockMovement]]:
        column = self._ORDERABLE.get(order_by, StockMovement.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> StockMovement | None:
        stmt = self._base_select(include_deleted=include_deleted).where(StockMovement.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("stock_movement.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(StockMovement).where(StockMovement.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(StockMovement.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(StockMovement.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(StockMovement)
        if not include_deleted:
            count_stmt = count_stmt.where(StockMovement.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(StockMovement)
        stmt = self._apply_tenant(stmt, tenant_id)
        _, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        return int(total)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        include_deleted: bool = False,
        item_id: UUID | None = None, from_location_id: UUID | None | None = None, to_location_id: UUID | None | None = None, movement_type: str | None = None,
        search: str | None = None,
    ) -> tuple[list[StockMovement], int]:
        filters: dict[str, Any] = {
            "item_id": item_id, "from_location_id": from_location_id, "to_location_id": to_location_id, "movement_type": movement_type,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(StockMovement)
        if not include_deleted:
            count_stmt = count_stmt.where(StockMovement.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "stock_movement.list",
            count=len(rows),
            total=int(total),
            page=page,
            order_by=order_by,
        )
        return list(rows), int(total)

    async def list_deleted(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[StockMovement], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: StockMovementCreate, *, tenant_id: UUID | None = None) -> StockMovement:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = StockMovement(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("stock_movement.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: StockMovement, data: StockMovementUpdate) -> StockMovement:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("stock_movement.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: StockMovement) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("stock_movement.deleted", entity_id=str(entity.id))

    async def restore(self, entity: StockMovement) -> StockMovement:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('stock_movement.restored', entity_id=str(entity.id))
        return entity
