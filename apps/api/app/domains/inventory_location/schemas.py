"""Pydantic schemas for InventoryLocation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryLocationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    code: str
    name: str
    location_type: str
    technician_id: UUID | None
    address: dict[str, object] | None
    is_active: bool


class InventoryLocationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    code: str
    name: str
    location_type: str = Field('warehouse')
    technician_id: UUID | None = Field(None)
    address: dict[str, object] | None = Field(None)
    is_active: bool = Field(True)
    @field_validator("code")
    @classmethod
    def validate_code_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("code cannot be blank")
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

    @field_validator("location_type")
    @classmethod
    def validate_location_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("location_type cannot be blank")
        return stripped


class InventoryLocationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    location_type: str | None = None
    technician_id: UUID | None | None = None
    address: dict[str, object] | None | None = None
    is_active: bool | None = None


class InventoryLocationRead(InventoryLocationBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class InventoryLocationListResponse(BaseModel):
    items: list[InventoryLocationRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[InventoryLocationRead], total: int, page: int, page_size: int) -> InventoryLocationListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class InventoryLocationFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    code: str | None = None
    technician_id: UUID | None | None = None


class InventoryLocationAssignToTechnicianRequest(BaseModel):
    """Payload for assign_to_technician."""
    technician_id: UUID
