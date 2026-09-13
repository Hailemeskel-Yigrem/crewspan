"""FastAPI routes for WorkOrder."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.work_order.repository import WorkOrderRepository
from app.domains.work_order.schemas import (
    WorkOrderAssignTechnicianRequest,
    WorkOrderCancelRequest,
    WorkOrderCompleteRequest,
    WorkOrderCreate,
    WorkOrderListResponse,
    WorkOrderRead,
    WorkOrderUpdate,
)
from app.domains.work_order.service import WorkOrderService

router = APIRouter(prefix="/work-orders", tags=["WorkOrder"])


def get_work_order_service(session=Depends(get_db_session)) -> WorkOrderService:
    return WorkOrderService(WorkOrderRepository(session))


@router.get("", response_model=WorkOrderListResponse)
async def list_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    order_number: str | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    site_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        order_number=order_number, customer_id=customer_id, site_id=site_id, status=status,
    )
    return WorkOrderListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_work_orders(
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=WorkOrderRead, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    payload: WorkOrderCreate,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=WorkOrderRead)
async def get_work_order(
    entity_id: UUID,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=WorkOrderRead)
async def update_work_order(
    entity_id: UUID,
    payload: WorkOrderUpdate,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_work_order(
    entity_id: UUID,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=WorkOrderRead)
async def restore_work_order(
    entity_id: UUID,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/submit", response_model=WorkOrderRead)
async def submit(
    entity_id: UUID,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    """Transition draft work order to submitted queue"""
    result = await service.submit(entity_id, tenant_id)
    return WorkOrderRead.model_validate(result)

@router.post("/{entity_id}/assign-technician", response_model=WorkOrderRead)
async def assign_technician(
    entity_id: UUID,
    payload: WorkOrderAssignTechnicianRequest,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    """Assign technician with conflict check"""
    result = await service.assign_technician(entity_id, tenant_id, technician_id=payload.technician_id)
    return WorkOrderRead.model_validate(result)

@router.post("/{entity_id}/start", response_model=WorkOrderRead)
async def start(
    entity_id: UUID,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    """Mark work order in progress"""
    result = await service.start(entity_id, tenant_id)
    return WorkOrderRead.model_validate(result)

@router.post("/{entity_id}/complete", response_model=WorkOrderRead)
async def complete(
    entity_id: UUID,
    payload: WorkOrderCompleteRequest,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    """Complete work order with notes"""
    result = await service.complete(entity_id, tenant_id, notes=payload.notes)
    return WorkOrderRead.model_validate(result)

@router.post("/{entity_id}/cancel", response_model=WorkOrderRead)
async def cancel(
    entity_id: UUID,
    payload: WorkOrderCancelRequest,
    service: WorkOrderService = Depends(get_work_order_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderRead:
    """Cancel with reason"""
    result = await service.cancel(entity_id, tenant_id, reason=payload.reason)
    return WorkOrderRead.model_validate(result)
