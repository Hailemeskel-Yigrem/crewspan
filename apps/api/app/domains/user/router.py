"""FastAPI routes for User."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.user.repository import UserRepository
from app.domains.user.schemas import (
    UserChangePasswordRequest,
    UserCreate,
    UserListResponse,
    UserRead,
    UserUpdate,
)
from app.domains.user.service import UserService

router = APIRouter(prefix="/users", tags=["User"])


def get_user_service(session=Depends(get_db_session)) -> UserService:
    return UserService(UserRepository(session))


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    email: str | None = Query(default=None),
    role_id: UUID | None = Query(default=None),
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        email=email, role_id=role_id,
    )
    return UserListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_users(
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=UserRead)
async def get_user(
    entity_id: UUID,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=UserRead)
async def update_user(
    entity_id: UUID,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_user(
    entity_id: UUID,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=UserRead)
async def restore_user(
    entity_id: UUID,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/change-password", response_model=UserRead)
async def change_password(
    entity_id: UUID,
    payload: UserChangePasswordRequest,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    """Validate and rotate user password hash"""
    result = await service.change_password(entity_id, tenant_id, new_password=payload.new_password)
    if hasattr(result, "__table__"):
        return UserRead.model_validate(result)
    return result

@router.post("/{entity_id}/record-login", response_model=UserRead)
async def record_login(
    entity_id: UUID,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    """Update last login timestamp"""
    result = await service.record_login(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return UserRead.model_validate(result)
    return result

@router.post("/{entity_id}/deactivate", response_model=UserRead)
async def deactivate(
    entity_id: UUID,
    service: UserService = Depends(get_user_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> UserRead:
    """Disable user without deleting audit history"""
    result = await service.deactivate(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return UserRead.model_validate(result)
    return result
