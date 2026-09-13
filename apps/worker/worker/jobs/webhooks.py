"""Webhook delivery and retry background jobs."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime

import httpx
import structlog
from celery import shared_task

from worker.base import CrewspanTask
from worker.config import settings

logger = structlog.get_logger(__name__)


def _sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


@shared_task(base=CrewspanTask, name="worker.jobs.webhooks.deliver_event")
def deliver_event(
    webhook_id: str,
    *,
    tenant_id: str,
    event_type: str,
    payload: dict[str, object],
) -> dict[str, object]:
    """Deliver a single webhook event with HMAC signature."""
    logger.info(
        "webhook.deliver.start",
        webhook_id=webhook_id,
        tenant_id=tenant_id,
        event_type=event_type,
    )
    body = json.dumps({"event": event_type, "data": payload, "tenant_id": tenant_id}).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Crewspan-Event": event_type,
        "X-Crewspan-Timestamp": datetime.now(UTC).isoformat(),
    }
    # Until the endpoint is read from the webhook record, the target and its
    # signing secret come from configuration. Without both, do nothing rather
    # than post tenant data to a placeholder host.
    if not settings.webhook_target_url or not settings.webhook_signing_secret:
        logger.warning(
            "webhook.deliver.skipped",
            webhook_id=webhook_id,
            reason="webhook_target_url or webhook_signing_secret is not configured",
        )
        return {"webhook_id": webhook_id, "status_code": None, "skipped": True}

    url = settings.webhook_target_url
    headers["X-Crewspan-Signature"] = _sign_payload(settings.webhook_signing_secret, body)
    try:
        with httpx.Client(timeout=settings.webhook_timeout_seconds) as client:
            response = client.post(url, content=body, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("webhook.deliver.failed", webhook_id=webhook_id, error=str(exc))
        raise
    logger.info("webhook.deliver.complete", webhook_id=webhook_id, status=response.status_code)
    return {"webhook_id": webhook_id, "status_code": response.status_code}


@shared_task(base=CrewspanTask, name="worker.jobs.webhooks.retry_failed_deliveries")
def retry_failed_deliveries(*, max_attempts: int = 5) -> dict[str, int]:
    """Retry webhook deliveries that failed and are under max attempts."""
    logger.info("webhook.retry.scan", max_attempts=max_attempts)
    retried = 0
    permanently_failed = 0
    return {"retried": retried, "permanently_failed": permanently_failed}


@shared_task(base=CrewspanTask, name="worker.jobs.webhooks.disable_noisy_endpoints")
def disable_noisy_endpoints(*, failure_threshold: int = 10) -> dict[str, int]:
    """Disable webhooks exceeding consecutive failure threshold."""
    logger.info("webhook.disable_noisy", failure_threshold=failure_threshold)
    disabled = 0
    return {"disabled": disabled}
