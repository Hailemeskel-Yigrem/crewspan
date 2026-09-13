"""FastAPI routes for Equipment."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.equipment.repository import EquipmentRepository
from app.domains.equipment.schemas import (
    EquipmentCreate,
    EquipmentListResponse,
    EquipmentRead,
    EquipmentRecordServiceRequest,
    EquipmentRetireRequest,
    EquipmentUpdate,
)
from app.domains.equipment.service import EquipmentService

router = APIRouter(prefix="/equipments", tags=["Equipment"])


def get_equipment_service(session=Depends(get_db_session)) -> EquipmentService:
    return EquipmentService(EquipmentRepository(session))


@router.get("", response_model=EquipmentListResponse)
async def list_equipments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    customer_id: UUID | None = Query(default=None),
    site_id: UUID | None | None = Query(default=None),
    asset_tag: str | None = Query(default=None),
    serial_number: str | None | None = Query(default=None),
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        customer_id=customer_id, site_id=site_id, asset_tag=asset_tag, serial_number=serial_number,
    )
    return EquipmentListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_equipments(
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    payload: EquipmentCreate,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=EquipmentRead)
async def get_equipment(
    entity_id: UUID,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=EquipmentRead)
async def update_equipment(
    entity_id: UUID,
    payload: EquipmentUpdate,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_equipment(
    entity_id: UUID,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=EquipmentRead)
async def restore_equipment(
    entity_id: UUID,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/record-service", response_model=EquipmentRead)
async def record_service(
    entity_id: UUID,
    payload: EquipmentRecordServiceRequest,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentRead:
    """Log service event on equipment"""
    result = await service.record_service(entity_id, tenant_id, work_order_id=payload.work_order_id, notes=payload.notes)
    return EquipmentRead.model_validate(result)

@router.post("/{entity_id}/retire", response_model=EquipmentRead)
async def retire(
    entity_id: UUID,
    payload: EquipmentRetireRequest,
    service: EquipmentService = Depends(get_equipment_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EquipmentRead:
    """Mark equipment out of service"""
    result = await service.retire(entity_id, tenant_id, reason=payload.reason)
    return EquipmentRead.model_validate(result)
