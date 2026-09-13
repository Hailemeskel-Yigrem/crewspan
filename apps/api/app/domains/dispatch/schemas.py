"""Pydantic schemas for Dispatch."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DispatchBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    work_order_id: UUID
    technician_id: UUID
    dispatched_at: datetime
    accepted_at: datetime | None
    status: str
    dispatch_notes: str | None
    route_eta_minutes: int | None


class DispatchCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    work_order_id: UUID
    technician_id: UUID
    dispatched_at: datetime
    accepted_at: datetime | None = Field(None)
    status: str = Field('pending')
    dispatch_notes: str | None = Field(None)
    route_eta_minutes: int | None = Field(None)
    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {'draft', 'pending', 'active', 'in_progress', 'completed', 'cancelled'}
        if value not in allowed:
            raise ValueError("status must be one of: " + ", ".join(sorted(allowed)))
        return value

    @field_validator("status")
    @classmethod
    def validate_status_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("status cannot be blank")
        return stripped


class DispatchUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    accepted_at: datetime | None | None = None
    status: str | None = None
    dispatch_notes: str | None | None = None
    route_eta_minutes: int | None | None = None


class DispatchRead(DispatchBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class DispatchListResponse(BaseModel):
    items: list[DispatchRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[DispatchRead], total: int, page: int, page_size: int) -> DispatchListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class DispatchFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    work_order_id: UUID | None = None
    technician_id: UUID | None = None
    status: str | None = None


class DispatchDeclineRequest(BaseModel):
    """Payload for decline."""
    reason: str
