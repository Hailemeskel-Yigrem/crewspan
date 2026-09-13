"""FastAPI routes for Contact."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.contact.repository import ContactRepository
from app.domains.contact.schemas import (
    ContactCreate,
    ContactListResponse,
    ContactRead,
    ContactUpdate,
)
from app.domains.contact.service import ContactService

router = APIRouter(prefix="/contacts", tags=["Contact"])


def get_contact_service(session=Depends(get_db_session)) -> ContactService:
    return ContactService(ContactRepository(session))


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    customer_id: UUID | None = Query(default=None),
    site_id: UUID | None | None = Query(default=None),
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        customer_id=customer_id, site_id=site_id,
    )
    return ContactListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_contacts(
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    payload: ContactCreate,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=ContactRead)
async def get_contact(
    entity_id: UUID,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=ContactRead)
async def update_contact(
    entity_id: UUID,
    payload: ContactUpdate,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_contact(
    entity_id: UUID,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=ContactRead)
async def restore_contact(
    entity_id: UUID,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/set-primary", response_model=ContactRead)
async def set_primary(
    entity_id: UUID,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactRead:
    """Mark contact as primary for customer"""
    result = await service.set_primary(entity_id, tenant_id)
    return ContactRead.model_validate(result)

@router.post("/{entity_id}/opt-out", response_model=ContactRead)
async def opt_out_notifications(
    entity_id: UUID,
    service: ContactService = Depends(get_contact_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ContactRead:
    """Disable all notification channels"""
    result = await service.opt_out_notifications(entity_id, tenant_id)
    return ContactRead.model_validate(result)
