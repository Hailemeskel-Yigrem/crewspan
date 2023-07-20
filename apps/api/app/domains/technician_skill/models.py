"""SQLAlchemy models for TechnicianSkill."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TechnicianSkill(Base):
    """Skill and certification assignments for technicians."""

    __tablename__ = "technician_skills"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    technician_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    skill_code: Mapped[str] = mapped_column(String(64), index=True, )
    skill_name: Mapped[str] = mapped_column(String(128), )
    proficiency_level: Mapped[int] = mapped_column(Integer, default=1, )
    certified_at: Mapped[date | None] = mapped_column(Date, nullable=True, )
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True, )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<TechnicianSkill id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
