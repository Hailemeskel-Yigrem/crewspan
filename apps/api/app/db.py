"""Database engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

from app.domains.tenant.models import Tenant  # noqa: F401
from app.domains.user.models import User  # noqa: F401
from app.domains.role.models import Role  # noqa: F401
from app.domains.customer.models import Customer  # noqa: F401
from app.domains.customer_site.models import CustomerSite  # noqa: F401
from app.domains.contact.models import Contact  # noqa: F401
from app.domains.work_order.models import WorkOrder  # noqa: F401
from app.domains.work_order_task.models import WorkOrderTask  # noqa: F401
from app.domains.technician.models import Technician  # noqa: F401
from app.domains.technician_skill.models import TechnicianSkill  # noqa: F401
from app.domains.schedule.models import Schedule  # noqa: F401
from app.domains.dispatch.models import Dispatch  # noqa: F401
from app.domains.inventory_item.models import InventoryItem  # noqa: F401
from app.domains.inventory_location.models import InventoryLocation  # noqa: F401
from app.domains.stock_movement.models import StockMovement  # noqa: F401
from app.domains.parts_request.models import PartsRequest  # noqa: F401
from app.domains.invoice.models import Invoice  # noqa: F401
from app.domains.invoice_line_item.models import InvoiceLineItem  # noqa: F401
from app.domains.payment.models import Payment  # noqa: F401
from app.domains.sla_policy.models import SlaPolicy  # noqa: F401
from app.domains.sla_breach.models import SlaBreach  # noqa: F401
from app.domains.service_contract.models import ServiceContract  # noqa: F401
from app.domains.equipment.models import Equipment  # noqa: F401
from app.domains.notification.models import Notification  # noqa: F401
from app.domains.webhook.models import Webhook  # noqa: F401
from app.domains.audit_log.models import AuditLog  # noqa: F401


class Base(DeclarativeBase):
    pass


engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    global engine, SessionLocal
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def close_db() -> None:
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
