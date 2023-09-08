"""Pydantic schemas for InvoiceLineItem."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InvoiceLineItemBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    invoice_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    line_total: Decimal
    item_type: str
    reference_id: UUID | None


class InvoiceLineItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    invoice_id: UUID
    description: str
    quantity: Decimal = Field(1)
    unit_price: Decimal
    tax_rate: Decimal = Field(0)
    line_total: Decimal = Field(0)
    item_type: str = Field('service')
    reference_id: UUID | None = Field(None)
    @field_validator("description")
    @classmethod
    def validate_description_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("description cannot be blank")
        return stripped

    @field_validator("unit_price")
    @classmethod
    def validate_unit_price_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("unit_price cannot be negative")
        return value

    @field_validator("item_type")
    @classmethod
    def validate_item_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("item_type cannot be blank")
        return stripped


class InvoiceLineItemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    quantity: Decimal | None = None
    tax_rate: Decimal | None = None
    line_total: Decimal | None = None
    item_type: str | None = None
    reference_id: UUID | None | None = None


class InvoiceLineItemRead(InvoiceLineItemBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class InvoiceLineItemListResponse(BaseModel):
    items: list[InvoiceLineItemRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[InvoiceLineItemRead], total: int, page: int, page_size: int) -> "InvoiceLineItemListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class InvoiceLineItemFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    invoice_id: UUID | None = None
