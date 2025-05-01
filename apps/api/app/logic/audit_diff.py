"""Compute audit diffs, redact secrets, and summarize entity changes."""

from __future__ import annotations

from typing import Any

SENSITIVE_KEYS = frozenset({"password", "password_hash", "secret", "token", "api_key"})


def _redact(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS or key.endswith("_hash"):
        return "***REDACTED***"
    return value


def diff_entities(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
    keys = set(before) | set(after)
    changes: dict[str, dict[str, Any]] = {}
    for key in sorted(keys):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            changes[key] = {"from": _redact(key, old), "to": _redact(key, new)}
    return changes


def has_changes(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return bool(diff_entities(before, after))


def summarize_changes(changes: dict[str, dict[str, Any]], *, max_fields: int = 5) -> str:
    if not changes:
        return "no changes"
    parts = []
    for key in list(changes)[:max_fields]:
        parts.append(f"{key}: {changes[key]['from']!r} -> {changes[key]['to']!r}")
    if len(changes) > max_fields:
        parts.append(f"+{len(changes) - max_fields} more")
    return "; ".join(parts)


def merge_snapshots(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(patch)
    return merged
# history-note: evolutionary edit 4
