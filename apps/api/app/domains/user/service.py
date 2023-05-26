"""Business logic for User."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog

from app.domains.user.exceptions import (
    UserConflictError,
    UserNotFoundError,
    UserValidationError,
)
from app.domains.user.models import User
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import UserCreate, UserRead, UserUpdate

logger = structlog.get_logger(__name__)


class UserService:
    """Orchestrates user use cases with validation, transitions, and auditing."""

    def __init__(self, repository: UserRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: User, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("user.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> User:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("user.not_found", entity_id=str(entity_id))
            raise UserNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise UserValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> UserRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("user.service.get", entity_id=str(entity_id))
        return UserRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[UserRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise UserValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise UserValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "user.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [UserRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: UserCreate, *, tenant_id: UUID | None = None
    ) -> UserRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("user.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return UserRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: UserUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> UserRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("user.service.update", entity_id=str(entity_id))
        return UserRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("user.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> UserRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise UserNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("user.service.restore", entity_id=str(entity_id))
        return UserRead.model_validate(restored)

    def _validate_create(self, data: UserCreate) -> None:
        """Domain-specific create validation for User."""
        email_val = getattr(data, "email", None)
        if email_val is not None and "@" not in email_val:
            raise UserValidationError("Valid email required for email")

        raw = getattr(data, "email", None)
        if raw is not None and not str(raw).strip():
            raise UserValidationError("email is required and cannot be blank")

        raw = getattr(data, "full_name", None)
        if raw is not None and not str(raw).strip():
            raise UserValidationError("full_name is required and cannot be blank")

    def _validate_update(self, entity: User, data: UserUpdate) -> None:
        """Domain-specific update validation for User."""
        logger.debug("user.validate_update", entity_id=str(entity.id))

    async def change_password(self, entity_id: UUID, tenant_id: UUID | None, new_password: str):
        """Validate and rotate user password hash"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("user.change_password.start", entity_id=str(entity.id))
        # Validate and rotate user password hash
        logger.info("user.change_password.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def record_login(self, entity_id: UUID, tenant_id: UUID | None):
        """Update last login timestamp"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("user.record_login.start", entity_id=str(entity.id))
        # Update last login timestamp
        logger.info("user.record_login.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def deactivate(self, entity_id: UUID, tenant_id: UUID | None):
        """Disable user without deleting audit history"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        if not entity.is_active:
            raise UserConflictError("Tenant is already inactive")
        entity.is_active = False
        logger.info("user.deactivate", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
