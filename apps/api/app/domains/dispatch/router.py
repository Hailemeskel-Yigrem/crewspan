"""FastAPI routes for Dispatch."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_db_session, get_tenant_id
from app.domains.dispatch.repository import DispatchRepository
from app.domains.dispatch.schemas import (
    DispatchCreate,
    DispatchDeclineRequest,
    DispatchListResponse,
    DispatchRead,
    DispatchUpdate,
)
from app.domains.dispatch.service import DispatchService

router = APIRouter(prefix="/dispatchs", tags=["Dispatch"])


def get_dispatch_service(session=Depends(get_db_session)) -> DispatchService:
    return DispatchService(DispatchRepository(session))


@router.get("", response_model=DispatchListResponse)
async def list_dispatchs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    work_order_id: UUID | None = Query(default=None),
    technician_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        work_order_id=work_order_id, technician_id=technician_id, status=status,
    )
    return DispatchListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_dispatchs(
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=DispatchRead, status_code=status.HTTP_201_CREATED)
async def create_dispatch(
    payload: DispatchCreate,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=DispatchRead)
async def get_dispatch(
    entity_id: UUID,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=DispatchRead)
async def update_dispatch(
    entity_id: UUID,
    payload: DispatchUpdate,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_dispatch(
    entity_id: UUID,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=DispatchRead)
async def restore_dispatch(
    entity_id: UUID,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/accept", response_model=DispatchRead)
async def accept(
    entity_id: UUID,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    """Technician accepts dispatch"""
    result = await service.accept(entity_id, tenant_id)
    return DispatchRead.model_validate(result)

@router.post("/{entity_id}/decline", response_model=DispatchRead)
async def decline(
    entity_id: UUID,
    payload: DispatchDeclineRequest,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    """Technician declines with reason"""
    result = await service.decline(entity_id, tenant_id, reason=payload.reason)
    return DispatchRead.model_validate(result)

@router.post("/{entity_id}/en-route", response_model=DispatchRead)
async def en_route(
    entity_id: UUID,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    """Mark technician en route"""
    result = await service.en_route(entity_id, tenant_id)
    return DispatchRead.model_validate(result)

@router.post("/{entity_id}/arrive", response_model=DispatchRead)
async def arrive(
    entity_id: UUID,
    service: DispatchService = Depends(get_dispatch_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DispatchRead:
    """Record on-site arrival"""
    result = await service.arrive(entity_id, tenant_id)
    return DispatchRead.model_validate(result)
