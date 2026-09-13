"""Pydantic schemas for PartsRequest."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PartsRequestBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    work_order_id: UUID
    requested_by_id: UUID
    status: str
    needed_by: datetime | None
    fulfillment_location_id: UUID | None
    line_items: list[object]
    notes: str | None


class PartsRequestCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    work_order_id: UUID
    requested_by_id: UUID
    status: str = Field('pending')
    needed_by: datetime | None = Field(None)
    fulfillment_location_id: UUID | None = Field(None)
    line_items: list[object] = Field(..., description="Requested parts with quantities")
    notes: str | None = Field(None)
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


class PartsRequestUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    status: str | None = None
    needed_by: datetime | None | None = None
    fulfillment_location_id: UUID | None | None = None
    notes: str | None | None = None


class PartsRequestRead(PartsRequestBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class PartsRequestListResponse(BaseModel):
    items: list[PartsRequestRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[PartsRequestRead], total: int, page: int, page_size: int) -> PartsRequestListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class PartsRequestFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    work_order_id: UUID | None = None
    requested_by_id: UUID | None = None
    status: str | None = None


class PartsRequestRejectRequest(BaseModel):
    """Payload for reject."""
    reason: str
