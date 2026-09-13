"""FastAPI routes for Invoice."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_db_session, get_tenant_id
from app.domains.invoice.repository import InvoiceRepository
from app.domains.invoice.schemas import (
    InvoiceCreate,
    InvoiceListResponse,
    InvoiceRead,
    InvoiceUpdate,
    InvoiceVoidRequest,
)
from app.domains.invoice.service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoice"])


def get_invoice_service(session=Depends(get_db_session)) -> InvoiceService:
    return InvoiceService(InvoiceRepository(session))


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    invoice_number: str | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    work_order_id: UUID | None | None = Query(default=None),
    status: str | None = Query(default=None),
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        invoice_number=invoice_number, customer_id=customer_id, work_order_id=work_order_id, status=status,
    )
    return InvoiceListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_invoices(
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=InvoiceRead)
async def get_invoice(
    entity_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=InvoiceRead)
async def update_invoice(
    entity_id: UUID,
    payload: InvoiceUpdate,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_invoice(
    entity_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=InvoiceRead)
async def restore_invoice(
    entity_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/finalize", response_model=InvoiceRead)
async def finalize(
    entity_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    """Lock invoice totals and assign number"""
    result = await service.finalize(entity_id, tenant_id)
    return InvoiceRead.model_validate(result)

@router.post("/{entity_id}/send", response_model=InvoiceRead)
async def send(
    entity_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    """Email invoice to customer"""
    result = await service.send(entity_id, tenant_id)
    return InvoiceRead.model_validate(result)

@router.post("/{entity_id}/void", response_model=InvoiceRead)
async def void(
    entity_id: UUID,
    payload: InvoiceVoidRequest,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    """Void draft or sent invoice"""
    result = await service.void(entity_id, tenant_id, reason=payload.reason)
    return InvoiceRead.model_validate(result)

@router.post("/{entity_id}/recalculate", response_model=InvoiceRead)
async def recalculate_totals(
    entity_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceRead:
    """Recompute subtotal, tax, and total"""
    result = await service.recalculate_totals(entity_id, tenant_id)
    return InvoiceRead.model_validate(result)
