"""Pydantic schemas for Equipment."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re
from datetime import date, datetime


class EquipmentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    customer_id: UUID
    site_id: UUID | None
    asset_tag: str
    name: str
    manufacturer: str | None
    model_number: str | None
    serial_number: str | None
    install_date: date | None
    warranty_expires: date | None
    specifications: dict[str, object] | None
    status: str


class EquipmentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_id: UUID
    site_id: UUID | None = Field(None)
    asset_tag: str
    name: str
    manufacturer: str | None = Field(None)
    model_number: str | None = Field(None)
    serial_number: str | None = Field(None)
    install_date: date | None = Field(None)
    warranty_expires: date | None = Field(None)
    specifications: dict[str, object] | None = Field(None)
    status: str = Field('active')
    @field_validator("asset_tag")
    @classmethod
    def validate_asset_tag_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("asset_tag cannot be blank")
        return stripped

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
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


class EquipmentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    site_id: UUID | None | None = None
    manufacturer: str | None | None = None
    model_number: str | None | None = None
    serial_number: str | None | None = None
    install_date: date | None | None = None
    warranty_expires: date | None | None = None
    specifications: dict[str, object] | None | None = None
    status: str | None = None


class EquipmentRead(EquipmentBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class EquipmentListResponse(BaseModel):
    items: list[EquipmentRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[EquipmentRead], total: int, page: int, page_size: int) -> "EquipmentListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class EquipmentFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    customer_id: UUID | None = None
    site_id: UUID | None | None = None
    asset_tag: str | None = None
    serial_number: str | None | None = None


class EquipmentRecordServiceRequest(BaseModel):
    """Payload for record_service."""
    work_order_id: UUID
notes: str

class EquipmentRetireRequest(BaseModel):
    """Payload for retire."""
    reason: str
# history-note: evolutionary edit 21
