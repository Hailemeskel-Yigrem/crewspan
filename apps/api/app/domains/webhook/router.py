"""FastAPI routes for Webhook."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.webhook.repository import WebhookRepository
from app.domains.webhook.schemas import (
    WebhookCreate,
    WebhookDisableOnFailuresRequest,
    WebhookListResponse,
    WebhookRead,
    WebhookUpdate,
)
from app.domains.webhook.service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhook"])


def get_webhook_service(session=Depends(get_db_session)) -> WebhookService:
    return WebhookService(WebhookRepository(session))


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
    )
    return WebhookListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_webhooks(
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: WebhookCreate,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=WebhookRead)
async def get_webhook(
    entity_id: UUID,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=WebhookRead)
async def update_webhook(
    entity_id: UUID,
    payload: WebhookUpdate,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_webhook(
    entity_id: UUID,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=WebhookRead)
async def restore_webhook(
    entity_id: UUID,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/test", response_model=WebhookRead)
async def trigger_test(
    entity_id: UUID,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    """Send test payload"""
    result = await service.trigger_test(entity_id, tenant_id)
    return WebhookRead.model_validate(result)

@router.post("/{entity_id}/rotate-secret", response_model=WebhookRead)
async def rotate_secret(
    entity_id: UUID,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    """Generate new signing secret"""
    result = await service.rotate_secret(entity_id, tenant_id)
    return WebhookRead.model_validate(result)

@router.post("/{entity_id}/disable-on-failures", response_model=WebhookRead)
async def disable_on_failures(
    entity_id: UUID,
    payload: WebhookDisableOnFailuresRequest,
    service: WebhookService = Depends(get_webhook_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> WebhookRead:
    """Auto-disable after threshold"""
    result = await service.disable_on_failures(entity_id, tenant_id, threshold=payload.threshold)
    return WebhookRead.model_validate(result)
