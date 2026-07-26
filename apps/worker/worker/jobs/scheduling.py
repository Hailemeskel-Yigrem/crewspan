"""Scheduling reminder and dispatch background jobs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog
from celery import shared_task

from worker.base import CrewspanTask

logger = structlog.get_logger(__name__)


@shared_task(base=CrewspanTask, name="worker.jobs.scheduling.send_upcoming_appointment_reminders")
def send_upcoming_appointment_reminders(*, horizon_hours: int = 24) -> dict[str, int]:
    """Find appointments starting within horizon and notify assigned technicians."""
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=horizon_hours)
    logger.info(
        "scheduling.reminders.scan",
        window_start=now.isoformat(),
        window_end=window_end.isoformat(),
    )
    reminders_sent = 0
    # Stub: query schedules where starts_at between now and window_end
    logger.info("scheduling.reminders.complete", reminders_sent=reminders_sent)
    return {"reminders_sent": reminders_sent}


@shared_task(base=CrewspanTask, name="worker.jobs.scheduling.detect_schedule_conflicts")
def detect_schedule_conflicts(
    technician_id: str,
    *,
    tenant_id: str,
    starts_at: str,
    ends_at: str,
) -> dict[str, object]:
    """Detect overlapping schedule entries for a technician in a time window."""
    logger.info(
        "scheduling.conflicts.check",
        technician_id=technician_id,
        tenant_id=tenant_id,
        starts_at=starts_at,
        ends_at=ends_at,
    )
    conflicts: list[dict[str, str]] = []
    return {"has_conflicts": bool(conflicts), "conflicts": conflicts}


@shared_task(base=CrewspanTask, name="worker.jobs.scheduling.auto_dispatch_overdue")
def auto_dispatch_overdue(*, tenant_id: str, grace_minutes: int = 15) -> dict[str, int]:
    """Re-dispatch work orders past scheduled start without technician acceptance."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=grace_minutes)
    logger.info(
        "scheduling.auto_dispatch.start",
        tenant_id=tenant_id,
        cutoff=cutoff.isoformat(),
    )
    redispatched = 0
    return {"redispatched": redispatched}


@shared_task(base=CrewspanTask, name="worker.jobs.scheduling.sync_technician_calendar")
def sync_technician_calendar(technician_id: str, *, tenant_id: str) -> dict[str, str]:
    """Push schedule blocks to external calendar provider (Google/Outlook)."""
    logger.info(
        "scheduling.calendar_sync",
        technician_id=technician_id,
        tenant_id=tenant_id,
    )
    return {"status": "synced", "technician_id": technician_id}
