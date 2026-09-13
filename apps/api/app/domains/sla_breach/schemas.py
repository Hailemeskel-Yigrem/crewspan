"""Pydantic schemas for SlaBreach."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SlaBreachBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    work_order_id: UUID
    sla_policy_id: UUID
    breach_type: str
    expected_at: datetime
    detected_at: datetime
    minutes_overdue: int
    acknowledged: bool
    escalation_level: int


class SlaBreachCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    work_order_id: UUID
    sla_policy_id: UUID
    breach_type: str
    expected_at: datetime
    detected_at: datetime
    minutes_overdue: int
    acknowledged: bool = Field(False)
    escalation_level: int = Field(0)
    @field_validator("breach_type")
    @classmethod
    def validate_breach_type_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("breach_type cannot be blank")
        return stripped


class SlaBreachUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    acknowledged: bool | None = None
    escalation_level: int | None = None


class SlaBreachRead(SlaBreachBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class SlaBreachListResponse(BaseModel):
    items: list[SlaBreachRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[SlaBreachRead], total: int, page: int, page_size: int) -> SlaBreachListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class SlaBreachFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    work_order_id: UUID | None = None
    sla_policy_id: UUID | None = None
    breach_type: str | None = None
