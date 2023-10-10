"""Shared worker utilities and base task class."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from celery import Task

logger = structlog.get_logger(__name__)


class RelayOpsTask(Task):
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
