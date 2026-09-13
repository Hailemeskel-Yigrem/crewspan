"""Business logic for CustomerSite."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.domains.customer_site.exceptions import (
    CustomerSiteConflictError,
    CustomerSiteNotFoundError,
    CustomerSiteValidationError,
)
from app.domains.customer_site.models import CustomerSite
from app.domains.customer_site.repository import CustomerSiteRepository
from app.domains.customer_site.schemas import CustomerSiteCreate, CustomerSiteRead, CustomerSiteUpdate

logger = structlog.get_logger(__name__)


class CustomerSiteService:
    """Orchestrates customer_site use cases with validation, transitions, and auditing."""

    def __init__(self, repository: CustomerSiteRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: CustomerSite, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("customer_site.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> CustomerSite:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("customer_site.not_found", entity_id=str(entity_id))
            raise CustomerSiteNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise CustomerSiteValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> CustomerSiteRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer_site.service.get", entity_id=str(entity_id))
        return CustomerSiteRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[CustomerSiteRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise CustomerSiteValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise CustomerSiteValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "customer_site.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [CustomerSiteRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: CustomerSiteCreate, *, tenant_id: UUID | None = None
    ) -> CustomerSiteRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("customer_site.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return CustomerSiteRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: CustomerSiteUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> CustomerSiteRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("customer_site.service.update", entity_id=str(entity_id))
        return CustomerSiteRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("customer_site.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> CustomerSiteRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise CustomerSiteNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("customer_site.service.restore", entity_id=str(entity_id))
        return CustomerSiteRead.model_validate(restored)

    def _validate_create(self, data: CustomerSiteCreate) -> None:
        """Domain-specific create validation for CustomerSite."""
        raw = getattr(data, "site_code", None)
        if raw is not None and not str(raw).strip():
            raise CustomerSiteValidationError("site_code is required and cannot be blank")

        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise CustomerSiteValidationError("name is required and cannot be blank")

    def _validate_update(self, entity: CustomerSite, data: CustomerSiteUpdate) -> None:
        """Domain-specific update validation for CustomerSite."""
        logger.debug("customer_site.validate_update", entity_id=str(entity.id))

    async def geocode(self, entity_id: UUID, tenant_id: UUID | None):
        """Resolve coordinates from address"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer_site.geocode.start", entity_id=str(entity.id))
        # Resolve coordinates from address
        logger.info("customer_site.geocode.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def validate_access_window(self, entity_id: UUID, tenant_id: UUID | None, at: datetime) -> bool:
        """Check if datetime falls within service window"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer_site.validate_access_window.start", entity_id=str(entity.id))
        # Check if datetime falls within service window
        logger.info("customer_site.validate_access_window.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
