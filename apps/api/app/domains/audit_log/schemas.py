"""Pydantic schemas for AuditLog."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AuditLogBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    actor_id: UUID | None
    action: str
    resource_type: str
    resource_id: UUID | None
    changes: dict[str, object] | None
    ip_address: str | None
    user_agent: str | None


class AuditLogCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    actor_id: UUID | None = Field(None)
    action: str
    resource_type: str
    resource_id: UUID | None = Field(None)
    changes: dict[str, object] | None = Field(None)
    ip_address: str | None = Field(None)
    user_agent: str | None = Field(None)
    @field_validator("action")
    @classmethod
    def validate_action_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("action cannot be blank")
        return stripped

    @field_validator("resource_type")
    @classmethod
    def validate_resource_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("resource_type cannot be blank")
        return stripped


class AuditLogUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    actor_id: UUID | None | None = None
    resource_id: UUID | None | None = None
    changes: dict[str, object] | None | None = None
    ip_address: str | None | None = None
    user_agent: str | None | None = None


class AuditLogRead(AuditLogBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime



class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[AuditLogRead], total: int, page: int, page_size: int) -> "AuditLogListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class AuditLogFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    actor_id: UUID | None | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: UUID | None | None = None


class AuditLogSearchByResourceRequest(BaseModel):
    """Payload for search_by_resource."""
    resource_type: str
    resource_id: UUID
