"""FastAPI routes for Technician."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_db_session, get_tenant_id
from app.domains.technician.repository import TechnicianRepository
from app.domains.technician.schemas import (
    TechnicianCalculateUtilizationRequest,
    TechnicianCreate,
    TechnicianListResponse,
    TechnicianRead,
    TechnicianSetStatusRequest,
    TechnicianUpdate,
    TechnicianUpdateLocationRequest,
)
from app.domains.technician.service import TechnicianService

router = APIRouter(prefix="/technicians", tags=["Technician"])


def get_technician_service(session=Depends(get_db_session)) -> TechnicianService:
    return TechnicianService(TechnicianRepository(session))


@router.get("", response_model=TechnicianListResponse)
async def list_technicians(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    user_id: UUID | None = Query(default=None),
    employee_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        user_id=user_id, employee_id=employee_id, status=status,
    )
    return TechnicianListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_technicians(
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=TechnicianRead, status_code=status.HTTP_201_CREATED)
async def create_technician(
    payload: TechnicianCreate,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=TechnicianRead)
async def get_technician(
    entity_id: UUID,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=TechnicianRead)
async def update_technician(
    entity_id: UUID,
    payload: TechnicianUpdate,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_technician(
    entity_id: UUID,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=TechnicianRead)
async def restore_technician(
    entity_id: UUID,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/set-status", response_model=TechnicianRead)
async def set_status(
    entity_id: UUID,
    payload: TechnicianSetStatusRequest,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    """Update availability status"""
    result = await service.set_status(entity_id, tenant_id, status=payload.status)
    return TechnicianRead.model_validate(result)

@router.post("/{entity_id}/update-location", response_model=TechnicianRead)
async def update_location(
    entity_id: UUID,
    payload: TechnicianUpdateLocationRequest,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    """Record current GPS coordinates"""
    result = await service.update_location(entity_id, tenant_id, lat=payload.lat, lng=payload.lng)
    return TechnicianRead.model_validate(result)

@router.post("/{entity_id}/calculate-utilization", response_model=TechnicianRead)
async def calculate_utilization(
    entity_id: UUID,
    payload: TechnicianCalculateUtilizationRequest,
    service: TechnicianService = Depends(get_technician_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianRead:
    """Compute utilization for date range"""
    result = await service.calculate_utilization(entity_id, tenant_id, start=payload.start, end=payload.end)
    return TechnicianRead.model_validate(result)
