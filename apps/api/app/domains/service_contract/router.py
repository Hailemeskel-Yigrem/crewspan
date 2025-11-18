"""FastAPI routes for ServiceContract."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.deps import get_db_session, get_tenant_id
from app.domains.service_contract.repository import ServiceContractRepository
from app.domains.service_contract.schemas import (
    ServiceContractCreate,
    ServiceContractListResponse,
    ServiceContractRead,
    ServiceContractUpdate,
)
from app.domains.service_contract.service import ServiceContractService

router = APIRouter(prefix="/service-contracts", tags=["ServiceContract"])


def get_service_contract_service(session=Depends(get_db_session)) -> ServiceContractService:
    return ServiceContractService(ServiceContractRepository(session))


@router.get("", response_model=ServiceContractListResponse)
async def list_service_contracts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(default=None, min_length=1, max_length=200),
    order_by: str = Query(default="created_at"),
    order_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    customer_id: UUID | None = Query(default=None),
    contract_number: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractListResponse:
    items, total = await service.list(
        tenant_id=tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        order_dir=order_dir,
        customer_id=customer_id, contract_number=contract_number, status=status,
    )
    return ServiceContractListResponse.from_page(items, total, page, page_size)


@router.get("/count")
async def count_service_contracts(
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, int]:
    total = await service.count(tenant_id=tenant_id)
    return {"total": total}


@router.post("", response_model=ServiceContractRead, status_code=status.HTTP_201_CREATED)
async def create_service_contract(
    payload: ServiceContractCreate,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    return await service.create(payload, tenant_id=tenant_id)


@router.get("/{entity_id}", response_model=ServiceContractRead)
async def get_service_contract(
    entity_id: UUID,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    return await service.get(entity_id, tenant_id=tenant_id)


@router.patch("/{entity_id}", response_model=ServiceContractRead)
async def update_service_contract(
    entity_id: UUID,
    payload: ServiceContractUpdate,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    return await service.update(entity_id, payload, tenant_id=tenant_id)


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_contract(
    entity_id: UUID,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> None:
    await service.delete(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/restore", response_model=ServiceContractRead)
async def restore_service_contract(
    entity_id: UUID,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    return await service.restore(entity_id, tenant_id=tenant_id)
@router.post("/{entity_id}/renew", response_model=ServiceContractRead)
async def renew(
    entity_id: UUID,
    payload: ServiceContractRenewRequest,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    """Extend contract end date"""
    result = await service.renew(entity_id, tenant_id, new_end_date=payload.new_end_date)
    if hasattr(result, "__table__"):
        return ServiceContractRead.model_validate(result)
    return result

@router.post("/{entity_id}/terminate", response_model=ServiceContractRead)
async def terminate(
    entity_id: UUID,
    payload: ServiceContractTerminateRequest,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    """End contract early"""
    result = await service.terminate(entity_id, tenant_id, reason=payload.reason)
    if hasattr(result, "__table__"):
        return ServiceContractRead.model_validate(result)
    return result

@router.post("/{entity_id}/generate-work-orders", response_model=ServiceContractRead)
async def generate_work_orders(
    entity_id: UUID,
    service: ServiceContractService = Depends(get_service_contract_service),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ServiceContractRead:
    """Create preventive maintenance work orders"""
    result = await service.generate_work_orders(entity_id, tenant_id)
    if hasattr(result, "__table__"):
        return ServiceContractRead.model_validate(result)
    return result
# history-note: evolutionary edit 47
