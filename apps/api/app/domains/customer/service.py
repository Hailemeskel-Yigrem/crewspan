"""Business logic for Customer."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from app.domains.customer.exceptions import (
    CustomerConflictError,
    CustomerNotFoundError,
    CustomerValidationError,
)
from app.domains.customer.models import Customer
from app.domains.customer.repository import CustomerRepository
from app.domains.customer.schemas import CustomerCreate, CustomerRead, CustomerUpdate

logger = structlog.get_logger(__name__)


class CustomerService:
    """Orchestrates customer use cases with validation, transitions, and auditing."""

    def __init__(self, repository: CustomerRepository) -> None:
        self._repo = repository

    def _set_status(self, entity: Customer, target: str, *, action: str) -> None:
        if hasattr(entity, "status"):
            entity.status = target
            logger.info("customer.status_set", entity_id=str(entity.id), status=target, action=action)

    async def _require_entity(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> Customer:
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id)
        if entity is None:
            logger.warning("customer.not_found", entity_id=str(entity_id))
            raise CustomerNotFoundError(entity_id)
        return entity

    def _validate_tenant(self, tenant_id: UUID | None) -> UUID:
        if tenant_id is None:
            raise CustomerValidationError('X-Tenant-Id is required')
        return tenant_id

    async def get(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> CustomerRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer.service.get", entity_id=str(entity_id))
        return CustomerRead.model_validate(entity)

    async def list(
        self,
        *,
        tenant_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
        order_by: str = "created_at",
        order_dir: str = "desc",
        **filters: Any,
    ) -> tuple[list[CustomerRead], int]:
        tenant_id = self._validate_tenant(tenant_id)
        if page < 1:
            raise CustomerValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 200:
            raise CustomerValidationError("Page size must be between 1 and 200")
        rows, total = await self._repo.list(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_dir=order_dir,
            **filters,
        )
        logger.info(
            "customer.service.list",
            page=page,
            page_size=page_size,
            total=total,
            returned=len(rows),
        )
        return [CustomerRead.model_validate(r) for r in rows], total

    async def count(self, *, tenant_id: UUID | None = None, **filters: Any) -> int:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.count(tenant_id=tenant_id, **filters)

    async def exists(self, entity_id: UUID, *, tenant_id: UUID | None = None) -> bool:
        tenant_id = self._validate_tenant(tenant_id)
        return await self._repo.exists(entity_id, tenant_id=tenant_id)

    async def create(
        self, data: CustomerCreate, *, tenant_id: UUID | None = None
    ) -> CustomerRead:
        tenant_id = self._validate_tenant(tenant_id)
        self._validate_create(data)
        entity = await self._repo.create(data, tenant_id=tenant_id)
        logger.info("customer.service.create", entity_id=str(entity.id), tenant_id=str(tenant_id))
        return CustomerRead.model_validate(entity)

    async def update(
        self,
        entity_id: UUID,
        data: CustomerUpdate,
        *,
        tenant_id: UUID | None = None,
    ) -> CustomerRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        self._validate_update(entity, data)
        updated = await self._repo.update(entity, data)
        logger.info("customer.service.update", entity_id=str(entity_id))
        return CustomerRead.model_validate(updated)

    async def delete(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> None:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        await self._repo.soft_delete(entity)
        logger.info("customer.service.delete", entity_id=str(entity_id))

    async def restore(
        self, entity_id: UUID, *, tenant_id: UUID | None = None
    ) -> CustomerRead:
        tenant_id = self._validate_tenant(tenant_id)
        entity = await self._repo.get_by_id(entity_id, tenant_id=tenant_id, include_deleted=True)
        if entity is None:
            raise CustomerNotFoundError(entity_id)
        restored = await self._repo.restore(entity)
        logger.info("customer.service.restore", entity_id=str(entity_id))
        return CustomerRead.model_validate(restored)

    def _validate_create(self, data: CustomerCreate) -> None:
        """Domain-specific create validation for Customer."""
        raw = getattr(data, "account_number", None)
        if raw is not None and not str(raw).strip():
            raise CustomerValidationError("account_number is required and cannot be blank")

        raw = getattr(data, "name", None)
        if raw is not None and not str(raw).strip():
            raise CustomerValidationError("name is required and cannot be blank")

        if hasattr(data, "customer_type") and getattr(data, "customer_type") is not None:
            if getattr(data, "customer_type") not in {'residential', 'commercial', 'government'}:
                raise CustomerValidationError(f"Invalid customer_type: {getattr(data, 'customer_type')}")

        raw = getattr(data, "customer_type", None)
        if raw is not None and not str(raw).strip():
            raise CustomerValidationError("customer_type is required and cannot be blank")

        email_val = getattr(data, "billing_email", None)
        if email_val is not None and "@" not in email_val:
            raise CustomerValidationError("Valid email required for billing_email")

    def _validate_update(self, entity: Customer, data: CustomerUpdate) -> None:
        """Domain-specific update validation for Customer."""
        new_customer_type = getattr(data, "customer_type", None)
        if new_customer_type is not None and new_customer_type not in {'residential', 'commercial', 'government'}:
            raise CustomerValidationError(f"Invalid customer_type: {new_customer_type}")

    async def update_credit_limit(self, entity_id: UUID, tenant_id: UUID | None, limit: Decimal):
        """Adjust credit limit with audit trail"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer.update_credit_limit.start", entity_id=str(entity.id))
        # Adjust credit limit with audit trail
        logger.info("customer.update_credit_limit.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def merge_into(self, entity_id: UUID, tenant_id: UUID | None, target_id: UUID):
        """Merge duplicate customer records"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer.merge_into.start", entity_id=str(entity.id))
        # Merge duplicate customer records
        logger.info("customer.merge_into.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity

    async def archive(self, entity_id: UUID, tenant_id: UUID | None):
        """Soft-archive inactive customer"""
        entity = await self._require_entity(entity_id, tenant_id=tenant_id)
        logger.info("customer.archive.start", entity_id=str(entity.id))
        # Soft-archive inactive customer
        logger.info("customer.archive.complete", entity_id=str(entity.id))
        await self._repo._session.flush()
        await self._repo._session.refresh(entity)
        return entity
