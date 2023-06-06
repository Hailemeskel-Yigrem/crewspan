"""FastAPI routes for Role."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.role.repository import RoleRepository
from app.domains.role.schemas import (
    RoleCreate,
    RoleListResponse,
    RoleRead,
    RoleUpdate,
)
from app.domains.role.service import RoleService

router = APIRouter(prefix="/roles", tags=["Role"])


def get_role_service(session=Depends(get_db_session)) -> RoleService:
    return RoleService(RoleRepository(session))


@router.get("", response_model=RoleListResponse)
async def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    name: str | None = Query(default=None),
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        name=name,
    )
    return RoleListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_roles(
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=RoleRead)
async def get_role(
    entity_id: UUID,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=RoleRead)
async def update_role(
    entity_id: UUID,
    payload: RoleUpdate,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    entity_id: UUID,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> None:
    await service.delete(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/restore", response_model=RoleRead)
async def restore_role(
    entity_id: UUID,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/grant-permission", response_model=RoleRead)
async def grant_permission(
    entity_id: UUID,
    payload: RoleGrantPermissionRequest,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    """Add permission if not already present"""
    result = await service.grant_permission(entity_id, tenant_id, permission=payload.permission)
    if hasattr(result, "__table__"):
        return RoleRead.model_validate(result)
    return result

@router.post("/{entity_id}/revoke-permission", response_model=RoleRead)
async def revoke_permission(
    entity_id: UUID,
    payload: RoleRevokePermissionRequest,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    """Remove permission from role"""
    result = await service.revoke_permission(entity_id, tenant_id, permission=payload.permission)
    if hasattr(result, "__table__"):
        return RoleRead.model_validate(result)
    return result

@router.post("/{entity_id}/clone", response_model=RoleRead, status_code=status.HTTP_201)
async def clone(
    entity_id: UUID,
    payload: RoleCloneRequest,
    service: RoleService = Depends(get_role_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> RoleRead:
    """Duplicate role under a new name"""
    result = await service.clone(entity_id, tenant_id, new_name=payload.new_name)
    if hasattr(result, "__table__"):
        return RoleRead.model_validate(result)
    return result
