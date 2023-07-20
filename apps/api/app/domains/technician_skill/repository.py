"""Data access layer for TechnicianSkill."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.technician_skill.models import TechnicianSkill
from app.domains.technician_skill.schemas import TechnicianSkillCreate, TechnicianSkillUpdate

logger = structlog.get_logger(__name__)


class TechnicianSkillRepository:
    """Persistence operations for technician_skills with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": TechnicianSkill.created_at,
        "updated_at": TechnicianSkill.updated_at,
        "technician_id": TechnicianSkill.technician_id,
        "skill_code": TechnicianSkill.skill_code,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[TechnicianSkill]]:
        stmt: Select[tuple[TechnicianSkill]] = select(TechnicianSkill)
        if not include_deleted:
            stmt = stmt.where(TechnicianSkill.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[TechnicianSkill]], tenant_id: UUID | None) -> Select[tuple[TechnicianSkill]]:
        if tenant_id is not None:
            stmt = stmt.where(TechnicianSkill.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[TechnicianSkill]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[TechnicianSkill]], Select[tuple[int]]]:
        if filters.get("technician_id") is not None:
            stmt = stmt.where(TechnicianSkill.technician_id == filters["technician_id"])
            count_stmt = count_stmt.where(TechnicianSkill.technician_id == filters["technician_id"])

        if filters.get("skill_code") is not None:
            stmt = stmt.where(TechnicianSkill.skill_code == filters["skill_code"])
            count_stmt = count_stmt.where(TechnicianSkill.skill_code == filters["skill_code"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(TechnicianSkill.skill_code.ilike(pattern)))
            count_stmt = count_stmt.where(or_(TechnicianSkill.skill_code.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[TechnicianSkill]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[TechnicianSkill]]:
        column = self._ORDERABLE.get(order_by, TechnicianSkill.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> TechnicianSkill | None:
        stmt = self._base_select(include_deleted=include_deleted).where(TechnicianSkill.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("technician_skill.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(TechnicianSkill).where(TechnicianSkill.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(TechnicianSkill.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(TechnicianSkill.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(TechnicianSkill)
        if not include_deleted:
            count_stmt = count_stmt.where(TechnicianSkill.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(TechnicianSkill)
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
        technician_id: UUID | None = None, skill_code: str | None = None,
        search: str | None = None,
    ) -> tuple[list[TechnicianSkill], int]:
        filters: dict[str, Any] = {
            "technician_id": technician_id, "skill_code": skill_code,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(TechnicianSkill)
        if not include_deleted:
            count_stmt = count_stmt.where(TechnicianSkill.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "technician_skill.list",
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
    ) -> tuple[list[TechnicianSkill], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: TechnicianSkillCreate, *, tenant_id: UUID | None = None) -> TechnicianSkill:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = TechnicianSkill(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("technician_skill.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: TechnicianSkill, data: TechnicianSkillUpdate) -> TechnicianSkill:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("technician_skill.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: TechnicianSkill) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("technician_skill.deleted", entity_id=str(entity.id))

    async def restore(self, entity: TechnicianSkill) -> TechnicianSkill:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('technician_skill.restored', entity_id=str(entity.id))
        return entity
