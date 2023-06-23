"""Pydantic schemas for Contact."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re


class ContactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    customer_id: UUID
    site_id: UUID | None
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    role_title: str | None
    is_primary: bool
    notify_on_dispatch: bool


class ContactCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    customer_id: UUID
    site_id: UUID | None = Field(None)
    first_name: str
    last_name: str
    email: str | None = Field(None)
    phone: str | None = Field(None)
    role_title: str | None = Field(None)
    is_primary: bool = Field(False)
    notify_on_dispatch: bool = Field(True)
    @field_validator("first_name")
    @classmethod
    def validate_first_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("first_name cannot be blank")
        return stripped

    @field_validator("last_name")
    @classmethod
    def validate_last_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("last_name cannot be blank")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "@" not in value or len(value) < 5:
            raise ValueError("Valid email address required for email")
        return value.strip().lower()


class ContactUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    site_id: UUID | None | None = None
    email: str | None | None = None
    phone: str | None | None = None
    role_title: str | None | None = None
    is_primary: bool | None = None
    notify_on_dispatch: bool | None = None


class ContactRead(ContactBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ContactListResponse(BaseModel):
    items: list[ContactRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[ContactRead], total: int, page: int, page_size: int) -> "ContactListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class ContactFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    customer_id: UUID | None = None
    site_id: UUID | None | None = None
