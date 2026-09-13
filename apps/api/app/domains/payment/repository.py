"""Data access layer for Payment."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.payment.models import Payment
from app.domains.payment.schemas import PaymentCreate, PaymentUpdate

logger = structlog.get_logger(__name__)


class PaymentRepository:
    """Persistence operations for payments with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": Payment.created_at,
        "updated_at": Payment.updated_at,
        "invoice_id": Payment.invoice_id,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[Payment]]:
        stmt: Select[tuple[Payment]] = select(Payment)
        if not include_deleted:
            stmt = stmt.where(Payment.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[Payment]], tenant_id: UUID | None) -> Select[tuple[Payment]]:
        if tenant_id is not None:
            stmt = stmt.where(Payment.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[Payment]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[Payment]], Select[tuple[int]]]:
        if filters.get("invoice_id") is not None:
            stmt = stmt.where(Payment.invoice_id == filters["invoice_id"])
            count_stmt = count_stmt.where(Payment.invoice_id == filters["invoice_id"])

        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[Payment]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[Payment]]:
        column = self._ORDERABLE.get(order_by, Payment.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> Payment | None:
        stmt = self._base_select(include_deleted=include_deleted).where(Payment.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("payment.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(Payment).where(Payment.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(Payment.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(Payment.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(Payment)
        if not include_deleted:
            count_stmt = count_stmt.where(Payment.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(Payment)
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
        invoice_id: UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Payment], int]:
        filters: dict[str, Any] = {
            "invoice_id": invoice_id,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(Payment)
        if not include_deleted:
            count_stmt = count_stmt.where(Payment.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "payment.list",
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
    ) -> tuple[list[Payment], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: PaymentCreate, *, tenant_id: UUID | None = None) -> Payment:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = Payment(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("payment.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: Payment, data: PaymentUpdate) -> Payment:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("payment.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: Payment) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("payment.deleted", entity_id=str(entity.id))

    async def restore(self, entity: Payment) -> Payment:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('payment.restored', entity_id=str(entity.id))
        return entity
