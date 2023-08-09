"""Data access layer for InventoryItem."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.inventory_item.models import InventoryItem
from app.domains.inventory_item.schemas import InventoryItemCreate, InventoryItemUpdate

logger = structlog.get_logger(__name__)


class InventoryItemRepository:
    """Persistence operations for inventory_items with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": InventoryItem.created_at,
        "updated_at": InventoryItem.updated_at,
        "sku": InventoryItem.sku,
        "name": InventoryItem.name,
        "category": InventoryItem.category,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[InventoryItem]]:
        stmt: Select[tuple[InventoryItem]] = select(InventoryItem)
        if not include_deleted:
            stmt = stmt.where(InventoryItem.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[InventoryItem]], tenant_id: UUID | None) -> Select[tuple[InventoryItem]]:
        if tenant_id is not None:
            stmt = stmt.where(InventoryItem.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[InventoryItem]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[InventoryItem]], Select[tuple[int]]]:
        if filters.get("sku") is not None:
            stmt = stmt.where(InventoryItem.sku == filters["sku"])
            count_stmt = count_stmt.where(InventoryItem.sku == filters["sku"])

        if filters.get("name") is not None:
            stmt = stmt.where(InventoryItem.name == filters["name"])
            count_stmt = count_stmt.where(InventoryItem.name == filters["name"])

        if filters.get("category") is not None:
            stmt = stmt.where(InventoryItem.category == filters["category"])
            count_stmt = count_stmt.where(InventoryItem.category == filters["category"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(InventoryItem.sku.ilike(pattern) | InventoryItem.name.ilike(pattern)))
            count_stmt = count_stmt.where(or_(InventoryItem.sku.ilike(pattern) | InventoryItem.name.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[InventoryItem]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[InventoryItem]]:
        column = self._ORDERABLE.get(order_by, InventoryItem.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> InventoryItem | None:
        stmt = self._base_select(include_deleted=include_deleted).where(InventoryItem.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("inventory_item.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(InventoryItem).where(InventoryItem.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(InventoryItem.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(InventoryItem.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(InventoryItem)
        if not include_deleted:
            count_stmt = count_stmt.where(InventoryItem.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(InventoryItem)
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
        sku: str | None = None, name: str | None = None, category: str | None | None = None,
        search: str | None = None,
    ) -> tuple[list[InventoryItem], int]:
        filters: dict[str, Any] = {
            "sku": sku, "name": name, "category": category,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(InventoryItem)
        if not include_deleted:
            count_stmt = count_stmt.where(InventoryItem.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "inventory_item.list",
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
    ) -> tuple[list[InventoryItem], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: InventoryItemCreate, *, tenant_id: UUID | None = None) -> InventoryItem:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = InventoryItem(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("inventory_item.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: InventoryItem, data: InventoryItemUpdate) -> InventoryItem:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("inventory_item.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: InventoryItem) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("inventory_item.deleted", entity_id=str(entity.id))

    async def restore(self, entity: InventoryItem) -> InventoryItem:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('inventory_item.restored', entity_id=str(entity.id))
        return entity
