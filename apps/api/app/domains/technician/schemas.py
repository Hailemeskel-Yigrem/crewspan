"""Pydantic schemas for Technician."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re


class TechnicianBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    user_id: UUID
    employee_id: str
    home_base_latitude: Decimal | None
    home_base_longitude: Decimal | None
    max_daily_hours: int
    status: str
    certifications: list[object] | None
    vehicle_info: dict[str, object] | None


class TechnicianCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    user_id: UUID
    employee_id: str
    home_base_latitude: Decimal | None = Field(None)
    home_base_longitude: Decimal | None = Field(None)
    max_daily_hours: int = Field(8)
    status: str = Field('available')
    certifications: list[object] | None = Field(None)
    vehicle_info: dict[str, object] | None = Field(None)
    @field_validator("employee_id")
    @classmethod
    def validate_employee_id_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("employee_id cannot be blank")
        return stripped

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


class TechnicianUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    home_base_latitude: Decimal | None | None = None
    home_base_longitude: Decimal | None | None = None
    max_daily_hours: int | None = None
    status: str | None = None
    certifications: list[object] | None | None = None
    vehicle_info: dict[str, object] | None | None = None


class TechnicianRead(TechnicianBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class TechnicianListResponse(BaseModel):
    items: list[TechnicianRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[TechnicianRead], total: int, page: int, page_size: int) -> "TechnicianListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class TechnicianFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    user_id: UUID | None = None
    employee_id: str | None = None
    status: str | None = None


class TechnicianSetStatusRequest(BaseModel):
    """Payload for set_status."""
    status: str

class TechnicianUpdateLocationRequest(BaseModel):
    """Payload for update_location."""
    lat: Decimal
lng: Decimal

class TechnicianCalculateUtilizationRequest(BaseModel):
    """Payload for calculate_utilization."""
    start: date
end: date
