"""FastAPI routes for SlaPolicy."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.sla_policy.repository import SlaPolicyRepository
from app.domains.sla_policy.schemas import (
    SlaPolicyCreate,
    SlaPolicyListResponse,
    SlaPolicyRead,
    SlaPolicyUpdate,
)
from app.domains.sla_policy.service import SlaPolicyService

router = APIRouter(prefix="/sla-policies", tags=["SlaPolicy"])


def get_sla_policy_service(session=Depends(get_db_session)) -> SlaPolicyService:
    return SlaPolicyService(SlaPolicyRepository(session))


@router.get("", response_model=SlaPolicyListResponse)
async def list_sla_policies(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    name: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        name=name, priority=priority,
    )
    return SlaPolicyListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_sla_policies(
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=SlaPolicyRead, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    payload: SlaPolicyCreate,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=SlaPolicyRead)
async def get_sla_policy(
    entity_id: UUID,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=SlaPolicyRead)
async def update_sla_policy(
    entity_id: UUID,
    payload: SlaPolicyUpdate,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_sla_policy(
    entity_id: UUID,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=SlaPolicyRead)
async def restore_sla_policy(
    entity_id: UUID,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/evaluate-deadlines", response_model=SlaPolicyRead)
async def evaluate_deadlines(
    entity_id: UUID,
    payload: SlaPolicyEvaluateDeadlinesRequest,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyRead:
    """Compute response/resolution deadlines"""
    result = await service.evaluate_deadlines(entity_id, tenant_id, opened_at=payload.opened_at)
    if hasattr(result, "__table__"):
        return SlaPolicyRead.model_validate(result)
    return result

@router.post("/{entity_id}/clone", response_model=SlaPolicyRead, status_code=status.HTTP_201_CREATED)
async def clone(
    entity_id: UUID,
    payload: SlaPolicyCloneRequest,
    service: SlaPolicyService = Depends(get_sla_policy_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaPolicyRead:
    """Duplicate policy"""
    result = await service.clone(entity_id, tenant_id, new_name=payload.new_name)
    if hasattr(result, "__table__"):
        return SlaPolicyRead.model_validate(result)
    return result
