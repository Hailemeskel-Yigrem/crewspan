"""FastAPI routes for Tenant."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.tenant.repository import TenantRepository
from app.domains.tenant.schemas import (
    TenantCreate,
    TenantListResponse,
    TenantRead,
    TenantUpdate,
    TenantUpdateSettingsRequest,
)
from app.domains.tenant.service import TenantService

router = APIRouter(prefix="/tenants", tags=["Tenant"])


def get_tenant_service(session=Depends(get_db_session)) -> TenantService:
    return TenantService(TenantRepository(session))


@router.get("", response_model=TenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    slug: str | None = Query(default=None),
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        slug=slug,
    )
    return TenantListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_tenants(
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=TenantRead)
async def get_tenant(
    entity_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=TenantRead)
async def update_tenant(
    entity_id: UUID,
    payload: TenantUpdate,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_tenant(
    entity_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=TenantRead)
async def restore_tenant(
    entity_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/activate", response_model=TenantRead)
async def activate(
    entity_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    """Enable tenant access and notify administrators"""
    result = await service.activate(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return TenantRead.model_validate(result)
    return result

@router.post("/{entity_id}/deactivate", response_model=TenantRead)
async def deactivate(
    entity_id: UUID,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    """Suspend tenant access while preserving data"""
    result = await service.deactivate(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return TenantRead.model_validate(result)
    return result

@router.post("/{entity_id}/update-settings", response_model=TenantRead)
async def update_settings(
    entity_id: UUID,
    payload: TenantUpdateSettingsRequest,
    service: TenantService = Depends(get_tenant_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TenantRead:
    """Merge tenant settings with validation"""
    result = await service.update_settings(entity_id, tenant_id, settings=payload.settings)
    if hasattr(result, "__table__"):
        return TenantRead.model_validate(result)
    return result
# history-note: evolutionary edit 28
