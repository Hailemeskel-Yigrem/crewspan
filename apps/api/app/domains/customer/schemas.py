"""Pydantic schemas for Customer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    account_number: str
    name: str
    customer_type: str
    billing_email: str | None
    billing_address: dict[str, object] | None
    credit_limit: Decimal | None
    payment_terms_days: int
    notes: str | None
    is_active: bool


class CustomerCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    account_number: str = Field(..., description="External account reference")
    name: str = Field(..., description="Customer display name")
    customer_type: str = Field('commercial', description="residential|commercial|government")
    billing_email: str | None = Field(None)
    billing_address: dict[str, object] | None = Field(None, description="Structured billing address")
    credit_limit: Decimal | None = Field(None)
    payment_terms_days: int = Field(30)
    notes: str | None = Field(None)
    is_active: bool = Field(True)
    @field_validator("account_number")
    @classmethod
    def validate_account_number_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("account_number cannot be blank")
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

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {'residential', 'commercial', 'government'}
        if value not in allowed:
            raise ValueError("customer_type must be one of: " + ", ".join(sorted(allowed)))
        return value

    @field_validator("customer_type")
    @classmethod
    def validate_customer_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("customer_type cannot be blank")
        return stripped

    @field_validator("billing_email")
    @classmethod
    def validate_billing_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "@" not in value or len(value) < 5:
            raise ValueError("Valid email address required for billing_email")
        return value.strip().lower()

    @field_validator("credit_limit")
    @classmethod
    def validate_credit_limit_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("credit_limit cannot be negative")
        return value


class CustomerUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_type: str | None = None
    billing_email: str | None | None = None
    billing_address: dict[str, object] | None | None = None
    credit_limit: Decimal | None | None = None
    payment_terms_days: int | None = None
    notes: str | None | None = None
    is_active: bool | None = None


class CustomerRead(CustomerBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CustomerListResponse(BaseModel):
    items: list[CustomerRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[CustomerRead], total: int, page: int, page_size: int) -> CustomerListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class CustomerFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    account_number: str | None = None
    name: str | None = None


class CustomerUpdateCreditLimitRequest(BaseModel):
    """Payload for update_credit_limit."""
    limit: Decimal

class CustomerMergeIntoRequest(BaseModel):
    """Payload for merge_into."""
    target_id: UUID
