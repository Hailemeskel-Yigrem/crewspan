"""FastAPI routes for AuditLog."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_db_session, get_tenant_id
from app.domains.audit_log.repository import AuditLogRepository
from app.domains.audit_log.schemas import (
    AuditLogCreate,
    AuditLogListResponse,
    AuditLogRead,
    AuditLogSearchByResourceRequest,
    AuditLogUpdate,
)
from app.domains.audit_log.service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["AuditLog"])


def get_audit_log_service(session=Depends(get_db_session)) -> AuditLogService:
    return AuditLogService(AuditLogRepository(session))


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    actor_id: UUID | None | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: UUID | None | None = Query(default=None),
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> AuditLogListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        actor_id=actor_id, action=action, resource_type=resource_type, resource_id=resource_id,
    )
    return AuditLogListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_audit_logs(
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=AuditLogRead, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    payload: AuditLogCreate,
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> AuditLogRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=AuditLogRead)
async def get_audit_log(
    entity_id: UUID,
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> AuditLogRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=AuditLogRead)
async def update_audit_log(
    entity_id: UUID,
    payload: AuditLogUpdate,
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> AuditLogRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_audit_log(
    entity_id: UUID,
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{entity_id}/by-resource", response_model=AuditLogRead)
async def search_by_resource(
    entity_id: UUID,
    payload: AuditLogSearchByResourceRequest,
    service: AuditLogService = Depends(get_audit_log_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> AuditLogRead:
    """Find audit entries for resource"""
    result = await service.search_by_resource(entity_id, tenant_id, resource_type=payload.resource_type, resource_id=payload.resource_id)
    return AuditLogRead.model_validate(result)
