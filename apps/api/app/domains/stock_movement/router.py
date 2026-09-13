"""FastAPI routes for StockMovement."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.stock_movement.repository import StockMovementRepository
from app.domains.stock_movement.schemas import (
    StockMovementCreate,
    StockMovementListResponse,
    StockMovementRead,
    StockMovementReverseRequest,
    StockMovementUpdate,
)
from app.domains.stock_movement.service import StockMovementService

router = APIRouter(prefix="/stock-movements", tags=["StockMovement"])


def get_stock_movement_service(session=Depends(get_db_session)) -> StockMovementService:
    return StockMovementService(StockMovementRepository(session))


@router.get("", response_model=StockMovementListResponse)
async def list_stock_movements(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    item_id: UUID | None = Query(default=None),
    from_location_id: UUID | None | None = Query(default=None),
    to_location_id: UUID | None | None = Query(default=None),
    movement_type: str | None = Query(default=None),
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        item_id=item_id, from_location_id=from_location_id, to_location_id=to_location_id, movement_type=movement_type,
    )
    return StockMovementListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_stock_movements(
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=StockMovementRead, status_code=status.HTTP_201_CREATED)
async def create_stock_movement(
    payload: StockMovementCreate,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=StockMovementRead)
async def get_stock_movement(
    entity_id: UUID,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=StockMovementRead)
async def update_stock_movement(
    entity_id: UUID,
    payload: StockMovementUpdate,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_stock_movement(
    entity_id: UUID,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=StockMovementRead)
async def restore_stock_movement(
    entity_id: UUID,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/validate", response_model=StockMovementRead)
async def validate_quantity(
    entity_id: UUID,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementRead:
    """Ensure sufficient stock for issue/transfer"""
    result = await service.validate_quantity(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return StockMovementRead.model_validate(result)
    return result

@router.post("/{entity_id}/reverse", response_model=StockMovementRead)
async def reverse(
    entity_id: UUID,
    payload: StockMovementReverseRequest,
    service: StockMovementService = Depends(get_stock_movement_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> StockMovementRead:
    """Create compensating movement"""
    result = await service.reverse(entity_id, tenant_id, reason=payload.reason)
    if hasattr(result, "__table__"):
        return StockMovementRead.model_validate(result)
    return result
# history-note: evolutionary edit 59
