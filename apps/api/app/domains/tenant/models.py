"""SQLAlchemy models for Tenant."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class Tenant(Base):
    """Multi-tenant organization registry with subscription tier and feature flags."""

    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(64), index=True, unique=True, )
    display_name: Mapped[str] = mapped_column(String(255), )
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True, )
    subscription_tier: Mapped[str] = mapped_column(String(32), default='standard', )
    timezone: Mapped[str] = mapped_column(String(64), default='UTC', )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, )
    feature_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
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
        return f"<Tenant id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime

        self.updated_at = datetime.now(UTC)
