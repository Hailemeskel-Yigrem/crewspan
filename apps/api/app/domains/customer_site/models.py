"""SQLAlchemy models for CustomerSite."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class CustomerSite(Base):
    """Physical service locations belonging to customers."""

    __tablename__ = "customer_sites"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    site_code: Mapped[str] = mapped_column(String(64), index=True, )
    name: Mapped[str] = mapped_column(String(255), )
    address: Mapped[dict] = mapped_column(JSON, )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True, )
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True, )
    access_instructions: Mapped[str | None] = mapped_column(Text, nullable=True, )
    service_window: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
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
        return f"<CustomerSite id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime

        self.updated_at = datetime.now(UTC)
