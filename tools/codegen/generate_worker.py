"""Generate the Fieldspan background worker application tree."""

from __future__ import annotations

import textwrap
from pathlib import Path

from tools.codegen.api_templates import finalize_source


def _write(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = finalize_source(content) if path.suffix == ".py" else content
    path.write_text(normalized, encoding="utf-8")
    return len(normalized.splitlines())


def _worker_pyproject() -> str:
    return textwrap.dedent(
        """\
        [build-system]
        requires = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "fieldspan-worker"
        version = "0.1.0"
        description = "Fieldspan background job worker"
        requires-python = ">=3.11"
        dependencies = [
            "celery[redis]>=5.3.0",
            "redis>=5.0.0",
            "sqlalchemy[asyncio]>=2.0.25",
            "asyncpg>=0.29.0",
            "pydantic>=2.6.0",
            "pydantic-settings>=2.2.0",
            "structlog>=24.1.0",
            "httpx>=0.27.0",
        ]

        [tool.setuptools.packages.find]
        where = ["."]
        include = ["worker*"]
        """
    )


def _worker_requirements() -> str:
    return textwrap.dedent(
        """\
        celery[redis]>=5.3.0
        redis>=5.0.0
        sqlalchemy[asyncio]>=2.0.25
        asyncpg>=0.29.0
        pydantic>=2.6.0
        pydantic-settings>=2.2.0
        structlog>=24.1.0
        httpx>=0.27.0
        """
    )


def _celery_app_py() -> str:
    return textwrap.dedent(
        '''\
        """Celery application factory for Fieldspan workers."""

        from __future__ import annotations

        from celery import Celery

        from worker.config import settings
        from worker.logging_config import configure_logging

        configure_logging()

        celery_app = Celery(
            "fieldspan-worker",
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend,
            include=[
                "worker.jobs.notifications",
                "worker.jobs.scheduling",
                "worker.jobs.invoicing",
                "worker.jobs.webhooks",
                "worker.jobs.reports",
            ],
        )

        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            task_acks_late=True,
            worker_prefetch_multiplier=1,
            task_default_queue="fieldspan.default",
            task_routes={
                "worker.jobs.notifications.*": {"queue": "fieldspan.notifications"},
                "worker.jobs.scheduling.*": {"queue": "fieldspan.scheduling"},
                "worker.jobs.invoicing.*": {"queue": "fieldspan.invoicing"},
                "worker.jobs.webhooks.*": {"queue": "fieldspan.webhooks"},
                "worker.jobs.reports.*": {"queue": "fieldspan.reports"},
            },
            beat_schedule={
                "dispatch-schedule-reminders": {
                    "task": "worker.jobs.scheduling.send_upcoming_appointment_reminders",
                    "schedule": 300.0,
                },
                "process-pending-invoices": {
                    "task": "worker.jobs.invoicing.process_draft_invoices",
                    "schedule": 900.0,
                },
                "retry-failed-webhooks": {
                    "task": "worker.jobs.webhooks.retry_failed_deliveries",
                    "schedule": 600.0,
                },
            },
        )
        '''
    )


def _worker_config_py() -> str:
    return textwrap.dedent(
        '''\
        """Worker configuration."""

        from __future__ import annotations

        from pydantic_settings import BaseSettings, SettingsConfigDict


        class WorkerSettings(BaseSettings):
            model_config = SettingsConfigDict(env_file=".env", env_prefix="FIELDSPAN_", extra="ignore")

            environment: str = "development"
            database_url: str = "postgresql+asyncpg://fieldspan:fieldspan@localhost:5432/fieldspan"
            celery_broker_url: str = "redis://localhost:6379/1"
            celery_result_backend: str = "redis://localhost:6379/2"
            log_level: str = "INFO"
            webhook_timeout_seconds: int = 30
            notification_from_email: str = "noreply@fieldspan.local"
            report_export_dir: str = "/tmp/fieldspan/exports"


        settings = WorkerSettings()
        '''
    )


def _worker_logging_py() -> str:
    return textwrap.dedent(
        '''\
        """Worker structured logging."""

        from __future__ import annotations

        import logging
        import sys

        import structlog

        from worker.config import settings


        def configure_logging() -> None:
            logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
            structlog.configure(
                processors=[
                    structlog.processors.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.JSONRenderer(),
                ],
                wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(),
                cache_logger_on_first_use=True,
            )
        '''
    )


def _worker_base_py() -> str:
    return textwrap.dedent(
        '''\
        """Shared worker utilities and base task class."""

        from __future__ import annotations

        from typing import Any
        from uuid import UUID

        import structlog
        from celery import Task

        logger = structlog.get_logger(__name__)


        class FieldspanTask(Task):
            """Base task with structured logging and retry defaults."""

            autoretry_for = (Exception,)
            retry_backoff = True
            retry_backoff_max = 600
            retry_jitter = True
            max_retries = 5

            def on_failure(self, exc: Exception, task_id: str, args: tuple[Any, ...], kwargs: dict[str, Any], einfo: object) -> None:
                logger.error(
                    "task.failed",
                    task_name=self.name,
                    task_id=task_id,
                    error=str(exc),
                )


        def parse_uuid(value: str) -> UUID:
            return UUID(value)
        '''
    )


def _notifications_job_py() -> str:
    return textwrap.dedent(
        '''\
        """Notification delivery background jobs."""

        from __future__ import annotations

        from datetime import datetime, timezone
        from uuid import UUID

        import structlog
        from celery import shared_task

        from worker.base import FieldspanTask
        from worker.config import settings

        logger = structlog.get_logger(__name__)


        @shared_task(base=FieldspanTask, name="worker.jobs.notifications.send_email")
        def send_email(notification_id: str, *, tenant_id: str) -> dict[str, str]:
            \"\"\"Deliver a queued email notification by ID.\"\"\"
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


        @shared_task(base=FieldspanTask, name="worker.jobs.notifications.send_sms")
        def send_sms(notification_id: str, *, tenant_id: str, phone: str) -> dict[str, str]:
            \"\"\"Deliver SMS notification to technician or customer contact.\"\"\"
            if not phone.startswith("+"):
                raise ValueError("Phone number must be E.164 format")
            logger.info(
                "notification.send_sms",
                notification_id=notification_id,
                tenant_id=tenant_id,
                phone=phone[:4] + "****",
            )
            return {"status": "sent", "notification_id": notification_id}


        @shared_task(base=FieldspanTask, name="worker.jobs.notifications.process_pending_batch")
        def process_pending_batch(*, tenant_id: str | None = None, limit: int = 100) -> dict[str, int]:
            \"\"\"Poll pending notifications and enqueue channel-specific delivery tasks.\"\"\"
            logger.info("notification.batch.start", tenant_id=tenant_id, limit=limit)
            processed = 0
            failed = 0
            # Stub: would query notifications table where status='pending'
            logger.info("notification.batch.complete", processed=processed, failed=failed)
            return {"processed": processed, "failed": failed}


        @shared_task(base=FieldspanTask, name="worker.jobs.notifications.dispatch_work_order_update")
        def dispatch_work_order_update(
            work_order_id: str,
            *,
            tenant_id: str,
            event: str,
            recipient_ids: list[str] | None = None,
        ) -> dict[str, object]:
            \"\"\"Fan out work order status change notifications to subscribed contacts.\"\"\"
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
        '''
    )


def _scheduling_job_py() -> str:
    return textwrap.dedent(
        '''\
        """Scheduling reminder and dispatch background jobs."""

        from __future__ import annotations

        from datetime import datetime, timedelta, timezone

        import structlog
        from celery import shared_task

        from worker.base import FieldspanTask

        logger = structlog.get_logger(__name__)


        @shared_task(base=FieldspanTask, name="worker.jobs.scheduling.send_upcoming_appointment_reminders")
        def send_upcoming_appointment_reminders(*, horizon_hours: int = 24) -> dict[str, int]:
            \"\"\"Find appointments starting within horizon and notify assigned technicians.\"\"\"
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


        @shared_task(base=FieldspanTask, name="worker.jobs.scheduling.detect_schedule_conflicts")
        def detect_schedule_conflicts(
            technician_id: str,
            *,
            tenant_id: str,
            starts_at: str,
            ends_at: str,
        ) -> dict[str, object]:
            \"\"\"Detect overlapping schedule entries for a technician in a time window.\"\"\"
            logger.info(
                "scheduling.conflicts.check",
                technician_id=technician_id,
                tenant_id=tenant_id,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            conflicts: list[dict[str, str]] = []
            return {"has_conflicts": bool(conflicts), "conflicts": conflicts}


        @shared_task(base=FieldspanTask, name="worker.jobs.scheduling.auto_dispatch_overdue")
        def auto_dispatch_overdue(*, tenant_id: str, grace_minutes: int = 15) -> dict[str, int]:
            \"\"\"Re-dispatch work orders past scheduled start without technician acceptance.\"\"\"
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=grace_minutes)
            logger.info(
                "scheduling.auto_dispatch.start",
                tenant_id=tenant_id,
                cutoff=cutoff.isoformat(),
            )
            redispatched = 0
            return {"redispatched": redispatched}


        @shared_task(base=FieldspanTask, name="worker.jobs.scheduling.sync_technician_calendar")
        def sync_technician_calendar(technician_id: str, *, tenant_id: str) -> dict[str, str]:
            \"\"\"Push schedule blocks to external calendar provider (Google/Outlook).\"\"\"
            logger.info(
                "scheduling.calendar_sync",
                technician_id=technician_id,
                tenant_id=tenant_id,
            )
            return {"status": "synced", "technician_id": technician_id}
        '''
    )


def _invoicing_job_py() -> str:
    return textwrap.dedent(
        '''\
        """Invoice generation and payment processing jobs."""

        from __future__ import annotations

        from datetime import date
        from decimal import Decimal

        import structlog
        from celery import shared_task

        from worker.base import FieldspanTask

        logger = structlog.get_logger(__name__)


        @shared_task(base=FieldspanTask, name="worker.jobs.invoicing.generate_from_work_order")
        def generate_from_work_order(work_order_id: str, *, tenant_id: str) -> dict[str, str]:
            \"\"\"Create draft invoice from completed work order labor and parts.\"\"\"
            logger.info(
                "invoicing.generate.start",
                work_order_id=work_order_id,
                tenant_id=tenant_id,
            )
            invoice_number = f"INV-{work_order_id[:8].upper()}"
            subtotal = Decimal("0.00")
            tax_rate = Decimal("0.0825")
            tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"))
            total = subtotal + tax_amount
            logger.info(
                "invoicing.generate.complete",
                work_order_id=work_order_id,
                invoice_number=invoice_number,
                total=str(total),
            )
            return {
                "invoice_number": invoice_number,
                "subtotal": str(subtotal),
                "tax_amount": str(tax_amount),
                "total": str(total),
            }


        @shared_task(base=FieldspanTask, name="worker.jobs.invoicing.process_draft_invoices")
        def process_draft_invoices(*, tenant_id: str | None = None) -> dict[str, int]:
            \"\"\"Finalize and send draft invoices past issue date.\"\"\"
            today = date.today()
            logger.info("invoicing.process_drafts", tenant_id=tenant_id, issue_date=str(today))
            finalized = 0
            sent = 0
            return {"finalized": finalized, "sent": sent}


        @shared_task(base=FieldspanTask, name="worker.jobs.invoicing.send_payment_reminders")
        def send_payment_reminders(*, days_overdue: int = 7) -> dict[str, int]:
            \"\"\"Email customers with overdue unpaid invoices.\"\"\"
            logger.info("invoicing.payment_reminders", days_overdue=days_overdue)
            reminders = 0
            return {"reminders_sent": reminders}


        @shared_task(base=FieldspanTask, name="worker.jobs.invoicing.recalculate_invoice_totals")
        def recalculate_invoice_totals(invoice_id: str, *, tenant_id: str) -> dict[str, str]:
            \"\"\"Recompute invoice subtotal, tax, and total from line items.\"\"\"
            logger.info("invoicing.recalculate", invoice_id=invoice_id, tenant_id=tenant_id)
            return {"invoice_id": invoice_id, "status": "recalculated"}
        '''
    )


def _webhooks_job_py() -> str:
    return textwrap.dedent(
        '''\
        """Webhook delivery and retry background jobs."""

        from __future__ import annotations

        import hashlib
        import hmac
        import json
        from datetime import datetime, timezone

        import httpx
        import structlog
        from celery import shared_task

        from worker.base import FieldspanTask
        from worker.config import settings

        logger = structlog.get_logger(__name__)


        def _sign_payload(secret: str, payload: bytes) -> str:
            return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


        @shared_task(base=FieldspanTask, name="worker.jobs.webhooks.deliver_event")
        def deliver_event(
            webhook_id: str,
            *,
            tenant_id: str,
            event_type: str,
            payload: dict[str, object],
        ) -> dict[str, object]:
            \"\"\"Deliver a single webhook event with HMAC signature.\"\"\"
            logger.info(
                "webhook.deliver.start",
                webhook_id=webhook_id,
                tenant_id=tenant_id,
                event_type=event_type,
            )
            body = json.dumps({"event": event_type, "data": payload, "tenant_id": tenant_id}).encode()
            headers = {
                "Content-Type": "application/json",
                "X-Fieldspan-Event": event_type,
                "X-Fieldspan-Timestamp": datetime.now(timezone.utc).isoformat(),
            }
            # Production would load webhook URL and secret from database
            url = "https://example.com/webhook"
            secret = "placeholder-secret"
            headers["X-Fieldspan-Signature"] = _sign_payload(secret, body)
            try:
                with httpx.Client(timeout=settings.webhook_timeout_seconds) as client:
                    response = client.post(url, content=body, headers=headers)
                    response.raise_for_status()
            except httpx.HTTPError as exc:
                logger.error("webhook.deliver.failed", webhook_id=webhook_id, error=str(exc))
                raise
            logger.info("webhook.deliver.complete", webhook_id=webhook_id, status=response.status_code)
            return {"webhook_id": webhook_id, "status_code": response.status_code}


        @shared_task(base=FieldspanTask, name="worker.jobs.webhooks.retry_failed_deliveries")
        def retry_failed_deliveries(*, max_attempts: int = 5) -> dict[str, int]:
            \"\"\"Retry webhook deliveries that failed and are under max attempts.\"\"\"
            logger.info("webhook.retry.scan", max_attempts=max_attempts)
            retried = 0
            permanently_failed = 0
            return {"retried": retried, "permanently_failed": permanently_failed}


        @shared_task(base=FieldspanTask, name="worker.jobs.webhooks.disable_noisy_endpoints")
        def disable_noisy_endpoints(*, failure_threshold: int = 10) -> dict[str, int]:
            \"\"\"Disable webhooks exceeding consecutive failure threshold.\"\"\"
            logger.info("webhook.disable_noisy", failure_threshold=failure_threshold)
            disabled = 0
            return {"disabled": disabled}
        '''
    )


def _reports_job_py() -> str:
    return textwrap.dedent(
        '''\
        """Report export and analytics background jobs."""

        from __future__ import annotations

        import csv
        from datetime import date
        from pathlib import Path

        import structlog
        from celery import shared_task

        from worker.base import FieldspanTask
        from worker.config import settings

        logger = structlog.get_logger(__name__)


        @shared_task(base=FieldspanTask, name="worker.jobs.reports.export_work_orders_csv")
        def export_work_orders_csv(
            *,
            tenant_id: str,
            start_date: str,
            end_date: str,
            requested_by_id: str,
        ) -> dict[str, str]:
            \"\"\"Export work orders in date range to CSV and return file path.\"\"\"
            export_dir = Path(settings.report_export_dir)
            export_dir.mkdir(parents=True, exist_ok=True)
            filename = f"work_orders_{tenant_id}_{start_date}_{end_date}.csv"
            filepath = export_dir / filename
            logger.info(
                "reports.export.work_orders.start",
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                requested_by_id=requested_by_id,
            )
            with filepath.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow([
                    "order_number", "status", "priority", "customer_id",
                    "scheduled_start", "scheduled_end", "created_at",
                ])
                # Stub: would query work_orders for tenant and date range
            logger.info("reports.export.work_orders.complete", filepath=str(filepath))
            return {"filepath": str(filepath), "format": "csv"}


        @shared_task(base=FieldspanTask, name="worker.jobs.reports.export_sla_breaches")
        def export_sla_breaches(*, tenant_id: str, month: str) -> dict[str, str]:
            \"\"\"Generate monthly SLA breach summary report.\"\"\"
            logger.info("reports.export.sla_breaches", tenant_id=tenant_id, month=month)
            export_dir = Path(settings.report_export_dir)
            export_dir.mkdir(parents=True, exist_ok=True)
            filepath = export_dir / f"sla_breaches_{tenant_id}_{month}.csv"
            with filepath.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow([
                    "work_order_id", "breach_type", "expected_at",
                    "detected_at", "minutes_overdue", "escalation_level",
                ])
            return {"filepath": str(filepath)}


        @shared_task(base=FieldspanTask, name="worker.jobs.reports.technician_utilization")
        def technician_utilization(
            *,
            tenant_id: str,
            period_start: str,
            period_end: str,
        ) -> dict[str, object]:
            \"\"\"Compute technician utilization metrics for a reporting period.\"\"\"
            logger.info(
                "reports.technician_utilization",
                tenant_id=tenant_id,
                period_start=period_start,
                period_end=period_end,
            )
            metrics: list[dict[str, object]] = []
            return {"period_start": period_start, "period_end": period_end, "technicians": metrics}


        @shared_task(base=FieldspanTask, name="worker.jobs.reports.inventory_valuation")
        def inventory_valuation(*, tenant_id: str, as_of: str | None = None) -> dict[str, str]:
            \"\"\"Calculate total inventory valuation across all locations.\"\"\"
            valuation_date = as_of or date.today().isoformat()
            logger.info("reports.inventory_valuation", tenant_id=tenant_id, as_of=valuation_date)
            return {"tenant_id": tenant_id, "as_of": valuation_date, "total_value": "0.00"}
        '''
    )


def _worker_dockerfile() -> str:
    return textwrap.dedent(
        """\
        FROM python:3.11-slim

        WORKDIR /app

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        ENV FIELDSPAN_ENVIRONMENT=production

        CMD ["celery", "-A", "worker.celery_app:celery_app", "worker", "--loglevel=info", "-Q", "fieldspan.default,fieldspan.notifications,fieldspan.scheduling,fieldspan.invoicing,fieldspan.webhooks,fieldspan.reports"]
        """
    )


def _worker_dockerfile_beat() -> str:
    return textwrap.dedent(
        """\
        FROM python:3.11-slim

        WORKDIR /app

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        CMD ["celery", "-A", "worker.celery_app:celery_app", "beat", "--loglevel=info"]
        """
    )


def generate_worker_tree(root: Path) -> dict[str, int]:
    """Write the Fieldspan worker tree under *root*.

    Returns a mapping of relative path -> line count for generated files.
    """
    worker_root = root / "apps" / "worker"
    stats: dict[str, int] = {}

    def record(rel: str, content: str) -> None:
        stats[rel] = _write(worker_root / rel, content)

    record("pyproject.toml", _worker_pyproject())
    record("requirements.txt", _worker_requirements())
    record("Dockerfile", _worker_dockerfile())
    record("Dockerfile.beat", _worker_dockerfile_beat())
    record("worker/__init__.py", '"""Fieldspan worker package."""\n')
    record("worker/config.py", _worker_config_py())
    record("worker/logging_config.py", _worker_logging_py())
    record("worker/celery_app.py", _celery_app_py())
    record("worker/base.py", _worker_base_py())
    record("worker/jobs/__init__.py", '"""Background job modules."""\n')
    record("worker/jobs/notifications.py", _notifications_job_py())
    record("worker/jobs/scheduling.py", _scheduling_job_py())
    record("worker/jobs/invoicing.py", _invoicing_job_py())
    record("worker/jobs/webhooks.py", _webhooks_job_py())
    record("worker/jobs/reports.py", _reports_job_py())

    return stats


def print_generation_summary(stats: dict[str, int]) -> None:
    total_lines = sum(stats.values())
    total_files = len(stats)
    print(f"Generated {total_files} worker files, ~{total_lines:,} lines")
    for rel, lines in sorted(stats.items()):
        print(f"  {rel}: {lines} lines")


if __name__ == "__main__":
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    summary = generate_worker_tree(repo_root)
    print_generation_summary(summary)
