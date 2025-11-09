"""FastAPI routes for WorkOrderTask."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.work_order_task.repository import WorkOrderTaskRepository
from app.domains.work_order_task.schemas import (
    WorkOrderTaskCreate,
    WorkOrderTaskListResponse,
    WorkOrderTaskRead,
    WorkOrderTaskUpdate,
)
from app.domains.work_order_task.service import WorkOrderTaskService

router = APIRouter(prefix="/work-order-tasks", tags=["WorkOrderTask"])


def get_work_order_task_service(session=Depends(get_db_session)) -> WorkOrderTaskService:
    return WorkOrderTaskService(WorkOrderTaskRepository(session))


@router.get("", response_model=WorkOrderTaskListResponse)
async def list_work_order_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    work_order_id: UUID | None = Query(default=None),
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        work_order_id=work_order_id,
    )
    return WorkOrderTaskListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_work_order_tasks(
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=WorkOrderTaskRead, status_code=status.HTTP_201_CREATED)
async def create_work_order_task(
    payload: WorkOrderTaskCreate,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=WorkOrderTaskRead)
async def get_work_order_task(
    entity_id: UUID,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=WorkOrderTaskRead)
async def update_work_order_task(
    entity_id: UUID,
    payload: WorkOrderTaskUpdate,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_order_task(
    entity_id: UUID,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> None:
    await service.delete(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/restore", response_model=WorkOrderTaskRead)
async def restore_work_order_task(
    entity_id: UUID,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/complete", response_model=WorkOrderTaskRead)
async def complete(
    entity_id: UUID,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    """Mark task completed"""
    result = await service.complete(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return WorkOrderTaskRead.model_validate(result)
    return result

@router.post("/{entity_id}/reopen", response_model=WorkOrderTaskRead)
async def reopen(
    entity_id: UUID,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    """Revert completed task to pending"""
    result = await service.reopen(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return WorkOrderTaskRead.model_validate(result)
    return result

@router.patch("/{entity_id}/reorder", response_model=WorkOrderTaskRead)
async def reorder(
    entity_id: UUID,
    payload: WorkOrderTaskReorderRequest,
    service: WorkOrderTaskService = Depends(get_work_order_task_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WorkOrderTaskRead:
    """Change task sequence"""
    result = await service.reorder(entity_id, tenant_id, sequence=payload.sequence)
    if hasattr(result, "__table__"):
        return WorkOrderTaskRead.model_validate(result)
    return result
# history-note: evolutionary edit 45
