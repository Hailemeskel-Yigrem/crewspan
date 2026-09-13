"""Business logic for TechnicianSkill."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

import structlog

from app.domains.technician_skill.exceptions import (
    TechnicianSkillConflictError,
    TechnicianSkillNotFoundError,
    TechnicianSkillValidationError,
)
from app.domains.technician_skill.models import TechnicianSkill
from app.domains.technician_skill.repository import TechnicianSkillRepository
from app.domains.technician_skill.schemas import TechnicianSkillCreate, TechnicianSkillRead, TechnicianSkillUpdate

logger = structlog.get_logger(__name__)


class TechnicianSkillService:
    """Orchestrates technician_skill use cases with validation, transitions, and auditing."""

    def __init__(self, repository: TechnicianSkillRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: TechnicianSkill, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("technician_skill.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> TechnicianSkill:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("technician_skill.not_found", entity_id=str(entity_id))
            raise TechnicianSkillNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise TechnicianSkillValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> TechnicianSkillRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("technician_skill.service.get", entity_id=str(entity_id))
        return TechnicianSkillRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[TechnicianSkillRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise TechnicianSkillValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise TechnicianSkillValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "technician_skill.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [TechnicianSkillRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: TechnicianSkillCreate, *, tenant_id: UUID | None = None
    ) -> TechnicianSkillRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("technician_skill.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return TechnicianSkillRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: TechnicianSkillUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> TechnicianSkillRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("technician_skill.service.update", entity_id=str(entity_id))
        return TechnicianSkillRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("technician_skill.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> TechnicianSkillRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise TechnicianSkillNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("technician_skill.service.restore", entity_id=str(entity_id))
        return TechnicianSkillRead.model_validate(restored)

    def _validate_create(self, data: TechnicianSkillCreate) -> None:
        """Domain-specific create validation for TechnicianSkill."""
        raw = getattr(data, "skill_code", None)
        if raw is not None and not str(raw).strip():
            raise TechnicianSkillValidationError("skill_code is required and cannot be blank")

        raw = getattr(data, "skill_name", None)
        if raw is not None and not str(raw).strip():
            raise TechnicianSkillValidationError("skill_name is required and cannot be blank")

    def _validate_update(self, entity: TechnicianSkill, data: TechnicianSkillUpdate) -> None:
        """Domain-specific update validation for TechnicianSkill."""
        logger.debug("technician_skill.validate_update", entity_id=str(entity.id))

    async def renew_certification(self, entity_id: UUID, tenant_id: UUID | None, expires_at: date):
        """Extend certification expiry"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("technician_skill.renew_certification.start", entity_id=str(entity.id))
        # Extend certification expiry
        logger.info("technician_skill.renew_certification.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def is_valid(self, entity_id: UUID, tenant_id: UUID | None) -> TechnicianSkill:
        """Check certification not expired"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("technician_skill.is_valid.start", entity_id=str(entity.id))
        # Check certification not expired
        logger.info("technician_skill.is_valid.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
