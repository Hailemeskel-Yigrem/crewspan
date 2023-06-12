"""Data access layer for Customer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.customer.models import Customer
from app.domains.customer.schemas import CustomerCreate, CustomerUpdate

logger = structlog.get_logger(__name__)


class CustomerRepository:
    """Persistence operations for customers with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": Customer.created_at,
        "updated_at": Customer.updated_at,
        "account_number": Customer.account_number,
        "name": Customer.name,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[Customer]]:
        stmt: Select[tuple[Customer]] = select(Customer)
        if not include_deleted:
            stmt = stmt.where(Customer.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[Customer]], tenant_id: UUID | None) -> Select[tuple[Customer]]:
        if tenant_id is not None:
            stmt = stmt.where(Customer.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[Customer]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[Customer]], Select[tuple[int]]]:
        if filters.get("account_number") is not None:
            stmt = stmt.where(Customer.account_number == filters["account_number"])
            count_stmt = count_stmt.where(Customer.account_number == filters["account_number"])

        if filters.get("name") is not None:
            stmt = stmt.where(Customer.name == filters["name"])
            count_stmt = count_stmt.where(Customer.name == filters["name"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Customer.account_number.ilike(pattern) | Customer.name.ilike(pattern)))
            count_stmt = count_stmt.where(or_(Customer.account_number.ilike(pattern) | Customer.name.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[Customer]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[Customer]]:
        column = self._ORDERABLE.get(order_by, Customer.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> Customer | None:
        stmt = self._base_select(include_deleted=include_deleted).where(Customer.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("customer.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(Customer).where(Customer.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Customer.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(Customer.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(Customer)
        if not include_deleted:
            count_stmt = count_stmt.where(Customer.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(Customer)
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
        account_number: str | None = None, name: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Customer], int]:
        filters: dict[str, Any] = {
            "account_number": account_number, "name": name,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(Customer)
        if not include_deleted:
            count_stmt = count_stmt.where(Customer.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "customer.list",
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
    ) -> tuple[list[Customer], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: CustomerCreate, *, tenant_id: UUID | None = None) -> Customer:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = Customer(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("customer.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: Customer, data: CustomerUpdate) -> Customer:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("customer.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: Customer) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info("customer.deleted", entity_id=str(entity.id))

    async def restore(self, entity: Customer) -> Customer:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('customer.restored', entity_id=str(entity.id))
        return entity
