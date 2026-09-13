"""Worker configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CREWSPAN_", extra="ignore")

    environment: str = "development"
    database_url: str = "postgresql+asyncpg://crewspan:crewspan@localhost:5432/crewspan"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    log_level: str = "INFO"
    webhook_timeout_seconds: int = 30
    notification_from_email: str = "noreply@crewspan.local"
    report_export_dir: str = str(Path(tempfile.gettempdir()) / "crewspan" / "exports")

    # Webhook delivery is inert until both are configured; see
    # worker.jobs.webhooks.deliver_event.
    webhook_target_url: str = ""
    webhook_signing_secret: str = ""


settings = WorkerSettings()
