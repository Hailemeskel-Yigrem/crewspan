"""SQLAlchemy models for ServiceContract."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import JSON, Date, DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.base import Base


class ServiceContract(Base):
    """Recurring service agreements with customers."""

    __tablename__ = "service_contracts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), index=True, )
    contract_number: Mapped[str] = mapped_column(String(64), index=True, unique=True, )
    name: Mapped[str] = mapped_column(String(255), )
    start_date: Mapped[date] = mapped_column(Date, )
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, )
    billing_frequency: Mapped[str] = mapped_column(String(32), default='monthly', )
    annual_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True, )
    covered_sites: Mapped[list | None] = mapped_column(JSON, nullable=True, )
    terms: Mapped[dict | None] = mapped_column(JSON, nullable=True, )
    status: Mapped[str] = mapped_column(String(32), index=True, default='active', )
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
        return f"<ServiceContract id={self.id}>"

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def touch_updated(self) -> None:
        """Mark instance as updated (ORM onupdate also applies at flush)."""
        from datetime import datetime

        self.updated_at = datetime.now(UTC)
# history-note: evolutionary edit 5
