"""Pydantic schemas for WorkOrderTask."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkOrderTaskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    work_order_id: UUID
    sequence: int
    title: str
    instructions: str | None
    is_required: bool
    status: str
    completed_at: datetime | None
    completed_by_id: UUID | None


class WorkOrderTaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    work_order_id: UUID
    sequence: int = Field(0)
    title: str
    instructions: str | None = Field(None)
    is_required: bool = Field(True)
    status: str = Field('pending')
    completed_at: datetime | None = Field(None)
    completed_by_id: UUID | None = Field(None)
    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
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


class WorkOrderTaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    sequence: int | None = None
    instructions: str | None | None = None
    is_required: bool | None = None
    status: str | None = None
    completed_at: datetime | None | None = None
    completed_by_id: UUID | None | None = None


class WorkOrderTaskRead(WorkOrderTaskBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class WorkOrderTaskListResponse(BaseModel):
    items: list[WorkOrderTaskRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[WorkOrderTaskRead], total: int, page: int, page_size: int) -> WorkOrderTaskListResponse:
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class WorkOrderTaskFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    work_order_id: UUID | None = None


class WorkOrderTaskReorderRequest(BaseModel):
    """Payload for reorder."""
    sequence: int
