"""Pydantic schemas for Payment."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re
from datetime import date, datetime


class PaymentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    invoice_id: UUID
    amount: Decimal
    payment_method: str
    payment_date: date
    reference_number: str | None
    status: str
    processor_response: dict[str, object] | None


class PaymentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    invoice_id: UUID
    amount: Decimal
    payment_method: str
    payment_date: date
    reference_number: str | None = Field(None)
    status: str = Field('completed')
    processor_response: dict[str, object] | None = Field(None)
    @field_validator("amount")
    @classmethod
    def validate_amount_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("amount cannot be negative")
        return value

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("payment_method cannot be blank")
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


class PaymentUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    reference_number: str | None | None = None
    status: str | None = None
    processor_response: dict[str, object] | None | None = None


class PaymentRead(PaymentBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class PaymentListResponse(BaseModel):
    items: list[PaymentRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[PaymentRead], total: int, page: int, page_size: int) -> "PaymentListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class PaymentFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    invoice_id: UUID | None = None


class PaymentRefundRequest(BaseModel):
    """Payload for refund."""
    amount: Decimal
reason: str
