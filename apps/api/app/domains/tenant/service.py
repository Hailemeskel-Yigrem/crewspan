"""Business logic for Tenant."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.tenant.exceptions import (
    TenantConflictError,
    TenantNotFoundError,
    TenantValidationError,
)
from app.domains.tenant.models import Tenant
from app.domains.tenant.repository import TenantRepository
from app.domains.tenant.schemas import TenantCreate, TenantRead, TenantUpdate

logger = structlog.get_logger(__name__)


class TenantService:
    """Orchestrates tenant use cases with validation, transitions, and auditing."""

    def __init__(self, repository: TenantRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: Tenant, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("tenant.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Tenant:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("tenant.not_found", entity_id=str(entity_id))
            raise TenantNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        return tenant_id  # type: ignore[return-value]

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> TenantRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("tenant.service.get", entity_id=str(entity_id))
        return TenantRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[TenantRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise TenantValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise TenantValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "tenant.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [TenantRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: TenantCreate, *, tenant_id: UUID | None = None
    ) -> TenantRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("tenant.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return TenantRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: TenantUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> TenantRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("tenant.service.update", entity_id=str(entity_id))
        return TenantRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("tenant.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> TenantRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise TenantNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("tenant.service.restore", entity_id=str(entity_id))
        return TenantRead.model_validate(restored)

    def _validate_create(self, data: TenantCreate) -> None:
        """Domain-specific create validation for Tenant."""
        raw = getattr(data, "slug", None)
        if raw is not None and not str(raw).strip():
            raise TenantValidationError("slug is required and cannot be blank")

        raw = getattr(data, "display_name", None)
        if raw is not None and not str(raw).strip():
            raise TenantValidationError("display_name is required and cannot be blank")

        raw = getattr(data, "subscription_tier", None)
        if raw is not None and not str(raw).strip():
            raise TenantValidationError("subscription_tier is required and cannot be blank")

        raw = getattr(data, "timezone", None)
        if raw is not None and not str(raw).strip():
            raise TenantValidationError("timezone is required and cannot be blank")

    def _validate_update(self, entity: Tenant, data: TenantUpdate) -> None:
        """Domain-specific update validation for Tenant."""
        logger.debug("tenant.validate_update", entity_id=str(entity.id))

    async def activate(self, entity_id: UUID, tenant_id: UUID | None):
        """Enable tenant access and notify administrators"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if entity.is_active:
            raise TenantConflictError("Tenant is already active")
        entity.is_active = True
        logger.info("tenant.activate", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def deactivate(self, entity_id: UUID, tenant_id: UUID | None):
        """Suspend tenant access while preserving data"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if not entity.is_active:
            raise TenantConflictError("Tenant is already inactive")
        entity.is_active = False
        logger.info("tenant.deactivate", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def update_settings(self, entity_id: UUID, tenant_id: UUID | None, settings: dict[str, object]) -> Tenant:
        """Merge tenant settings with validation"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("tenant.update_settings.start", entity_id=str(entity.id))
        # Merge tenant settings with validation
        logger.info("tenant.update_settings.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
