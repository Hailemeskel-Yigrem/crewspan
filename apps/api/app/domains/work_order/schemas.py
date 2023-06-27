"""Pydantic schemas for WorkOrder."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import re


class WorkOrderBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    order_number: str
    customer_id: UUID
    site_id: UUID
    title: str
    description: str | None
    priority: str
    status: str
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    assigned_technician_id: UUID | None
    sla_policy_id: UUID | None
    estimated_duration_minutes: int | None
    completion_notes: str | None


class WorkOrderCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    order_number: str
    customer_id: UUID
    site_id: UUID
    title: str
    description: str | None = Field(None)
    priority: str = Field('normal', description="low|normal|high|critical")
    status: str = Field('draft')
    scheduled_start: datetime | None = Field(None)
    scheduled_end: datetime | None = Field(None)
    assigned_technician_id: UUID | None = Field(None)
    sla_policy_id: UUID | None = Field(None)
    estimated_duration_minutes: int | None = Field(None)
    completion_notes: str | None = Field(None)
    @field_validator("order_number")
    @classmethod
    def validate_order_number_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("order_number cannot be blank")
        return stripped

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
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

    @model_validator(mode="after")
    def validate_scheduled_start_scheduled_end_ordering(self) -> "WorkOrderCreate":
        start = getattr(self, "scheduled_start", None)
        end = getattr(self, "scheduled_end", None)
        if start is not None and end is not None and end < start:
            raise ValueError("scheduled_end must be on or after scheduled_start")
        return self


class WorkOrderUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str | None | None = None
    priority: str | None = None
    status: str | None = None
    scheduled_start: datetime | None | None = None
    scheduled_end: datetime | None | None = None
    assigned_technician_id: UUID | None | None = None
    sla_policy_id: UUID | None | None = None
    estimated_duration_minutes: int | None | None = None
    completion_notes: str | None | None = None


class WorkOrderRead(WorkOrderBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class WorkOrderListResponse(BaseModel):
    items: list[WorkOrderRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[WorkOrderRead], total: int, page: int, page_size: int) -> "WorkOrderListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class WorkOrderFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    order_number: str | None = None
    customer_id: UUID | None = None
    site_id: UUID | None = None
    status: str | None = None
    assigned_technician_id: UUID | None | None = None


class WorkOrderAssignTechnicianRequest(BaseModel):
    """Payload for assign_technician."""
    technician_id: UUID

class WorkOrderCompleteRequest(BaseModel):
    """Payload for complete."""
    notes: str | None

class WorkOrderCancelRequest(BaseModel):
    """Payload for cancel."""
    reason: str
