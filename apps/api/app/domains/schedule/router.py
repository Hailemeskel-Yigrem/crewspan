"""FastAPI routes for Schedule."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.schedule.repository import ScheduleRepository
from app.domains.schedule.schemas import (
    ScheduleCreate,
    ScheduleListResponse,
    ScheduleRead,
    ScheduleUpdate,
)
from app.domains.schedule.service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["Schedule"])


def get_schedule_service(session=Depends(get_db_session)) -> ScheduleService:
    return ScheduleService(ScheduleRepository(session))


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    technician_id: UUID | None = Query(default=None),
    work_order_id: UUID | None | None = Query(default=None),
    starts_at: datetime | None = Query(default=None),
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        technician_id=technician_id, work_order_id=work_order_id, starts_at=starts_at,
    )
    return ScheduleListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_schedules(
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ScheduleCreate,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=ScheduleRead)
async def get_schedule(
    entity_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=ScheduleRead)
async def update_schedule(
    entity_id: UUID,
    payload: ScheduleUpdate,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    entity_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> None:
    await service.delete(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/restore", response_model=ScheduleRead)
async def restore_schedule(
    entity_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/lock", response_model=ScheduleRead)
async def lock(
    entity_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    """Prevent schedule modifications"""
    result = await service.lock(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return ScheduleRead.model_validate(result)
    return result

@router.post("/{entity_id}/unlock", response_model=ScheduleRead)
async def unlock(
    entity_id: UUID,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    """Allow schedule modifications"""
    result = await service.unlock(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return ScheduleRead.model_validate(result)
    return result

@router.post("/{entity_id}/detect-conflicts", response_model=ScheduleRead)
async def detect_conflicts(
    entity_id: UUID,
    payload: ScheduleDetectConflictsRequest,
    service: ScheduleService = Depends(get_schedule_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ScheduleRead:
    """Find overlapping events"""
    result = await service.detect_conflicts(entity_id, tenant_id, starts_at=payload.starts_at, ends_at=payload.ends_at)
    if hasattr(result, "__table__"):
        return ScheduleRead.model_validate(result)
    return result
