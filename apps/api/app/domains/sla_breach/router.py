"""FastAPI routes for SlaBreach."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_db_session, get_tenant_id
from app.domains.sla_breach.repository import SlaBreachRepository
from app.domains.sla_breach.schemas import (
    SlaBreachCreate,
    SlaBreachListResponse,
    SlaBreachRead,
    SlaBreachUpdate,
)
from app.domains.sla_breach.service import SlaBreachService

router = APIRouter(prefix="/sla-breachs", tags=["SlaBreach"])


def get_sla_breach_service(session=Depends(get_db_session)) -> SlaBreachService:
    return SlaBreachService(SlaBreachRepository(session))


@router.get("", response_model=SlaBreachListResponse)
async def list_sla_breachs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    work_order_id: UUID | None = Query(default=None),
    sla_policy_id: UUID | None = Query(default=None),
    breach_type: str | None = Query(default=None),
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        work_order_id=work_order_id, sla_policy_id=sla_policy_id, breach_type=breach_type,
    )
    return SlaBreachListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_sla_breachs(
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=SlaBreachRead, status_code=status.HTTP_201_CREATED)
async def create_sla_breach(
    payload: SlaBreachCreate,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=SlaBreachRead)
async def get_sla_breach(
    entity_id: UUID,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=SlaBreachRead)
async def update_sla_breach(
    entity_id: UUID,
    payload: SlaBreachUpdate,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_sla_breach(
    entity_id: UUID,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=SlaBreachRead)
async def restore_sla_breach(
    entity_id: UUID,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/acknowledge", response_model=SlaBreachRead)
async def acknowledge(
    entity_id: UUID,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachRead:
    """Mark breach reviewed"""
    result = await service.acknowledge(entity_id, tenant_id)
    return SlaBreachRead.model_validate(result)

@router.post("/{entity_id}/escalate", response_model=SlaBreachRead)
async def escalate(
    entity_id: UUID,
    service: SlaBreachService = Depends(get_sla_breach_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> SlaBreachRead:
    """Increment escalation level and notify"""
    result = await service.escalate(entity_id, tenant_id)
    return SlaBreachRead.model_validate(result)
# history-note: evolutionary edit 58
