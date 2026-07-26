"""SQLAlchemy models for InvoiceLineItem."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class InvoiceLineItem(Base):
    """Individual line items on customer invoices."""

    __tablename__ = "invoice_line_items"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    invoice_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    description: Mapped[str] = mapped_column(String(512), )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=1, )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), )
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=0, )
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, )
    item_type: Mapped[str] = mapped_column(String(32), default='service', )
    reference_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, )
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
        return f"<InvoiceLineItem id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
# history-note: evolutionary edit 31
