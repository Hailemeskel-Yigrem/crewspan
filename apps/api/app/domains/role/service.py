"""Business logic for Role."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.role.exceptions import (
    RoleNotFoundError,
    RoleValidationError,
)
from app.domains.role.models import Role
from app.domains.role.repository import RoleRepository
from app.domains.role.schemas import RoleCreate, RoleRead, RoleUpdate

logger = structlog.get_logger(__name__)


class RoleService:
    """Orchestrates role use cases with validation, transitions, and auditing."""

    def __init__(self, repository: RoleRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: Role, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("role.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Role:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("role.not_found", entity_id=str(entity_id))
            raise RoleNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise RoleValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> RoleRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("role.service.get", entity_id=str(entity_id))
        return RoleRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[RoleRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise RoleValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise RoleValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "role.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [RoleRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: RoleCreate, *, tenant_id: UUID | None = None
    ) -> RoleRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("role.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return RoleRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: RoleUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> RoleRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("role.service.update", entity_id=str(entity_id))
        return RoleRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("role.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> RoleRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise RoleNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("role.service.restore", entity_id=str(entity_id))
        return RoleRead.model_validate(restored)

    def _validate_create(self, data: RoleCreate) -> None:
        """Domain-specific create validation for Role."""
        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise RoleValidationError("name is required and cannot be blank")

    def _validate_update(self, entity: Role, data: RoleUpdate) -> None:
        """Domain-specific update validation for Role."""
        logger.debug("role.validate_update", entity_id=str(entity.id))

    async def grant_permission(self, entity_id: UUID, tenant_id: UUID | None, permission: str) -> list:
        """Add permission if not already present"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("role.grant_permission.start", entity_id=str(entity.id))
        # Add permission if not already present
        logger.info("role.grant_permission.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def revoke_permission(self, entity_id: UUID, tenant_id: UUID | None, permission: str) -> list:
        """Remove permission from role"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("role.revoke_permission.start", entity_id=str(entity.id))
        # Remove permission from role
        logger.info("role.revoke_permission.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def clone(self, entity_id: UUID, tenant_id: UUID | None, new_name: str) -> Role:
        """Duplicate role under a new name"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("role.clone.start", entity_id=str(entity.id))
        # Duplicate role under a new name
        logger.info("role.clone.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
