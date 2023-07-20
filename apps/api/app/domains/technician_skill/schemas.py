"""Pydantic schemas for TechnicianSkill."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TechnicianSkillBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    technician_id: UUID
    skill_code: str
    skill_name: str
    proficiency_level: int
    certified_at: date | None
    expires_at: date | None


class TechnicianSkillCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    technician_id: UUID
    skill_code: str
    skill_name: str
    proficiency_level: int = Field(1, description="1-5 scale")
    certified_at: date | None = Field(None)
    expires_at: date | None = Field(None)
    @field_validator("skill_code")
    @classmethod
    def validate_skill_code_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("skill_code cannot be blank")
        return stripped

    @field_validator("skill_name")
    @classmethod
    def validate_skill_name_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("skill_name cannot be blank")
        return stripped


class TechnicianSkillUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    proficiency_level: int | None = None
    certified_at: date | None | None = None
    expires_at: date | None | None = None


class TechnicianSkillRead(TechnicianSkillBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class TechnicianSkillListResponse(BaseModel):
    items: list[TechnicianSkillRead]
    total: int
    page: int
    page_size: int
    pages: int = Field(default=1, ge=1)

    @classmethod
    def from_page(cls, items: list[TechnicianSkillRead], total: int, page: int, page_size: int) -> "TechnicianSkillListResponse":
        pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


class TechnicianSkillFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)
    search: str | None = None
    order_by: str = Field(default="created_at")
    order_dir: str = Field(default="desc", pattern="^(asc|desc)$")
    technician_id: UUID | None = None
    skill_code: str | None = None


class TechnicianSkillRenewCertificationRequest(BaseModel):
    """Payload for renew_certification."""
    expires_at: date
