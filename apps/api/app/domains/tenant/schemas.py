"""Pydantic schemas for Tenant."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    slug: str
    display_name: str
    legal_name: str | None
    subscription_tier: str
    timezone: str
    is_active: bool
    feature_flags: dict[str, object] | None
    settings: dict[str, object] | None


class TenantCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    slug: str = Field(..., description="URL-safe tenant identifier")
    display_name: str = Field(..., description="Human-readable organization name")
    legal_name: str | None = Field(None, description="Registered legal entity name")
    subscription_tier: str = Field('standard', description="Billing tier")
    timezone: str = Field('UTC', description="Default IANA timezone")
    is_active: bool = Field(True, description="Whether tenant may authenticate")
    feature_flags: dict[str, object] | None = Field(None, description="Per-tenant feature toggles")
    settings: dict[str, object] | None = Field(None, description="Tenant-level configuration blob")
    @field_validator("slug")
    @classmethod
    def validate_slug_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("slug cannot be blank")
        return stripped

    @field_validator("display_name")
    @classmethod
    def validate_display_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("display_name cannot be blank")
        return stripped

    @field_validator("subscription_tier")
    @classmethod
    def validate_subscription_tier_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("subscription_tier cannot be blank")
        return stripped

    @field_validator("timezone")
    @classmethod
    def validate_timezone_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("timezone cannot be blank")
        return stripped


class TenantUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    legal_name: str | None | None = None
    subscription_tier: str | None = None
    timezone: str | None = None
    is_active: bool | None = None
    feature_flags: dict[str, object] | None | None = None
    settings: dict[str, object] | None | None = None


class TenantRead(TenantBase):
    id: UUID

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class TenantListResponse(BaseModel):
    items: list[TenantRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[TenantRead], total: int, page: int, page_size: int) -> TenantListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class TenantFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    slug: str | None = None


class TenantUpdateSettingsRequest(BaseModel):
    """Payload for update_settings."""
    settings: dict[str, object]
