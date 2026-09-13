"""Finite state machine for Dispatch with transition guards and history."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted", "active", "cancelled", "pending"},
    "pending": {"approved", "rejected", "cancelled", "active"},
    "submitted": {"assigned", "in_progress", "cancelled"},
    "assigned": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "completed", "cancelled"},
    "blocked": {"in_progress", "cancelled", "active"},
    "approved": {"fulfilled", "rejected", "cancelled"},
    "active": {"blocked", "completed", "cancelled", "inactive"},
    "fulfilled": set(),
    "completed": set(),
    "cancelled": set(),
    "rejected": set(),
}

TERMINAL = frozenset({"completed", "cancelled", "rejected", "fulfilled"})


@dataclass(frozen=True, slots=True)
class TransitionRecord:
    from_status: str
    to_status: str
    valid: bool


def can_transition(current: str, target: str) -> bool:
    if current == target:
        return True
    return target in TRANSITIONS.get(current, set())


def allowed_targets(current: str) -> set[str]:
    return set(TRANSITIONS.get(current, set()))


def assert_transition(current: str, target: str) -> None:
    if not can_transition(current, target):
        allowed = ", ".join(sorted(allowed_targets(current))) or "none"
        raise ValueError(
            f"Invalid dispatch transition {current} -> {target}; allowed: {allowed}"
        )


def validate_path(states: Iterable[str]) -> list[TransitionRecord]:
    """Validate a sequence of statuses representing a lifecycle path."""
    seq = list(states)
    if not seq:
        return []
    records: list[TransitionRecord] = []
    for idx in range(len(seq) - 1):
        src, dst = seq[idx], seq[idx + 1]
        ok = can_transition(src, dst)
        records.append(TransitionRecord(from_status=src, to_status=dst, valid=ok))
        if not ok:
            break
    return records


def is_terminal(status: str) -> bool:
    return status in TERMINAL
