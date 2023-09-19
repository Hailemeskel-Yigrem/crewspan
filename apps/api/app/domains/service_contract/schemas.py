"""Pydantic schemas for ServiceContract."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re
from datetime import date, datetime


class ServiceContractBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    customer_id: UUID
    contract_number: str
    name: str
    start_date: date
    end_date: date | None
    billing_frequency: str
    annual_value: Decimal | None
    covered_sites: list[object] | None
    terms: dict[str, object] | None
    status: str


class ServiceContractCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_id: UUID
    contract_number: str
    name: str
    start_date: date
    end_date: date | None = Field(None)
    billing_frequency: str = Field('monthly')
    annual_value: Decimal | None = Field(None)
    covered_sites: list[object] | None = Field(None)
    terms: dict[str, object] | None = Field(None)
    status: str = Field('active')
    @field_validator("contract_number")
    @classmethod
    def validate_contract_number_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("contract_number cannot be blank")
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

    @field_validator("billing_frequency")
    @classmethod
    def validate_billing_frequency_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("billing_frequency cannot be blank")
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


class ServiceContractUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    end_date: date | None | None = None
    billing_frequency: str | None = None
    annual_value: Decimal | None | None = None
    covered_sites: list[object] | None | None = None
    terms: dict[str, object] | None | None = None
    status: str | None = None


class ServiceContractRead(ServiceContractBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ServiceContractListResponse(BaseModel):
    items: list[ServiceContractRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[ServiceContractRead], total: int, page: int, page_size: int) -> "ServiceContractListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class ServiceContractFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    customer_id: UUID | None = None
    contract_number: str | None = None
    status: str | None = None


class ServiceContractRenewRequest(BaseModel):
    """Payload for renew."""
    new_end_date: date

class ServiceContractTerminateRequest(BaseModel):
    """Payload for terminate."""
    reason: str
