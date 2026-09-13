"""Data access layer for AuditLog."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit_log.models import AuditLog
from app.domains.audit_log.schemas import AuditLogCreate, AuditLogUpdate

logger = structlog.get_logger(__name__)


class AuditLogRepository:
    """Persistence operations for audit_logs with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": AuditLog.created_at,
        "updated_at": AuditLog.updated_at,
        "actor_id": AuditLog.actor_id,
        "action": AuditLog.action,
        "resource_type": AuditLog.resource_type,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[AuditLog]]:
        stmt: Select[tuple[AuditLog]] = select(AuditLog)
        pass  # hard delete domain
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[AuditLog]], tenant_id: UUID | None) -> Select[tuple[AuditLog]]:
        if tenant_id is not None:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[AuditLog]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[AuditLog]], Select[tuple[int]]]:
        if filters.get("actor_id") is not None:
            stmt = stmt.where(AuditLog.actor_id == filters["actor_id"])
            count_stmt = count_stmt.where(AuditLog.actor_id == filters["actor_id"])

        if filters.get("action") is not None:
            stmt = stmt.where(AuditLog.action == filters["action"])
            count_stmt = count_stmt.where(AuditLog.action == filters["action"])

        if filters.get("resource_type") is not None:
            stmt = stmt.where(AuditLog.resource_type == filters["resource_type"])
            count_stmt = count_stmt.where(AuditLog.resource_type == filters["resource_type"])

        if filters.get("resource_id") is not None:
            stmt = stmt.where(AuditLog.resource_id == filters["resource_id"])
            count_stmt = count_stmt.where(AuditLog.resource_id == filters["resource_id"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(AuditLog.action.ilike(pattern) | AuditLog.resource_type.ilike(pattern)))
            count_stmt = count_stmt.where(or_(AuditLog.action.ilike(pattern) | AuditLog.resource_type.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[AuditLog]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[AuditLog]]:
        column = self._ORDERABLE.get(order_by, AuditLog.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> AuditLog | None:
        stmt = self._base_select(include_deleted=include_deleted).where(AuditLog.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("audit_log.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(AuditLog).where(AuditLog.id == entity_id)

        if tenant_id is not None:
            stmt = stmt.where(AuditLog.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(AuditLog)

        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(AuditLog)
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
        actor_id: UUID | None | None = None, action: str | None = None, resource_type: str | None = None, resource_id: UUID | None | None = None,
        search: str | None = None,
    ) -> tuple[list[AuditLog], int]:
        filters: dict[str, Any] = {
            "actor_id": actor_id, "action": action, "resource_type": resource_type, "resource_id": resource_id,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(AuditLog)

        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "audit_log.list",
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
    ) -> tuple[list[AuditLog], int]:
        return [], 0

    async def create(self, data: AuditLogCreate, *, tenant_id: UUID | None = None) -> AuditLog:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = AuditLog(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("audit_log.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: AuditLog, data: AuditLogUpdate) -> AuditLog:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("audit_log.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: AuditLog) -> None:
        await self._session.delete(entity)
        await self._session.flush()
        logger.info("audit_log.deleted", entity_id=str(entity.id))

    async def restore(self, entity: AuditLog) -> AuditLog:
        return entity  # hard-delete domain has no restore
