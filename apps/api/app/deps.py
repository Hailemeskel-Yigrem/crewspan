"""FastAPI dependency providers for DB sessions, auth, and tenant context."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id, get_optional_user_id
from app.db import get_session


async def get_db_session(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> UUID:
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id header is required",
        )
    try:
        return UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant id format",
        ) from exc


async def get_optional_tenant_id(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> UUID | None:
    if not x_tenant_id:
        return None
    try:
        return UUID(x_tenant_id)
    except ValueError:
        return None


TenantId = Annotated[UUID, Depends(get_tenant_id)]


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    tenant_id: UUID = Depends(get_tenant_id),
) -> dict[str, UUID]:
    return {"user_id": user_id, "tenant_id": tenant_id}


async def get_request_context(
    user_id: UUID | None = Depends(get_optional_user_id),
    tenant_id: UUID | None = Depends(get_optional_tenant_id),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> dict[str, object]:
    return {
        "user_id": str(user_id) if user_id else None,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "request_id": x_request_id,
    }
