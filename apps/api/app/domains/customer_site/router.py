"""FastAPI routes for CustomerSite."""

from __future__ import annotations

from uuid import UUID

from fastapi import Response, APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.customer_site.repository import CustomerSiteRepository
from app.domains.customer_site.schemas import (
    CustomerSiteCreate,
    CustomerSiteListResponse,
    CustomerSiteRead,
    CustomerSiteUpdate,
    CustomerSiteValidateAccessWindowRequest,
)
from app.domains.customer_site.service import CustomerSiteService

router = APIRouter(prefix="/customer-sites", tags=["CustomerSite"])


def get_customer_site_service(session=Depends(get_db_session)) -> CustomerSiteService:
    return CustomerSiteService(CustomerSiteRepository(session))


@router.get("", response_model=CustomerSiteListResponse)
async def list_customer_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    customer_id: UUID | None = Query(default=None),
    site_code: str | None = Query(default=None),
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        customer_id=customer_id, site_code=site_code,
    )
    return CustomerSiteListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_customer_sites(
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=CustomerSiteRead, status_code=status.HTTP_201_CREATED)
async def create_customer_site(
    payload: CustomerSiteCreate,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=CustomerSiteRead)
async def get_customer_site(
    entity_id: UUID,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=CustomerSiteRead)
async def update_customer_site(
    entity_id: UUID,
    payload: CustomerSiteUpdate,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_customer_site(
    entity_id: UUID,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    await service.delete(entity_id, tenant_id=tenant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.post("/{entity_id}/restore", response_model=CustomerSiteRead)
async def restore_customer_site(
    entity_id: UUID,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/geocode", response_model=CustomerSiteRead)
async def geocode(
    entity_id: UUID,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteRead:
    """Resolve coordinates from address"""
    result = await service.geocode(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return CustomerSiteRead.model_validate(result)
    return result

@router.post("/{entity_id}/validate-access-window", response_model=CustomerSiteRead)
async def validate_access_window(
    entity_id: UUID,
    payload: CustomerSiteValidateAccessWindowRequest,
    service: CustomerSiteService = Depends(get_customer_site_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> CustomerSiteRead:
    """Check if datetime falls within service window"""
    result = await service.validate_access_window(entity_id, tenant_id, at=payload.at)
    if hasattr(result, "__table__"):
        return CustomerSiteRead.model_validate(result)
    return result
# history-note: evolutionary edit 10
