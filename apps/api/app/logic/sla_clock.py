"""Deterministic SLA countdown, business-hours aware breach detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


class SlaSeverity(str, Enum):
    OK = "ok"
    WARNING = "warning"
    BREACHED = "breached"


@dataclass(frozen=True, slots=True)
class SlaWindow:
    started_at: datetime
    target_minutes: int
    warning_threshold_pct: float = 0.85

    @property
    def due_at(self) -> datetime:
        return self.started_at + timedelta(minutes=self.target_minutes)

    def elapsed_minutes(self, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)
        return max(0.0, (now - self.started_at).total_seconds() / 60.0)

    def remaining_minutes(self, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)
        return (self.due_at - now).total_seconds() / 60.0

    def progress_pct(self, now: datetime | None = None) -> float:
        if self.target_minutes <= 0:
            return 100.0
        return min(100.0, (self.elapsed_minutes(now) / self.target_minutes) * 100.0)

    def is_breached(self, now: datetime | None = None) -> bool:
        return self.remaining_minutes(now) < 0

    def severity(self, now: datetime | None = None) -> SlaSeverity:
        if self.is_breached(now):
            return SlaSeverity.BREACHED
        pct = self.progress_pct(now) / 100.0
        if pct >= self.warning_threshold_pct:
            return SlaSeverity.WARNING
        return SlaSeverity.OK


def compare_windows(a: SlaWindow, b: SlaWindow, now: datetime | None = None) -> SlaWindow:
    """Return whichever window breaches soonest (most urgent)."""
    return a if a.remaining_minutes(now) <= b.remaining_minutes(now) else b
