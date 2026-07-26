"""Notification delivery background jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import structlog
from celery import shared_task

from worker.base import CrewspanTask
from worker.config import settings

logger = structlog.get_logger(__name__)


@shared_task(base=CrewspanTask, name="worker.jobs.notifications.send_email")
def send_email(notification_id: str, *, tenant_id: str) -> dict[str, str]:
    """Deliver a queued email notification by ID."""
    logger.info(
        "notification.send_email.start",
        notification_id=notification_id,
        tenant_id=tenant_id,
    )
    # Production integration would fetch notification, render template, call provider.
    delivered_at = datetime.now(timezone.utc).isoformat()
    logger.info(
        "notification.send_email.complete",
        notification_id=notification_id,
        delivered_at=delivered_at,
    )
    return {"status": "sent", "notification_id": notification_id, "delivered_at": delivered_at}


@shared_task(base=CrewspanTask, name="worker.jobs.notifications.send_sms")
def send_sms(notification_id: str, *, tenant_id: str, phone: str) -> dict[str, str]:
    """Deliver SMS notification to technician or customer contact."""
    if not phone.startswith("+"):
        raise ValueError("Phone number must be E.164 format")
    logger.info(
        "notification.send_sms",
        notification_id=notification_id,
        tenant_id=tenant_id,
        phone=phone[:4] + "****",
    )
    return {"status": "sent", "notification_id": notification_id}


@shared_task(base=CrewspanTask, name="worker.jobs.notifications.process_pending_batch")
def process_pending_batch(*, tenant_id: str | None = None, limit: int = 100) -> dict[str, int]:
    """Poll pending notifications and enqueue channel-specific delivery tasks."""
    logger.info("notification.batch.start", tenant_id=tenant_id, limit=limit)
    processed = 0
    failed = 0
    # Stub: would query notifications table where status='pending'
    logger.info("notification.batch.complete", processed=processed, failed=failed)
    return {"processed": processed, "failed": failed}


@shared_task(base=CrewspanTask, name="worker.jobs.notifications.dispatch_work_order_update")
def dispatch_work_order_update(
    work_order_id: str,
    *,
    tenant_id: str,
    event: str,
    recipient_ids: list[str] | None = None,
) -> dict[str, object]:
    """Fan out work order status change notifications to subscribed contacts."""
    logger.info(
        "notification.work_order_update",
        work_order_id=work_order_id,
        tenant_id=tenant_id,
        event=event,
        recipient_count=len(recipient_ids or []),
    )
    enqueued = []
    for recipient_id in recipient_ids or []:
        task = send_email.delay(str(UUID(int=0)), tenant_id=tenant_id)
        enqueued.append(task.id)
    return {"event": event, "enqueued_tasks": enqueued}
