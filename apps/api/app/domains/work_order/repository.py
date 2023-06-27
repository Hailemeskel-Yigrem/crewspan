"""Data access layer for WorkOrder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.work_order.models import WorkOrder
from app.domains.work_order.schemas import WorkOrderCreate, WorkOrderUpdate

logger = structlog.get_logger(__name__)


class WorkOrderRepository:
    """Persistence operations for work_orders with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": WorkOrder.created_at,
        "updated_at": WorkOrder.updated_at,
        "order_number": WorkOrder.order_number,
        "customer_id": WorkOrder.customer_id,
        "site_id": WorkOrder.site_id,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[WorkOrder]]:
        stmt: Select[tuple[WorkOrder]] = select(WorkOrder)
        if not include_deleted:
            stmt = stmt.where(WorkOrder.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[WorkOrder]], tenant_id: UUID | None) -> Select[tuple[WorkOrder]]:
        if tenant_id is not None:
            stmt = stmt.where(WorkOrder.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[WorkOrder]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[WorkOrder]], Select[tuple[int]]]:
        if filters.get("order_number") is not None:
            stmt = stmt.where(WorkOrder.order_number == filters["order_number"])
            count_stmt = count_stmt.where(WorkOrder.order_number == filters["order_number"])

        if filters.get("customer_id") is not None:
            stmt = stmt.where(WorkOrder.customer_id == filters["customer_id"])
            count_stmt = count_stmt.where(WorkOrder.customer_id == filters["customer_id"])

        if filters.get("site_id") is not None:
            stmt = stmt.where(WorkOrder.site_id == filters["site_id"])
            count_stmt = count_stmt.where(WorkOrder.site_id == filters["site_id"])

        if filters.get("status") is not None:
            stmt = stmt.where(WorkOrder.status == filters["status"])
            count_stmt = count_stmt.where(WorkOrder.status == filters["status"])

        if filters.get("assigned_technician_id") is not None:
            stmt = stmt.where(WorkOrder.assigned_technician_id == filters["assigned_technician_id"])
            count_stmt = count_stmt.where(WorkOrder.assigned_technician_id == filters["assigned_technician_id"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(WorkOrder.order_number.ilike(pattern) | WorkOrder.status.ilike(pattern)))
            count_stmt = count_stmt.where(or_(WorkOrder.order_number.ilike(pattern) | WorkOrder.status.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[WorkOrder]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[WorkOrder]]:
        column = self._ORDERABLE.get(order_by, WorkOrder.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> WorkOrder | None:
        stmt = self._base_select(include_deleted=include_deleted).where(WorkOrder.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("work_order.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(WorkOrder).where(WorkOrder.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(WorkOrder.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(WorkOrder.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(WorkOrder)
        if not include_deleted:
            count_stmt = count_stmt.where(WorkOrder.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(WorkOrder)
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
        order_number: str | None = None, customer_id: UUID | None = None, site_id: UUID | None = None, status: str | None = None, assigned_technician_id: UUID | None | None = None,
        search: str | None = None,
    ) -> tuple[list[WorkOrder], int]:
        filters: dict[str, Any] = {
            "order_number": order_number, "customer_id": customer_id, "site_id": site_id, "status": status, "assigned_technician_id": assigned_technician_id,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(WorkOrder)
        if not include_deleted:
            count_stmt = count_stmt.where(WorkOrder.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "work_order.list",
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
    ) -> tuple[list[WorkOrder], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: WorkOrderCreate, *, tenant_id: UUID | None = None) -> WorkOrder:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = WorkOrder(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("work_order.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: WorkOrder, data: WorkOrderUpdate) -> WorkOrder:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("work_order.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: WorkOrder) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("work_order.deleted", entity_id=str(entity.id))

    async def restore(self, entity: WorkOrder) -> WorkOrder:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('work_order.restored', entity_id=str(entity.id))
        return entity
