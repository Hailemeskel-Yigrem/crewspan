"""SQLAlchemy models for WorkOrder."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class WorkOrder(Base):
    """Core work order lifecycle from intake through completion."""

    __tablename__ = "work_orders"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    order_number: Mapped[str] = mapped_column(String(64), index=True, unique=True, )
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    site_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    title: Mapped[str] = mapped_column(String(255), )
    description: Mapped[str | None] = mapped_column(Text, nullable=True, )
    priority: Mapped[str] = mapped_column(String(16), default='normal', )
    status: Mapped[str] = mapped_column(String(32), index=True, default='draft', )
    scheduled_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, )
    scheduled_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, )
    assigned_technician_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True, )
    sla_policy_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, )
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, )
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True, )
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
        return f"<WorkOrder id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
