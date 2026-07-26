"""SQLAlchemy models for AuditLog."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class AuditLog(Base):
    """Immutable audit trail for compliance and forensics."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True, )
    action: Mapped[str] = mapped_column(String(64), index=True, )
    resource_type: Mapped[str] = mapped_column(String(64), index=True, )
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True, )
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True, )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return False

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime, timezone

        self.updated_at = datetime.now(timezone.utc)
