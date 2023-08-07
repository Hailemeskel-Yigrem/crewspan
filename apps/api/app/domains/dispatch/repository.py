"""Data access layer for Dispatch."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.dispatch.models import Dispatch
from app.domains.dispatch.schemas import DispatchCreate, DispatchUpdate

logger = structlog.get_logger(__name__)


class DispatchRepository:
    """Persistence operations for dispatchs with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": Dispatch.created_at,
        "updated_at": Dispatch.updated_at,
        "work_order_id": Dispatch.work_order_id,
        "technician_id": Dispatch.technician_id,
        "status": Dispatch.status,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[Dispatch]]:
        stmt: Select[tuple[Dispatch]] = select(Dispatch)
        if not include_deleted:
            stmt = stmt.where(Dispatch.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[Dispatch]], tenant_id: UUID | None) -> Select[tuple[Dispatch]]:
        if tenant_id is not None:
            stmt = stmt.where(Dispatch.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[Dispatch]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[Dispatch]], Select[tuple[int]]]:
        if filters.get("work_order_id") is not None:
            stmt = stmt.where(Dispatch.work_order_id == filters["work_order_id"])
            count_stmt = count_stmt.where(Dispatch.work_order_id == filters["work_order_id"])

        if filters.get("technician_id") is not None:
            stmt = stmt.where(Dispatch.technician_id == filters["technician_id"])
            count_stmt = count_stmt.where(Dispatch.technician_id == filters["technician_id"])

        if filters.get("status") is not None:
            stmt = stmt.where(Dispatch.status == filters["status"])
            count_stmt = count_stmt.where(Dispatch.status == filters["status"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Dispatch.status.ilike(pattern)))
            count_stmt = count_stmt.where(or_(Dispatch.status.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[Dispatch]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[Dispatch]]:
        column = self._ORDERABLE.get(order_by, Dispatch.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> Dispatch | None:
        stmt = self._base_select(include_deleted=include_deleted).where(Dispatch.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("dispatch.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(Dispatch).where(Dispatch.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Dispatch.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(Dispatch.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(Dispatch)
        if not include_deleted:
            count_stmt = count_stmt.where(Dispatch.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(Dispatch)
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
        work_order_id: UUID | None = None, technician_id: UUID | None = None, status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Dispatch], int]:
        filters: dict[str, Any] = {
            "work_order_id": work_order_id, "technician_id": technician_id, "status": status,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(Dispatch)
        if not include_deleted:
            count_stmt = count_stmt.where(Dispatch.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "dispatch.list",
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
    ) -> tuple[list[Dispatch], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: DispatchCreate, *, tenant_id: UUID | None = None) -> Dispatch:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = Dispatch(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("dispatch.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: Dispatch, data: DispatchUpdate) -> Dispatch:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("dispatch.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: Dispatch) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("dispatch.deleted", entity_id=str(entity.id))

    async def restore(self, entity: Dispatch) -> Dispatch:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('dispatch.restored', entity_id=str(entity.id))
        return entity
