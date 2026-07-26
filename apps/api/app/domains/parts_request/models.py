"""SQLAlchemy models for PartsRequest."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class PartsRequest(Base):
    """Parts requisitions linked to work orders."""

    __tablename__ = "parts_requests"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    work_order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    requested_by_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    status: Mapped[str] = mapped_column(String(32), index=True, default='pending', )
    needed_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, )
    fulfillment_location_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, )
    line_items: Mapped[list] = mapped_column(JSON, )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, )
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
        return f"<PartsRequest id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
