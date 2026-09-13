"""FastAPI routes for InvoiceLineItem."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.invoice_line_item.repository import InvoiceLineItemRepository
from app.domains.invoice_line_item.schemas import (
    InvoiceLineItemCreate,
    InvoiceLineItemListResponse,
    InvoiceLineItemRead,
    InvoiceLineItemUpdate,
)
from app.domains.invoice_line_item.service import InvoiceLineItemService

router = APIRouter(prefix="/invoice-line-items", tags=["InvoiceLineItem"])


def get_invoice_line_item_service(session=Depends(get_db_session)) -> InvoiceLineItemService:
    return InvoiceLineItemService(InvoiceLineItemRepository(session))


@router.get("", response_model=InvoiceLineItemListResponse)
async def list_invoice_line_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    invoice_id: UUID | None = Query(default=None),
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceLineItemListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        invoice_id=invoice_id,
    )
    return InvoiceLineItemListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_invoice_line_items(
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=InvoiceLineItemRead, status_code=status.HTTP_201_CREATED)
async def create_invoice_line_item(
    payload: InvoiceLineItemCreate,
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceLineItemRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=InvoiceLineItemRead)
async def get_invoice_line_item(
    entity_id: UUID,
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceLineItemRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=InvoiceLineItemRead)
async def update_invoice_line_item(
    entity_id: UUID,
    payload: InvoiceLineItemUpdate,
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceLineItemRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_invoice_line_item(
    entity_id: UUID,
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=InvoiceLineItemRead)
async def restore_invoice_line_item(
    entity_id: UUID,
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceLineItemRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/recalculate", response_model=InvoiceLineItemRead)
async def recalculate(
    entity_id: UUID,
    service: InvoiceLineItemService = Depends(get_invoice_line_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InvoiceLineItemRead:
    """Update line total from quantity and price"""
    result = await service.recalculate(entity_id, tenant_id)
    return InvoiceLineItemRead.model_validate(result)
