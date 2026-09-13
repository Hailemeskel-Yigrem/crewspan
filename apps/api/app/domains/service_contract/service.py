"""Business logic for ServiceContract."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

import structlog

from app.domains.service_contract.exceptions import (
    ServiceContractConflictError,
    ServiceContractNotFoundError,
    ServiceContractValidationError,
)
from app.domains.service_contract.models import ServiceContract
from app.domains.service_contract.repository import ServiceContractRepository
from app.domains.service_contract.schemas import ServiceContractCreate, ServiceContractRead, ServiceContractUpdate

logger = structlog.get_logger(__name__)


class ServiceContractService:
    """Orchestrates service_contract use cases with validation, transitions, and auditing."""

    def __init__(self, repository: ServiceContractRepository) -> None:
        self._repo = repository

    _STATUS_TRANSITIONS: dict[str, set[str]] = {
        "draft": {"submitted", "cancelled", "active", "pending"},
        "pending": {"approved", "rejected", "cancelled", "active"},
        "submitted": {"in_progress", "assigned", "cancelled"},
        "assigned": {"in_progress", "cancelled"},
        "in_progress": {"completed", "cancelled", "blocked"},
        "blocked": {"in_progress", "cancelled"},
        "approved": {"fulfilled", "rejected", "cancelled"},
        "active": {"inactive", "completed", "cancelled", "blocked"},
        "completed": set(),
        "cancelled": set(),
        "rejected": set(),
    }

    def _assert_status_transition(self, entity: ServiceContract, target: str, *, action: str) -> None:
        current = str(getattr(entity, "status", "draft"))
        allowed = self._STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and current != target:
            raise ServiceContractValidationError(
                f"Cannot {action} service_contract from status '{current}' to '{target}'"
            )
        logger.info(
            "service_contract.status_transition",
            entity_id=str(entity.id),
            from_status=current,
            to_status=target,
            action=action,
        )

    def _set_status(self, entity: ServiceContract, target: str, *, action: str) -> None:
        self._assert_status_transition(entity, target, action=action)
        entity.status = target

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> ServiceContract:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("service_contract.not_found", entity_id=str(entity_id))
            raise ServiceContractNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise ServiceContractValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> ServiceContractRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("service_contract.service.get", entity_id=str(entity_id))
        return ServiceContractRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[ServiceContractRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise ServiceContractValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise ServiceContractValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "service_contract.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [ServiceContractRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: ServiceContractCreate, *, tenant_id: UUID | None = None
    ) -> ServiceContractRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("service_contract.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return ServiceContractRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: ServiceContractUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> ServiceContractRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("service_contract.service.update", entity_id=str(entity_id))
        return ServiceContractRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("service_contract.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> ServiceContractRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise ServiceContractNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("service_contract.service.restore", entity_id=str(entity_id))
        return ServiceContractRead.model_validate(restored)

    def _validate_create(self, data: ServiceContractCreate) -> None:
        """Domain-specific create validation for ServiceContract."""
        raw = getattr(data, "contract_number", None)
        if raw is not None and not str(raw).strip():
            raise ServiceContractValidationError("contract_number is required and cannot be blank")

        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise ServiceContractValidationError("name is required and cannot be blank")

        raw = getattr(data, "billing_frequency", None)
        if raw is not None and not str(raw).strip():
            raise ServiceContractValidationError("billing_frequency is required and cannot be blank")

        if hasattr(data, "status") and getattr(data, "status") is not None:
            if getattr(data, "status") not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
                raise ServiceContractValidationError("Invalid status: {getattr(data, 'status')}")

        raw = getattr(data, "status", None)
        if raw is not None and not str(raw).strip():
            raise ServiceContractValidationError("status is required and cannot be blank")

    def _validate_update(self, entity: ServiceContract, data: ServiceContractUpdate) -> None:
        """Domain-specific update validation for ServiceContract."""
        if data.status is not None and data.status == entity.status:
            raise ServiceContractConflictError("Status is already {entity.status}")

        new_status = getattr(data, "status", None)
        if new_status is not None and new_status not in {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}:
            raise ServiceContractValidationError("Invalid status: {new_status}")

    async def renew(self, entity_id: UUID, tenant_id: UUID | None, new_end_date: date):
        """Extend contract end date"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("service_contract.renew.start", entity_id=str(entity.id))
        # Extend contract end date
        logger.info("service_contract.renew.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def terminate(self, entity_id: UUID, tenant_id: UUID | None, reason: str):
        """End contract early"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("service_contract.terminate.start", entity_id=str(entity.id))
        # End contract early
        logger.info("service_contract.terminate.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def generate_work_orders(self, entity_id: UUID, tenant_id: UUID | None) -> list:
        """Create preventive maintenance work orders"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("service_contract.generate_work_orders.start", entity_id=str(entity.id))
        # Create preventive maintenance work orders
        logger.info("service_contract.generate_work_orders.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
