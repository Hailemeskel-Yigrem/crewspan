"""FastAPI routes for InventoryItem."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.inventory_item.repository import InventoryItemRepository
from app.domains.inventory_item.schemas import (
    InventoryItemCreate,
    InventoryItemListResponse,
    InventoryItemRead,
    InventoryItemUpdate,
)
from app.domains.inventory_item.service import InventoryItemService

router = APIRouter(prefix="/inventory-items", tags=["InventoryItem"])


def get_inventory_item_service(session=Depends(get_db_session)) -> InventoryItemService:
    return InventoryItemService(InventoryItemRepository(session))


@router.get("", response_model=InventoryItemListResponse)
async def list_inventory_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    sku: str | None = Query(default=None),
    name: str | None = Query(default=None),
    category: str | None | None = Query(default=None),
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        sku=sku, name=name, category=category,
    )
    return InventoryItemListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_inventory_items(
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=InventoryItemRead, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: InventoryItemCreate,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=InventoryItemRead)
async def get_inventory_item(
    entity_id: UUID,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=InventoryItemRead)
async def update_inventory_item(
    entity_id: UUID,
    payload: InventoryItemUpdate,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    entity_id: UUID,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> None:
    await service.delete(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/restore", response_model=InventoryItemRead)
async def restore_inventory_item(
    entity_id: UUID,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/adjust-reorder-levels", response_model=InventoryItemRead)
async def adjust_reorder_levels(
    entity_id: UUID,
    payload: InventoryItemAdjustReorderLevelsRequest,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    """Update reorder point and quantity"""
    result = await service.adjust_reorder_levels(entity_id, tenant_id, point=payload.point, quantity=payload.quantity)
    if hasattr(result, "__table__"):
        return InventoryItemRead.model_validate(result)
    return result

@router.post("/{entity_id}/deactivate", response_model=InventoryItemRead)
async def deactivate(
    entity_id: UUID,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    """Mark item inactive"""
    result = await service.deactivate(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return InventoryItemRead.model_validate(result)
    return result

@router.get("/{entity_id}/stock-value", response_model=InventoryItemRead)
async def calculate_stock_value(
    entity_id: UUID,
    service: InventoryItemService = Depends(get_inventory_item_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> InventoryItemRead:
    """Sum stock on hand times unit cost"""
    result = await service.calculate_stock_value(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return InventoryItemRead.model_validate(result)
    return result
