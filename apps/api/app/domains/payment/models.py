"""SQLAlchemy models for Payment."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class Payment(Base):
    """Payment records applied to invoices."""

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    invoice_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), )
    payment_method: Mapped[str] = mapped_column(String(32), )
    payment_date: Mapped[date] = mapped_column(Date, )
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True, )
    status: Mapped[str] = mapped_column(String(32), default='completed', )
    processor_response: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
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
        return f"<Payment id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
