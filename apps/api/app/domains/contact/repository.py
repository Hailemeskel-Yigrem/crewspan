"""Data access layer for Contact."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.contact.models import Contact
from app.domains.contact.schemas import ContactCreate, ContactUpdate

logger = structlog.get_logger(__name__)


class ContactRepository:
    """Persistence operations for contacts with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": Contact.created_at,
        "updated_at": Contact.updated_at,
        "customer_id": Contact.customer_id,
        "site_id": Contact.site_id,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[Contact]]:
        stmt: Select[tuple[Contact]] = select(Contact)
        if not include_deleted:
            stmt = stmt.where(Contact.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[Contact]], tenant_id: UUID | None) -> Select[tuple[Contact]]:
        if tenant_id is not None:
            stmt = stmt.where(Contact.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[Contact]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[Contact]], Select[tuple[int]]]:
        if filters.get("customer_id") is not None:
            stmt = stmt.where(Contact.customer_id == filters["customer_id"])
            count_stmt = count_stmt.where(Contact.customer_id == filters["customer_id"])

        if filters.get("site_id") is not None:
            stmt = stmt.where(Contact.site_id == filters["site_id"])
            count_stmt = count_stmt.where(Contact.site_id == filters["site_id"])

        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[Contact]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[Contact]]:
        column = self._ORDERABLE.get(order_by, Contact.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> Contact | None:
        stmt = self._base_select(include_deleted=include_deleted).where(Contact.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("contact.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(Contact).where(Contact.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Contact.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(Contact.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(Contact)
        if not include_deleted:
            count_stmt = count_stmt.where(Contact.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(Contact)
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
        customer_id: UUID | None = None, site_id: UUID | None | None = None,
        search: str | None = None,
    ) -> tuple[list[Contact], int]:
        filters: dict[str, Any] = {
            "customer_id": customer_id, "site_id": site_id,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(Contact)
        if not include_deleted:
            count_stmt = count_stmt.where(Contact.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "contact.list",
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
    ) -> tuple[list[Contact], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: ContactCreate, *, tenant_id: UUID | None = None) -> Contact:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = Contact(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("contact.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: Contact, data: ContactUpdate) -> Contact:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("contact.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: Contact) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("contact.deleted", entity_id=str(entity.id))

    async def restore(self, entity: Contact) -> Contact:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('contact.restored', entity_id=str(entity.id))
        return entity
