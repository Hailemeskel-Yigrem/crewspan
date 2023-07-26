"""Pydantic schemas for Schedule."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScheduleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    technician_id: UUID
    work_order_id: UUID | None
    event_type: str
    starts_at: datetime
    ends_at: datetime
    title: str
    notes: str | None
    is_locked: bool


class ScheduleCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    technician_id: UUID
    work_order_id: UUID | None = Field(None)
    event_type: str = Field('appointment')
    starts_at: datetime
    ends_at: datetime
    title: str
    notes: str | None = Field(None)
    is_locked: bool = Field(False)
    @field_validator("event_type")
    @classmethod
    def validate_event_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("event_type cannot be blank")
        return stripped

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        return stripped

    @model_validator(mode="after")
    def validate_starts_at_ends_at_ordering(self) -> "ScheduleCreate":
        start = getattr(self, "starts_at", None)
        end = getattr(self, "ends_at", None)
        if start is not None and end is not None and end < start:
            raise ValueError("ends_at must be on or after starts_at")
        return self


class ScheduleUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    work_order_id: UUID | None | None = None
    event_type: str | None = None
    notes: str | None | None = None
    is_locked: bool | None = None


class ScheduleRead(ScheduleBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ScheduleListResponse(BaseModel):
    items: list[ScheduleRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[ScheduleRead], total: int, page: int, page_size: int) -> "ScheduleListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class ScheduleFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    technician_id: UUID | None = None
    work_order_id: UUID | None | None = None
    starts_at: datetime | None = None


class ScheduleDetectConflictsRequest(BaseModel):
    """Payload for detect_conflicts."""
    starts_at: datetime
ends_at: datetime
