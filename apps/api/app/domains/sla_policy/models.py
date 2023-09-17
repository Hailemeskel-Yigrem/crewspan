"""SQLAlchemy models for SlaPolicy."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SlaPolicy(Base):
    """Service level agreement policy definitions."""

    __tablename__ = "sla_policies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), index=True, )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, )
    priority: Mapped[str] = mapped_column(String(16), index=True, )
    response_minutes: Mapped[int] = mapped_column(Integer, )
    resolution_minutes: Mapped[int] = mapped_column(Integer, )
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True, )
    escalation_rules: Mapped[list | None] = mapped_column(JSON, nullable=True, )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, )
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
        return f"<SlaPolicy id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
