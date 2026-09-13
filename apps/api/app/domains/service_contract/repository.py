"""Data access layer for ServiceContract."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.service_contract.models import ServiceContract
from app.domains.service_contract.schemas import ServiceContractCreate, ServiceContractUpdate

logger = structlog.get_logger(__name__)


class ServiceContractRepository:
    """Persistence operations for service_contracts with filter, ordering, and soft-delete support."""

    _ORDERABLE = {
        "created_at": ServiceContract.created_at,
        "updated_at": ServiceContract.updated_at,
        "customer_id": ServiceContract.customer_id,
        "contract_number": ServiceContract.contract_number,
        "status": ServiceContract.status,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_select(self, *, include_deleted: bool = False) -> Select[tuple[ServiceContract]]:
        stmt: Select[tuple[ServiceContract]] = select(ServiceContract)
        if not include_deleted:
            stmt = stmt.where(ServiceContract.deleted_at.is_(None))
        return stmt

    def _apply_tenant(self, stmt: Select[tuple[ServiceContract]], tenant_id: UUID | None) -> Select[tuple[ServiceContract]]:
        if tenant_id is not None:
            stmt = stmt.where(ServiceContract.tenant_id == tenant_id)
        return stmt

    def _apply_filters(
        self,
        stmt: Select[tuple[ServiceContract]],
        count_stmt: Select[tuple[int]],
        filters: dict[str, Any],
    ) -> tuple[Select[tuple[ServiceContract]], Select[tuple[int]]]:
        if filters.get("customer_id") is not None:
            stmt = stmt.where(ServiceContract.customer_id == filters["customer_id"])
            count_stmt = count_stmt.where(ServiceContract.customer_id == filters["customer_id"])

        if filters.get("contract_number") is not None:
            stmt = stmt.where(ServiceContract.contract_number == filters["contract_number"])
            count_stmt = count_stmt.where(ServiceContract.contract_number == filters["contract_number"])

        if filters.get("status") is not None:
            stmt = stmt.where(ServiceContract.status == filters["status"])
            count_stmt = count_stmt.where(ServiceContract.status == filters["status"])
        search = filters.get("search")
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(ServiceContract.contract_number.ilike(pattern) | ServiceContract.status.ilike(pattern)))
            count_stmt = count_stmt.where(or_(ServiceContract.contract_number.ilike(pattern) | ServiceContract.status.ilike(pattern)))
        return stmt, count_stmt

    def _apply_ordering(
        self,
        stmt: Select[tuple[ServiceContract]],
        *,
        order_by: str = "created_at",
        order_dir: str = "desc",
    ) -> Select[tuple[ServiceContract]]:
        column = self._ORDERABLE.get(order_by, ServiceContract.created_at)
        if order_dir.lower() == "asc":
            return stmt.order_by(column.asc())
        return stmt.order_by(column.desc())

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> ServiceContract | None:
        stmt = self._base_select(include_deleted=include_deleted).where(ServiceContract.id == entity_id)
        stmt = self._apply_tenant(stmt, tenant_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug("service_contract.get_by_id", entity_id=str(entity_id), found=row is not None)
        return row

    async def exists(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count()).select_from(ServiceContract).where(ServiceContract.id == entity_id)
        if not include_deleted:
            stmt = stmt.where(ServiceContract.deleted_at.is_(None))
        if tenant_id is not None:
            stmt = stmt.where(ServiceContract.tenant_id == tenant_id)
        count = (await self._session.execute(stmt)).scalar_one()
        return int(count) > 0

    async def count(
        self,
        *,
        tenant_id: UUID | None = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> int:
        count_stmt = select(func.count()).select_from(ServiceContract)
        if not include_deleted:
            count_stmt = count_stmt.where(ServiceContract.deleted_at.is_(None))
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt = select(ServiceContract)
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
        customer_id: UUID | None = None, contract_number: str | None = None, status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[ServiceContract], int]:
        filters: dict[str, Any] = {
            "customer_id": customer_id, "contract_number": contract_number, "status": status,
            "search": search,
        }
        stmt = self._base_select(include_deleted=include_deleted)
        count_stmt = select(func.count()).select_from(ServiceContract)
        if not include_deleted:
            count_stmt = count_stmt.where(ServiceContract.deleted_at.is_(None))
        stmt = self._apply_tenant(stmt, tenant_id)
        count_stmt = self._apply_tenant(count_stmt, tenant_id)
        stmt, count_stmt = self._apply_filters(stmt, count_stmt, filters)
        total = (await self._session.execute(count_stmt)).scalar_one()
        stmt = self._apply_ordering(stmt, order_by=order_by, order_dir=order_dir)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        rows = (await self._session.execute(stmt)).scalars().all()
        logger.debug(
            "service_contract.list",
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
    ) -> tuple[list[ServiceContract], int]:
        return await self.list(tenant_id=tenant_id, page=page, page_size=page_size, include_deleted=True)

    async def create(self, data: ServiceContractCreate, *, tenant_id: UUID | None = None) -> ServiceContract:
        payload = data.model_dump(exclude_unset=True)
        if tenant_id is None:
            raise ValueError('tenant_id required')
        payload['tenant_id'] = tenant_id
        entity = ServiceContract(**payload)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("service_contract.created", entity_id=str(entity.id), tenant_id=str(tenant_id) if tenant_id else None)
        return entity

    async def update(self, entity: ServiceContract, data: ServiceContractUpdate) -> ServiceContract:
        changes = data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(entity, key, value)
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info("service_contract.updated", entity_id=str(entity.id), fields=sorted(changes))
        return entity

    async def soft_delete(self, entity: ServiceContract) -> None:
        entity.deleted_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("service_contract.deleted", entity_id=str(entity.id))

    async def restore(self, entity: ServiceContract) -> ServiceContract:
        if entity.deleted_at is None:
            return entity
        entity.deleted_at = None
        await self._session.flush()
        await self._session.refresh(entity)
        logger.info('service_contract.restored', entity_id=str(entity.id))
        return entity
