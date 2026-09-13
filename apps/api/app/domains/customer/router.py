"""FastAPI routes for Customer."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.customer.repository import CustomerRepository
from app.domains.customer.schemas import (
    CustomerCreate,
    CustomerListResponse,
    CustomerMergeIntoRequest,
    CustomerRead,
    CustomerUpdate,
    CustomerUpdateCreditLimitRequest,
)
from app.domains.customer.service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customer"])


def get_customer_service(session=Depends(get_db_session)) -> CustomerService:
    return CustomerService(CustomerRepository(session))


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    account_number: str | None = Query(default=None),
    name: str | None = Query(default=None),
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        account_number=account_number, name=name,
    )
    return CustomerListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_customers(
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=CustomerRead)
async def get_customer(
    entity_id: UUID,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=CustomerRead)
async def update_customer(
    entity_id: UUID,
    payload: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_customer(
    entity_id: UUID,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=CustomerRead)
async def restore_customer(
    entity_id: UUID,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/update-credit-limit", response_model=CustomerRead)
async def update_credit_limit(
    entity_id: UUID,
    payload: CustomerUpdateCreditLimitRequest,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    """Adjust credit limit with audit trail"""
    result = await service.update_credit_limit(entity_id, tenant_id, limit=payload.limit)
    return CustomerRead.model_validate(result)

@router.post("/{entity_id}/merge-into", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def merge_into(
    entity_id: UUID,
    payload: CustomerMergeIntoRequest,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    """Merge duplicate customer records"""
    result = await service.merge_into(entity_id, tenant_id, target_id=payload.target_id)
    return CustomerRead.model_validate(result)

@router.post("/{entity_id}/archive", response_model=CustomerRead)
async def archive(
    entity_id: UUID,
    service: CustomerService = Depends(get_customer_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerRead:
    """Soft-archive inactive customer"""
    result = await service.archive(entity_id, tenant_id)
    return CustomerRead.model_validate(result)
