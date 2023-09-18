"""SQLAlchemy models for SlaBreach."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SlaBreach(Base):
    """Recorded SLA violations for reporting and escalation."""

    __tablename__ = "sla_breaches"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    work_order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    sla_policy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    breach_type: Mapped[str] = mapped_column(String(32), index=True, )
    expected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), )
    minutes_overdue: Mapped[int] = mapped_column(Integer, )
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, )
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, )
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
        return f"<SlaBreach id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
