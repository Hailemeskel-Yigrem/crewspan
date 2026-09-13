"""FastAPI routes for PartsRequest."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.parts_request.repository import PartsRequestRepository
from app.domains.parts_request.schemas import (
    PartsRequestCreate,
    PartsRequestListResponse,
    PartsRequestRead,
    PartsRequestRejectRequest,
    PartsRequestUpdate,
)
from app.domains.parts_request.service import PartsRequestService

router = APIRouter(prefix="/parts-requests", tags=["PartsRequest"])


def get_parts_request_service(session=Depends(get_db_session)) -> PartsRequestService:
    return PartsRequestService(PartsRequestRepository(session))


@router.get("", response_model=PartsRequestListResponse)
async def list_parts_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    work_order_id: UUID | None = Query(default=None),
    requested_by_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        work_order_id=work_order_id, requested_by_id=requested_by_id, status=status,
    )
    return PartsRequestListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_parts_requests(
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=PartsRequestRead, status_code=status.HTTP_201_CREATED)
async def create_parts_request(
    payload: PartsRequestCreate,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=PartsRequestRead)
async def get_parts_request(
    entity_id: UUID,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=PartsRequestRead)
async def update_parts_request(
    entity_id: UUID,
    payload: PartsRequestUpdate,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_parts_request(
    entity_id: UUID,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=PartsRequestRead)
async def restore_parts_request(
    entity_id: UUID,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/approve", response_model=PartsRequestRead)
async def approve(
    entity_id: UUID,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    """Approve parts request"""
    result = await service.approve(entity_id, tenant_id)
    return PartsRequestRead.model_validate(result)

@router.post("/{entity_id}/fulfill", response_model=PartsRequestRead)
async def fulfill(
    entity_id: UUID,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    """Issue parts and update inventory"""
    result = await service.fulfill(entity_id, tenant_id)
    return PartsRequestRead.model_validate(result)

@router.post("/{entity_id}/reject", response_model=PartsRequestRead)
async def reject(
    entity_id: UUID,
    payload: PartsRequestRejectRequest,
    service: PartsRequestService = Depends(get_parts_request_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> PartsRequestRead:
    """Reject with reason"""
    result = await service.reject(entity_id, tenant_id, reason=payload.reason)
    return PartsRequestRead.model_validate(result)
