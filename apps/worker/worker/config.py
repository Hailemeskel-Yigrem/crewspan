"""Worker configuration."""

from __future__ import annotations

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
    report_export_dir: str = "/tmp/crewspan/exports"


settings = WorkerSettings()
