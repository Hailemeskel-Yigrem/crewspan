"""Data access layer for Invoice."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.invoice.models import Invoice
from app.domains.invoice.schemas import InvoiceCreate, InvoiceUpdate

logger = structlog.get_logger(__name__)


class InvoiceRepository:
    """Persistence operations for invoices with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": Invoice.created_at,
        "updated_at": Invoice.updated_at,
        "invoice_number": Invoice.invoice_number,
        "customer_id": Invoice.customer_id,
        "work_order_id": Invoice.work_order_id,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[Invoice]]:
        stmt: Select[tuple[Invoice]] = select(Invoice)
        if not include_deleted:
            stmt = stmt.where(Invoice.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[Invoice]], tenant_id: UUID | None) -> Select[tuple[Invoice]]:
        if tenant_id is not None:
            stmt = stmt.where(Invoice.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[Invoice]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[Invoice]], Select[tuple[int]]]:
        if filters.get("invoice_number") is not None:
            stmt = stmt.where(Invoice.invoice_number == filters["invoice_number"])
            count_stmt = count_stmt.where(Invoice.invoice_number == filters["invoice_number"])

        if filters.get("customer_id") is not None:
            stmt = stmt.where(Invoice.customer_id == filters["customer_id"])
            count_stmt = count_stmt.where(Invoice.customer_id == filters["customer_id"])

        if filters.get("work_order_id") is not None:
            stmt = stmt.where(Invoice.work_order_id == filters["work_order_id"])
            count_stmt = count_stmt.where(Invoice.work_order_id == filters["work_order_id"])

        if filters.get("status") is not None:
            stmt = stmt.where(Invoice.status == filters["status"])
            count_stmt = count_stmt.where(Invoice.status == filters["status"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Invoice.invoice_number.ilike(pattern) | Invoice.status.ilike(pattern)))
            count_stmt = count_stmt.where(or_(Invoice.invoice_number.ilike(pattern) | Invoice.status.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[Invoice]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[Invoice]]:
        column = self._ORDERABLE.get(order_by, Invoice.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> Invoice | None:
        stmt = self._base_select(include_deleted=include_deleted).where(Invoice.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("invoice.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(Invoice).where(Invoice.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Invoice.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(Invoice.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(Invoice)
        if not include_deleted:
            count_stmt = count_stmt.where(Invoice.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(Invoice)
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
        invoice_number: str | None = None, customer_id: UUID | None = None, work_order_id: UUID | None | None = None, status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Invoice], int]:
        filters: dict[str, Any] = {
            "invoice_number": invoice_number, "customer_id": customer_id, "work_order_id": work_order_id, "status": status,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(Invoice)
        if not include_deleted:
            count_stmt = count_stmt.where(Invoice.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "invoice.list",
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
    ) -> tuple[list[Invoice], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: InvoiceCreate, *, tenant_id: UUID | None = None) -> Invoice:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = Invoice(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("invoice.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: Invoice, data: InvoiceUpdate) -> Invoice:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("invoice.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: Invoice) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("invoice.deleted", entity_id=str(entity.id))

    async def restore(self, entity: Invoice) -> Invoice:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('invoice.restored', entity_id=str(entity.id))
        return entity
