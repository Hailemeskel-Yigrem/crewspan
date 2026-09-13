"""FastAPI routes for InventoryLocation."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_db_session, get_tenant_id
from app.domains.inventory_location.repository import InventoryLocationRepository
from app.domains.inventory_location.schemas import (
    InventoryLocationAssignToTechnicianRequest,
    InventoryLocationCreate,
    InventoryLocationListResponse,
    InventoryLocationRead,
    InventoryLocationUpdate,
)
from app.domains.inventory_location.service import InventoryLocationService

router = APIRouter(prefix="/inventory-locations", tags=["InventoryLocation"])


def get_inventory_location_service(session=Depends(get_db_session)) -> InventoryLocationService:
    return InventoryLocationService(InventoryLocationRepository(session))


@router.get("", response_model=InventoryLocationListResponse)
async def list_inventory_locations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    code: str | None = Query(default=None),
    technician_id: UUID | None | None = Query(default=None),
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        code=code, technician_id=technician_id,
    )
    return InventoryLocationListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_inventory_locations(
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=InventoryLocationRead, status_code=status.HTTP_201_CREATED)
async def create_inventory_location(
    payload: InventoryLocationCreate,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=InventoryLocationRead)
async def get_inventory_location(
    entity_id: UUID,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=InventoryLocationRead)
async def update_inventory_location(
    entity_id: UUID,
    payload: InventoryLocationUpdate,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_inventory_location(
    entity_id: UUID,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=InventoryLocationRead)
async def restore_inventory_location(
    entity_id: UUID,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/assign-to-technician", response_model=InventoryLocationRead)
async def assign_to_technician(
    entity_id: UUID,
    payload: InventoryLocationAssignToTechnicianRequest,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationRead:
    """Link location to technician van stock"""
    result = await service.assign_to_technician(entity_id, tenant_id, technician_id=payload.technician_id)
    return InventoryLocationRead.model_validate(result)

@router.get("/{entity_id}/low-stock", response_model=InventoryLocationRead)
async def list_low_stock(
    entity_id: UUID,
    service: InventoryLocationService = Depends(get_inventory_location_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryLocationRead:
    """Return items below reorder point at location"""
    result = await service.list_low_stock(entity_id, tenant_id)
    return InventoryLocationRead.model_validate(result)
