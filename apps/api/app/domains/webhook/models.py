"""SQLAlchemy models for Webhook."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class Webhook(Base):
    """Tenant webhook subscriptions for outbound event delivery."""

    __tablename__ = "webhooks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), )
    url: Mapped[str] = mapped_column(String(2048), )
    secret: Mapped[str] = mapped_column(String(255), )
    event_types: Mapped[list] = mapped_column(JSON, )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, )
    failure_count: Mapped[int] = mapped_column(Integer, default=0, )
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, )
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
        return f"<Webhook id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
