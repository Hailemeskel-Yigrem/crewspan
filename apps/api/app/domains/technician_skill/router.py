"""FastAPI routes for TechnicianSkill."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.technician_skill.repository import TechnicianSkillRepository
from app.domains.technician_skill.schemas import (
    TechnicianSkillCreate,
    TechnicianSkillListResponse,
    TechnicianSkillRead,
    TechnicianSkillRenewCertificationRequest,
    TechnicianSkillUpdate,
)
from app.domains.technician_skill.service import TechnicianSkillService

router = APIRouter(prefix="/technician-skills", tags=["TechnicianSkill"])


def get_technician_skill_service(session=Depends(get_db_session)) -> TechnicianSkillService:
    return TechnicianSkillService(TechnicianSkillRepository(session))


@router.get("", response_model=TechnicianSkillListResponse)
async def list_technician_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    technician_id: UUID | None = Query(default=None),
    skill_code: str | None = Query(default=None),
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        technician_id=technician_id, skill_code=skill_code,
    )
    return TechnicianSkillListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_technician_skills(
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=TechnicianSkillRead, status_code=status.HTTP_201_CREATED)
async def create_technician_skill(
    payload: TechnicianSkillCreate,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=TechnicianSkillRead)
async def get_technician_skill(
    entity_id: UUID,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=TechnicianSkillRead)
async def update_technician_skill(
    entity_id: UUID,
    payload: TechnicianSkillUpdate,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_technician_skill(
    entity_id: UUID,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=TechnicianSkillRead)
async def restore_technician_skill(
    entity_id: UUID,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/renew-certification", response_model=TechnicianSkillRead)
async def renew_certification(
    entity_id: UUID,
    payload: TechnicianSkillRenewCertificationRequest,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillRead:
    """Extend certification expiry"""
    result = await service.renew_certification(entity_id, tenant_id, expires_at=payload.expires_at)
    return TechnicianSkillRead.model_validate(result)

@router.get("/{entity_id}/is-valid", response_model=TechnicianSkillRead)
async def is_valid(
    entity_id: UUID,
    service: TechnicianSkillService = Depends(get_technician_skill_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> TechnicianSkillRead:
    """Check certification not expired"""
    result = await service.is_valid(entity_id, tenant_id)
    return TechnicianSkillRead.model_validate(result)
