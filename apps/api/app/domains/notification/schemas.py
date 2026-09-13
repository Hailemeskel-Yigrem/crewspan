"""Pydantic schemas for Notification."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    recipient_id: UUID | None
    recipient_email: str | None
    channel: str
    template_key: str
    subject: str | None
    body: str
    status: str
    sent_at: datetime | None
    payload_meta: dict[str, object] | None


class NotificationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    recipient_id: UUID | None = Field(None)
    recipient_email: str | None = Field(None)
    channel: str
    template_key: str
    subject: str | None = Field(None)
    body: str
    status: str = Field('pending')
    sent_at: datetime | None = Field(None)
    payload_meta: dict[str, object] | None = Field(None, description="Channel-specific payload attributes")
    @field_validator("recipient_email")
    @classmethod
    def validate_recipient_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if "@" not in value or len(value) < 5:
            raise ValueError("Valid email address required for recipient_email")
        return value.strip().lower()

    @field_validator("channel")
    @classmethod
    def validate_channel_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("channel cannot be blank")
        return stripped

    @field_validator("template_key")
    @classmethod
    def validate_template_key_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("template_key cannot be blank")
        return stripped

    @field_validator("body")
    @classmethod
    def validate_body_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("body cannot be blank")
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


class NotificationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    recipient_id: UUID | None | None = None
    recipient_email: str | None | None = None
    subject: str | None | None = None
    status: str | None = None
    sent_at: datetime | None | None = None
    payload_meta: dict[str, object] | None | None = None


class NotificationRead(NotificationBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[NotificationRead], total: int, page: int, page_size: int) -> NotificationListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class NotificationFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    recipient_id: UUID | None | None = None
    channel: str | None = None
    status: str | None = None


class NotificationMarkFailedRequest(BaseModel):
    """Payload for mark_failed."""
    error: str
