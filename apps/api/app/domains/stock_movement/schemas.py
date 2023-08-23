"""Pydantic schemas for StockMovement."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StockMovementBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    item_id: UUID
    from_location_id: UUID | None
    to_location_id: UUID | None
    quantity: Decimal
    movement_type: str
    reference_type: str | None
    reference_id: UUID | None
    performed_by_id: UUID | None
    notes: str | None


class StockMovementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    item_id: UUID
    from_location_id: UUID | None = Field(None)
    to_location_id: UUID | None = Field(None)
    quantity: Decimal
    movement_type: str
    reference_type: str | None = Field(None)
    reference_id: UUID | None = Field(None)
    performed_by_id: UUID | None = Field(None)
    notes: str | None = Field(None)
    @field_validator("movement_type")
    @classmethod
    def validate_movement_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("movement_type cannot be blank")
        return stripped


class StockMovementUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    from_location_id: UUID | None | None = None
    to_location_id: UUID | None | None = None
    reference_type: str | None | None = None
    reference_id: UUID | None | None = None
    performed_by_id: UUID | None | None = None
    notes: str | None | None = None


class StockMovementRead(StockMovementBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class StockMovementListResponse(BaseModel):
    items: list[StockMovementRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[StockMovementRead], total: int, page: int, page_size: int) -> "StockMovementListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class StockMovementFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    item_id: UUID | None = None
    from_location_id: UUID | None | None = None
    to_location_id: UUID | None | None = None
    movement_type: str | None = None


class StockMovementReverseRequest(BaseModel):
    """Payload for reverse."""
    reason: str
