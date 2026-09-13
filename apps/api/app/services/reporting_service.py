"""Operational reporting aggregates for dashboard and analytics endpoints."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.invoice.models import Invoice
from app.domains.sla_breach.models import SlaBreach
from app.domains.technician.models import Technician
from app.domains.work_order.models import WorkOrder

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class DashboardMetrics:
    open_work_orders: int = 0
    in_progress_work_orders: int = 0
    active_technicians: int = 0
    revenue_mtd: Decimal = Decimal("0")
    sla_breaches_open: int = 0
    completed_this_week: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class UtilizationRow:
    technician_id: UUID
    employee_id: str
    utilization_pct: float
    open_jobs: int


class ReportingService:
    """Computes tenant-scoped KPIs across 26 domain modules."""

    OPEN_STATUSES = ("draft", "submitted", "assigned", "in_progress", "pending")
    IN_PROGRESS_STATUSES = ("in_progress", "assigned")

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def dashboard(self, tenant_id: UUID) -> DashboardMetrics:
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=now.weekday())

        open_count = await self._count_work_orders(tenant_id, self.OPEN_STATUSES)
        in_progress = await self._count_work_orders(tenant_id, self.IN_PROGRESS_STATUSES)
        active_techs = await self._count_active_technicians(tenant_id)
        revenue = await self._sum_invoice_revenue(tenant_id, month_start)
        breaches = await self._count_open_sla_breaches(tenant_id)
        completed_week = await self._count_completed_since(tenant_id, week_start)

        metrics = DashboardMetrics(
            open_work_orders=open_count,
            in_progress_work_orders=in_progress,
            active_technicians=active_techs,
            revenue_mtd=revenue,
            sla_breaches_open=breaches,
            completed_this_week=completed_week,
        )
        logger.info("reporting.dashboard", tenant_id=str(tenant_id), **metrics.__dict__)
        return metrics

    async def technician_utilization(
        self,
        tenant_id: UUID,
        *,
        on_date: date | None = None,
    ) -> list[UtilizationRow]:
        on_date = on_date or date.today()
        stmt = select(Technician).where(
            Technician.tenant_id == tenant_id,
            Technician.deleted_at.is_(None),
            Technician.status.in_(("available", "busy", "on_job")),
        )
        techs = (await self._session.execute(stmt)).scalars().all()
        rows: list[UtilizationRow] = []
        for tech in techs:
            open_jobs = await self._open_jobs_for_technician(tenant_id, tech.id)
            max_hours = max(1, int(getattr(tech, "max_daily_hours", 8) or 8))
            utilization = min(100.0, (open_jobs / max_hours) * 100.0)
            rows.append(
                UtilizationRow(
                    technician_id=tech.id,
                    employee_id=str(tech.employee_id),
                    utilization_pct=round(utilization, 1),
                    open_jobs=open_jobs,
                )
            )
        return sorted(rows, key=lambda r: -r.utilization_pct)

    async def _count_work_orders(self, tenant_id: UUID, statuses: tuple[str, ...]) -> int:
        stmt = (
            select(func.count())
            .select_from(WorkOrder)
            .where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.deleted_at.is_(None),
                WorkOrder.status.in_(statuses),
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _count_active_technicians(self, tenant_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Technician)
            .where(
                Technician.tenant_id == tenant_id,
                Technician.deleted_at.is_(None),
                Technician.status != "offline",
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _sum_invoice_revenue(self, tenant_id: UUID, since: datetime) -> Decimal:
        stmt = select(func.coalesce(func.sum(Invoice.total_amount), 0)).where(
            Invoice.tenant_id == tenant_id,
            Invoice.deleted_at.is_(None),
            Invoice.created_at >= since,
            Invoice.status.in_(("finalized", "paid", "sent")),
        )
        value = (await self._session.execute(stmt)).scalar_one()
        return Decimal(str(value or 0))

    async def _count_open_sla_breaches(self, tenant_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(SlaBreach)
            .where(
                SlaBreach.tenant_id == tenant_id,
                SlaBreach.deleted_at.is_(None),
                SlaBreach.acknowledged.is_(False),
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _count_completed_since(self, tenant_id: UUID, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(WorkOrder)
            .where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.deleted_at.is_(None),
                WorkOrder.status == "completed",
                WorkOrder.updated_at >= since,
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _open_jobs_for_technician(self, tenant_id: UUID, technician_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(WorkOrder)
            .where(
                WorkOrder.tenant_id == tenant_id,
                WorkOrder.deleted_at.is_(None),
                WorkOrder.assigned_technician_id == technician_id,
                WorkOrder.status.in_(self.IN_PROGRESS_STATUSES),
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())
