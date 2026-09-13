"""SQLAlchemy models for Contact."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class Contact(Base):
    """Customer contacts for scheduling and notification routing."""

    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    site_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True, )
    first_name: Mapped[str] = mapped_column(String(128), )
    last_name: Mapped[str] = mapped_column(String(128), )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, )
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, )
    role_title: Mapped[str | None] = mapped_column(String(128), nullable=True, )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, )
    notify_on_dispatch: Mapped[bool] = mapped_column(Boolean, default=True, )
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
        return f"<Contact id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime

        self.updated_at = datetime.now(UTC)
