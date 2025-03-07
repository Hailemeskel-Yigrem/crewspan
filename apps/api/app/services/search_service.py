"""Cross-entity search across customers, work orders, and technicians."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.domains.customer.models import Customer
from app.domains.technician.models import Technician
from app.domains.work_order.models import WorkOrder

logger = structlog.get_logger(__name__)


class SearchEntity(str, Enum):
    WORK_ORDER = "work_order"
    CUSTOMER = "customer"
    TECHNICIAN = "technician"


@dataclass(frozen=True, slots=True)
class SearchHit:
    entity_type: SearchEntity
    entity_id: UUID
    title: str
    subtitle: str | None
    score: float


class SearchService:
    """Simple ILIKE search with tenant isolation and result caps."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        tenant_id: UUID,
        query: str,
        *,
        entity_types: list[SearchEntity] | None = None,
        limit: int | None = None,
    ) -> list[SearchHit]:
        q = query.strip()
        if len(q) < 2:
            return []
        limit = min(limit or 25, settings.search_max_results)
        types = entity_types or list(SearchEntity)
        hits: list[SearchHit] = []

        if SearchEntity.WORK_ORDER in types:
            hits.extend(await self._search_work_orders(tenant_id, q, limit))
        if SearchEntity.CUSTOMER in types:
            hits.extend(await self._search_customers(tenant_id, q, limit))
        if SearchEntity.TECHNICIAN in types:
            hits.extend(await self._search_technicians(tenant_id, q, limit))

        hits.sort(key=lambda h: -h.score)
        result = hits[:limit]
        logger.info("search.executed", tenant_id=str(tenant_id), query=q, hits=len(result))
        return result

    async def _search_work_orders(self, tenant_id: UUID, q: str, limit: int) -> list[SearchHit]:
        pattern = f"%{q}%"
        stmt = (
            select(WorkOrder)
            .where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.deleted_at.is_(None),
                or_(WorkOrder.title.ilike(pattern), WorkOrder.order_number.ilike(pattern)),
            )
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            SearchHit(
                entity_type=SearchEntity.WORK_ORDER,
                entity_id=row.id,
                title=row.title,
                subtitle=row.order_number,
                score=1.0 if q.lower() in row.order_number.lower() else 0.8,
            )
            for row in rows
        ]

    async def _search_customers(self, tenant_id: UUID, q: str, limit: int) -> list[SearchHit]:
        pattern = f"%{q}%"
        stmt = (
            select(Customer)
            .where(
                Customer.tenant_id == tenant_id,
                Customer.deleted_at.is_(None),
                or_(Customer.name.ilike(pattern), Customer.account_number.ilike(pattern)),
            )
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            SearchHit(
                entity_type=SearchEntity.CUSTOMER,
                entity_id=row.id,
                title=row.name,
                subtitle=row.account_number,
                score=0.9,
            )
            for row in rows
        ]

    async def _search_technicians(self, tenant_id: UUID, q: str, limit: int) -> list[SearchHit]:
        pattern = f"%{q}%"
        stmt = (
            select(Technician)
            .where(
                Technician.tenant_id == tenant_id,
                Technician.deleted_at.is_(None),
                Technician.employee_id.ilike(pattern),
            )
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            SearchHit(
                entity_type=SearchEntity.TECHNICIAN,
                entity_id=row.id,
                title=row.employee_id,
                subtitle=row.status,
                score=0.85,
            )
            for row in rows
        ]
