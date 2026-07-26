"""SQLAlchemy models for InventoryLocation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class InventoryLocation(Base):
    """Warehouses, vans, and stock locations."""

    __tablename__ = "inventory_locations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(64), index=True, )
    name: Mapped[str] = mapped_column(String(255), )
    location_type: Mapped[str] = mapped_column(String(32), default='warehouse', )
    technician_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True, )
    address: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
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
        return f"<InventoryLocation id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
