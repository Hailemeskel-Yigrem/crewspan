"""Pydantic schemas for Invoice."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvoiceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    invoice_number: str
    customer_id: UUID
    work_order_id: UUID | None
    status: str
    issue_date: date
    due_date: date
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    notes: str | None


class InvoiceCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    invoice_number: str
    customer_id: UUID
    work_order_id: UUID | None = Field(None)
    status: str = Field('draft')
    issue_date: date
    due_date: date
    subtotal: Decimal = Field(0)
    tax_amount: Decimal = Field(0)
    total_amount: Decimal = Field(0)
    currency: str = Field('USD')
    notes: str | None = Field(None)
    @field_validator("invoice_number")
    @classmethod
    def validate_invoice_number_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("invoice_number cannot be blank")
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

    @field_validator("currency")
    @classmethod
    def validate_currency_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("currency cannot be blank")
        return stripped


class InvoiceUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    work_order_id: UUID | None | None = None
    status: str | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    currency: str | None = None
    notes: str | None | None = None


class InvoiceRead(InvoiceBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class InvoiceListResponse(BaseModel):
    items: list[InvoiceRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[InvoiceRead], total: int, page: int, page_size: int) -> InvoiceListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class InvoiceFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    invoice_number: str | None = None
    customer_id: UUID | None = None
    work_order_id: UUID | None | None = None
    status: str | None = None


class InvoiceVoidRequest(BaseModel):
    """Payload for void."""
    reason: str
