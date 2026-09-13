"""FastAPI routes for Payment."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.payment.repository import PaymentRepository
from app.domains.payment.schemas import (
    PaymentCreate,
    PaymentListResponse,
    PaymentRead,
    PaymentRefundRequest,
    PaymentUpdate,
)
from app.domains.payment.service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payment"])


def get_payment_service(session=Depends(get_db_session)) -> PaymentService:
    return PaymentService(PaymentRepository(session))


@router.get("", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    invoice_id: UUID | None = Query(default=None),
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        invoice_id=invoice_id,
    )
    return PaymentListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_payments(
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payload: PaymentCreate,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=PaymentRead)
async def get_payment(
    entity_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=PaymentRead)
async def update_payment(
    entity_id: UUID,
    payload: PaymentUpdate,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_payment(
    entity_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=PaymentRead)
async def restore_payment(
    entity_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/refund", response_model=PaymentRead)
async def refund(
    entity_id: UUID,
    payload: PaymentRefundRequest,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentRead:
    """Issue partial or full refund"""
    result = await service.refund(entity_id, tenant_id, amount=payload.amount, reason=payload.reason)
    return PaymentRead.model_validate(result)

@router.post("/{entity_id}/reconcile", response_model=PaymentRead)
async def reconcile(
    entity_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PaymentRead:
    """Mark payment reconciled with bank feed"""
    result = await service.reconcile(entity_id, tenant_id)
    return PaymentRead.model_validate(result)
