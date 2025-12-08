"""Pydantic schemas for User."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    email: str
    full_name: str
    password_hash: str
    phone: str | None
    role_id: UUID
    is_active: bool
    last_login_at: datetime | None
    preferences: dict[str, object] | None


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: str = Field(..., description="Login email address")
    full_name: str = Field(..., description="Display name")
    phone: str | None = Field(None, description="Contact phone number")
    role_id: UUID = Field(..., description="Assigned RBAC role")
    is_active: bool = Field(True, description="Account enabled flag")
    last_login_at: datetime | None = Field(None)
    preferences: dict[str, object] | None = Field(None, description="UI and notification preferences")
    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "@" not in value or len(value) < 5:
            raise ValueError("Valid email address required for email")
        return value.strip().lower()

    @field_validator("email")
    @classmethod
    def validate_email_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("email cannot be blank")
        return stripped

    @field_validator("full_name")
    @classmethod
    def validate_full_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("full_name cannot be blank")
        return stripped


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    phone: str | None | None = None
    is_active: bool | None = None
    last_login_at: datetime | None | None = None
    preferences: dict[str, object] | None | None = None


class UserRead(UserBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class UserListResponse(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[UserRead], total: int, page: int, page_size: int) -> "UserListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class UserFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    email: str | None = None
    role_id: UUID | None = None


class UserChangePasswordRequest(BaseModel):
    """Payload for change_password."""
    new_password: str
# history-note: evolutionary edit 52
