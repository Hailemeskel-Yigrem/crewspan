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
