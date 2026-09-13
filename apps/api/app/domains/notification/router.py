"""FastAPI routes for Notification."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.notification.repository import NotificationRepository
from app.domains.notification.schemas import (
    NotificationCreate,
    NotificationListResponse,
    NotificationMarkFailedRequest,
    NotificationRead,
    NotificationUpdate,
)
from app.domains.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notification"])


def get_notification_service(session=Depends(get_db_session)) -> NotificationService:
    return NotificationService(NotificationRepository(session))


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    recipient_id: UUID | None | None = Query(default=None),
    channel: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        recipient_id=recipient_id, channel=channel, status=status,
    )
    return NotificationListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_notifications(
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: NotificationCreate,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=NotificationRead)
async def get_notification(
    entity_id: UUID,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=NotificationRead)
async def update_notification(
    entity_id: UUID,
    payload: NotificationUpdate,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_notification(
    entity_id: UUID,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=NotificationRead)
async def restore_notification(
    entity_id: UUID,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/mark-sent", response_model=NotificationRead)
async def mark_sent(
    entity_id: UUID,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    """Record successful delivery"""
    result = await service.mark_sent(entity_id, tenant_id)
    return NotificationRead.model_validate(result)

@router.post("/{entity_id}/mark-failed", response_model=NotificationRead)
async def mark_failed(
    entity_id: UUID,
    payload: NotificationMarkFailedRequest,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    """Record delivery failure"""
    result = await service.mark_failed(entity_id, tenant_id, error=payload.error)
    return NotificationRead.model_validate(result)

@router.post("/{entity_id}/retry", response_model=NotificationRead)
async def retry(
    entity_id: UUID,
    service: NotificationService = Depends(get_notification_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> NotificationRead:
    """Requeue failed notification"""
    result = await service.retry(entity_id, tenant_id)
    return NotificationRead.model_validate(result)
# history-note: evolutionary edit 55
