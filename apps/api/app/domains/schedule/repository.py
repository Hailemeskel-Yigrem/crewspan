"""Data access layer for Schedule."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.schedule.models import Schedule
from app.domains.schedule.schemas import ScheduleCreate, ScheduleUpdate

logger = structlog.get_logger(__name__)


class ScheduleRepository:
    """Persistence operations for schedules with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": Schedule.created_at,
        "updated_at": Schedule.updated_at,
        "technician_id": Schedule.technician_id,
        "work_order_id": Schedule.work_order_id,
        "starts_at": Schedule.starts_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[Schedule]]:
        stmt: Select[tuple[Schedule]] = select(Schedule)
        if not include_deleted:
            stmt = stmt.where(Schedule.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[Schedule]], tenant_id: UUID | None) -> Select[tuple[Schedule]]:
        if tenant_id is not None:
            stmt = stmt.where(Schedule.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[Schedule]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[Schedule]], Select[tuple[int]]]:
        if filters.get("technician_id") is not None:
            stmt = stmt.where(Schedule.technician_id == filters["technician_id"])
            count_stmt = count_stmt.where(Schedule.technician_id == filters["technician_id"])

        if filters.get("work_order_id") is not None:
            stmt = stmt.where(Schedule.work_order_id == filters["work_order_id"])
            count_stmt = count_stmt.where(Schedule.work_order_id == filters["work_order_id"])

        if filters.get("starts_at") is not None:
            stmt = stmt.where(Schedule.starts_at == filters["starts_at"])
            count_stmt = count_stmt.where(Schedule.starts_at == filters["starts_at"])

        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[Schedule]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[Schedule]]:
        column = self._ORDERABLE.get(order_by, Schedule.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> Schedule | None:
        stmt = self._base_select(include_deleted=include_deleted).where(Schedule.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("schedule.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(Schedule).where(Schedule.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Schedule.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(Schedule.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(Schedule)
        if not include_deleted:
            count_stmt = count_stmt.where(Schedule.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(Schedule)
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
        technician_id: UUID | None = None, work_order_id: UUID | None | None = None, starts_at: datetime | None = None,
        search: str | None = None,
    ) -> tuple[list[Schedule], int]:
        filters: dict[str, Any] = {
            "technician_id": technician_id, "work_order_id": work_order_id, "starts_at": starts_at,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(Schedule)
        if not include_deleted:
            count_stmt = count_stmt.where(Schedule.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "schedule.list",
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
    ) -> tuple[list[Schedule], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: ScheduleCreate, *, tenant_id: UUID | None = None) -> Schedule:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = Schedule(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("schedule.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: Schedule, data: ScheduleUpdate) -> Schedule:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("schedule.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: Schedule) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("schedule.deleted", entity_id=str(entity.id))

    async def restore(self, entity: Schedule) -> Schedule:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('schedule.restored', entity_id=str(entity.id))
        return entity
