"""Pydantic schemas for SlaPolicy."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re


class SlaPolicyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    name: str
    description: str | None
    priority: str
    response_minutes: int
    resolution_minutes: int
    business_hours_only: bool
    escalation_rules: list[object] | None
    is_active: bool


class SlaPolicyCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str
    description: str | None = Field(None)
    priority: str
    response_minutes: int
    resolution_minutes: int
    business_hours_only: bool = Field(True)
    escalation_rules: list[object] | None = Field(None)
    is_active: bool = Field(True)
    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {'low', 'normal', 'high', 'critical'}
        if value not in allowed:
            raise ValueError("priority must be one of: " + ", ".join(sorted(allowed)))
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("priority cannot be blank")
        return stripped


class SlaPolicyUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str | None | None = None
    business_hours_only: bool | None = None
    escalation_rules: list[object] | None | None = None
    is_active: bool | None = None


class SlaPolicyRead(SlaPolicyBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class SlaPolicyListResponse(BaseModel):
    items: list[SlaPolicyRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[SlaPolicyRead], total: int, page: int, page_size: int) -> "SlaPolicyListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class SlaPolicyFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    name: str | None = None
    priority: str | None = None


class SlaPolicyEvaluateDeadlinesRequest(BaseModel):
    """Payload for evaluate_deadlines."""
    opened_at: datetime

class SlaPolicyCloneRequest(BaseModel):
    """Payload for clone."""
    new_name: str
