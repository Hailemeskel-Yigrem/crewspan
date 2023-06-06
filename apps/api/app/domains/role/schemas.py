"""Pydantic schemas for Role."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    name: str
    description: str | None
    permissions: list[object]
    is_system: bool


class RoleCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., description="Role identifier within tenant")
    description: str | None = Field(None, description="Role purpose summary")
    permissions: list[object] = Field(..., description="Granted permission keys")
    is_system: bool = Field(False, description="Built-in role that cannot be deleted")
    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class RoleUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str | None | None = None
    is_system: bool | None = None


class RoleRead(RoleBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class RoleListResponse(BaseModel):
    items: list[RoleRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[RoleRead], total: int, page: int, page_size: int) -> "RoleListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class RoleFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    name: str | None = None


class RoleGrantPermissionRequest(BaseModel):
    """Payload for grant_permission."""
    permission: str

class RoleRevokePermissionRequest(BaseModel):
    """Payload for revoke_permission."""
    permission: str

class RoleCloneRequest(BaseModel):
    """Payload for clone."""
    new_name: str
