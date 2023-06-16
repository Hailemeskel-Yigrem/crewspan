"""Pydantic schemas for CustomerSite."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CustomerSiteBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    customer_id: UUID
    site_code: str
    name: str
    address: dict[str, object]
    latitude: Decimal | None
    longitude: Decimal | None
    access_instructions: str | None
    service_window: dict[str, object] | None
    is_active: bool


class CustomerSiteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_id: UUID
    site_code: str
    name: str
    address: dict[str, object] = Field(..., description="Structured service address")
    latitude: Decimal | None = Field(None)
    longitude: Decimal | None = Field(None)
    access_instructions: str | None = Field(None)
    service_window: dict[str, object] | None = Field(None, description="Preferred service hours")
    is_active: bool = Field(True)
    @field_validator("site_code")
    @classmethod
    def validate_site_code_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("site_code cannot be blank")
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


class CustomerSiteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    latitude: Decimal | None | None = None
    longitude: Decimal | None | None = None
    access_instructions: str | None | None = None
    service_window: dict[str, object] | None | None = None
    is_active: bool | None = None


class CustomerSiteRead(CustomerSiteBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class CustomerSiteListResponse(BaseModel):
    items: list[CustomerSiteRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[CustomerSiteRead], total: int, page: int, page_size: int) -> "CustomerSiteListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class CustomerSiteFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    customer_id: UUID | None = None
    site_code: str | None = None


class CustomerSiteValidateAccessWindowRequest(BaseModel):
    """Payload for validate_access_window."""
    at: datetime
