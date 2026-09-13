"""SQLAlchemy models for Technician."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class Technician(Base):
    """Field technician profiles linked to user accounts."""

    __tablename__ = "technicians"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, unique=True, )
    employee_id: Mapped[str] = mapped_column(String(64), index=True, )
    home_base_latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True, )
    home_base_longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True, )
    max_daily_hours: Mapped[int] = mapped_column(Integer, default=8, )
    status: Mapped[str] = mapped_column(String(32), index=True, default='available', )
    certifications: Mapped[list | None] = mapped_column(JSON, nullable=True, )
    vehicle_info: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
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
        return f"<Technician id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime

        self.updated_at = datetime.now(UTC)
