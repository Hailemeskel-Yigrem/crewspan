"""Idempotency key registry for safe mutation retries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

Status = Literal["started", "completed", "failed"]


@dataclass
class IdempotencyRecord:
    key: str
    status: Status
    result: Any = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None


@dataclass
class IdempotencyStore:
    _seen: dict[str, IdempotencyRecord] = field(default_factory=dict)
    ttl: timedelta = timedelta(hours=24)

    def _purge_expired(self) -> None:
        now = datetime.now(UTC)
        expired = [k for k, v in self._seen.items() if v.expires_at and v.expires_at <= now]
        for key in expired:
            del self._seen[key]

    def begin(self, key: str) -> bool:
        """Return True if this is the first time the key is seen."""
        self._purge_expired()
        if key in self._seen:
            return False
        self._seen[key] = IdempotencyRecord(
            key=key,
            status="started",
            expires_at=datetime.now(UTC) + self.ttl,
        )
        return True

    def complete(self, key: str, result: Any) -> None:
        record = self._seen.setdefault(key, IdempotencyRecord(key=key, status="started"))
        record.status = "completed"
        record.result = result

    def fail(self, key: str, error: str) -> None:
        record = self._seen.setdefault(key, IdempotencyRecord(key=key, status="started"))
        record.status = "failed"
        record.result = {"error": error}

    def get(self, key: str) -> Any | None:
        self._purge_expired()
        row = self._seen.get(key)
        if not row or row.status != "completed":
            return None
        return row.result

    def status(self, key: str) -> Status | None:
        row = self._seen.get(key)
        return row.status if row else None
