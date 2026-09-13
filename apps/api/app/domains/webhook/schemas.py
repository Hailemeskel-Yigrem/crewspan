"""Pydantic schemas for Webhook."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WebhookBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    name: str
    url: str
    secret: str
    event_types: list[object]
    is_active: bool
    failure_count: int
    last_triggered_at: datetime | None


class WebhookCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str
    url: str
    secret: str
    event_types: list[object]
    is_active: bool = Field(True)
    failure_count: int = Field(0)
    last_triggered_at: datetime | None = Field(None)
    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped

    @field_validator("url")
    @classmethod
    def validate_url_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("url cannot be blank")
        return stripped

    @field_validator("secret")
    @classmethod
    def validate_secret_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("secret cannot be blank")
        return stripped


class WebhookUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    is_active: bool | None = None
    failure_count: int | None = None
    last_triggered_at: datetime | None | None = None


class WebhookRead(WebhookBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class WebhookListResponse(BaseModel):
    items: list[WebhookRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[WebhookRead], total: int, page: int, page_size: int) -> WebhookListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class WebhookFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")



class WebhookDisableOnFailuresRequest(BaseModel):
    """Payload for disable_on_failures."""
    threshold: int
