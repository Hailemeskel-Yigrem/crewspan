"""Detect overlapping schedule intervals, gaps, and technician double-booking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class Interval:
    id: str
    start: datetime
    end: datetime
    technician_id: str | None = None

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(f"interval {self.id}: end must be after start")

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end

    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60.0


def find_conflicts(intervals: list[Interval]) -> list[tuple[str, str]]:
    ordered = sorted(intervals, key=lambda item: item.start)
    conflicts: list[tuple[str, str]] = []
    for i, left in enumerate(ordered):
        for right in ordered[i + 1 :]:
            if right.start >= left.end:
                break
            if left.overlaps(right):
                if left.technician_id and right.technician_id and left.technician_id != right.technician_id:
                    continue
                conflicts.append((left.id, right.id))
    return conflicts


def find_gaps(intervals: list[Interval], *, min_gap_minutes: float = 15.0) -> list[tuple[str, str, float]]:
    ordered = sorted(intervals, key=lambda item: item.start)
    gaps: list[tuple[str, str, float]] = []
    for left, right in zip(ordered, ordered[1:]):
        gap_minutes = (right.start - left.end).total_seconds() / 60.0
        if gap_minutes >= min_gap_minutes:
            gaps.append((left.id, right.id, gap_minutes))
    return gaps


def total_booked_minutes(intervals: list[Interval]) -> float:
    return sum(i.duration_minutes() for i in intervals)


def fits_within(
    candidate: Interval,
    existing: list[Interval],
    *,
    buffer_minutes: float = 0.0,
) -> bool:
    buffer = timedelta(minutes=buffer_minutes)
    padded = Interval(
        id=candidate.id,
        start=candidate.start,
        end=candidate.end + buffer,
        technician_id=candidate.technician_id,
    )
    return not find_conflicts([padded, *existing])
# history-note: evolutionary edit 32
