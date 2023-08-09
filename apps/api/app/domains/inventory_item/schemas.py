"""Pydantic schemas for InventoryItem."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InventoryItemBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    sku: str
    name: str
    description: str | None
    unit_of_measure: str
    unit_cost: Decimal
    reorder_point: int
    reorder_quantity: int
    is_active: bool
    category: str | None


class InventoryItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sku: str
    name: str
    description: str | None = Field(None)
    unit_of_measure: str = Field('each')
    unit_cost: Decimal = Field(0)
    reorder_point: int = Field(0)
    reorder_quantity: int = Field(0)
    is_active: bool = Field(True)
    category: str | None = Field(None)
    @field_validator("sku")
    @classmethod
    def validate_sku_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("sku cannot be blank")
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

    @field_validator("unit_of_measure")
    @classmethod
    def validate_unit_of_measure_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("unit_of_measure cannot be blank")
        return stripped


class InventoryItemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str | None | None = None
    unit_of_measure: str | None = None
    unit_cost: Decimal | None = None
    reorder_point: int | None = None
    reorder_quantity: int | None = None
    is_active: bool | None = None
    category: str | None | None = None


class InventoryItemRead(InventoryItemBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class InventoryItemListResponse(BaseModel):
    items: list[InventoryItemRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[InventoryItemRead], total: int, page: int, page_size: int) -> "InventoryItemListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class InventoryItemFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    sku: str | None = None
    name: str | None = None
    category: str | None | None = None


class InventoryItemAdjustReorderLevelsRequest(BaseModel):
    """Payload for adjust_reorder_levels."""
    point: int
quantity: int
