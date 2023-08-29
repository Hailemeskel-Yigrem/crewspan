"""Data access layer for PartsRequest."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.parts_request.models import PartsRequest
from app.domains.parts_request.schemas import PartsRequestCreate, PartsRequestUpdate

logger = structlog.get_logger(__name__)


class PartsRequestRepository:
    """Persistence operations for parts_requests with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": PartsRequest.created_at,
        "updated_at": PartsRequest.updated_at,
        "work_order_id": PartsRequest.work_order_id,
        "requested_by_id": PartsRequest.requested_by_id,
        "status": PartsRequest.status,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[PartsRequest]]:
        stmt: Select[tuple[PartsRequest]] = select(PartsRequest)
        if not include_deleted:
            stmt = stmt.where(PartsRequest.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[PartsRequest]], tenant_id: UUID | None) -> Select[tuple[PartsRequest]]:
        if tenant_id is not None:
            stmt = stmt.where(PartsRequest.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[PartsRequest]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[PartsRequest]], Select[tuple[int]]]:
        if filters.get("work_order_id") is not None:
            stmt = stmt.where(PartsRequest.work_order_id == filters["work_order_id"])
            count_stmt = count_stmt.where(PartsRequest.work_order_id == filters["work_order_id"])

        if filters.get("requested_by_id") is not None:
            stmt = stmt.where(PartsRequest.requested_by_id == filters["requested_by_id"])
            count_stmt = count_stmt.where(PartsRequest.requested_by_id == filters["requested_by_id"])

        if filters.get("status") is not None:
            stmt = stmt.where(PartsRequest.status == filters["status"])
            count_stmt = count_stmt.where(PartsRequest.status == filters["status"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(PartsRequest.status.ilike(pattern)))
            count_stmt = count_stmt.where(or_(PartsRequest.status.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[PartsRequest]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[PartsRequest]]:
        column = self._ORDERABLE.get(order_by, PartsRequest.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> PartsRequest | None:
        stmt = self._base_select(include_deleted=include_deleted).where(PartsRequest.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("parts_request.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(PartsRequest).where(PartsRequest.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(PartsRequest.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(PartsRequest.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(PartsRequest)
        if not include_deleted:
            count_stmt = count_stmt.where(PartsRequest.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(PartsRequest)
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
        work_order_id: UUID | None = None, requested_by_id: UUID | None = None, status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[PartsRequest], int]:
        filters: dict[str, Any] = {
            "work_order_id": work_order_id, "requested_by_id": requested_by_id, "status": status,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(PartsRequest)
        if not include_deleted:
            count_stmt = count_stmt.where(PartsRequest.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "parts_request.list",
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
    ) -> tuple[list[PartsRequest], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: PartsRequestCreate, *, tenant_id: UUID | None = None) -> PartsRequest:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = PartsRequest(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("parts_request.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: PartsRequest, data: PartsRequestUpdate) -> PartsRequest:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("parts_request.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: PartsRequest) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("parts_request.deleted", entity_id=str(entity.id))

    async def restore(self, entity: PartsRequest) -> PartsRequest:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('parts_request.restored', entity_id=str(entity.id))
        return entity
