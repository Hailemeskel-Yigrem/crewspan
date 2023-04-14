"""Shared validation helpers for API inputs and business rules."""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.errors import ValidationAppError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PHONE_RE = re.compile(r"^\+?[0-9\s\-().]{7,32}$")


def require_non_empty(value: str | None, *, field: str) -> str:
    if value is None or not str(value).strip():
        raise ValidationAppError(f"{field} is required", field=field)
    return str(value).strip()


def validate_email(value: str | None, *, field: str = "email") -> str:
    normalized = require_non_empty(value, field=field).lower()
    if not EMAIL_RE.match(normalized):
        raise ValidationAppError("Invalid email address", field=field)
    return normalized


def validate_slug(value: str, *, field: str = "slug") -> str:
    cleaned = value.strip().lower()
    if not SLUG_RE.match(cleaned):
        raise ValidationAppError("Slug must be lowercase alphanumeric with hyphens", field=field)
    return cleaned


def validate_phone(value: str | None, *, field: str = "phone", required: bool = False) -> str | None:
    if value is None or not value.strip():
        if required:
            raise ValidationAppError(f"{field} is required", field=field)
        return None
    cleaned = value.strip()
    if not PHONE_RE.match(cleaned):
        raise ValidationAppError("Invalid phone number format", field=field)
    return cleaned


def validate_enum(value: str, allowed: set[str], *, field: str) -> str:
    if value not in allowed:
        raise ValidationAppError(
            f"{field} must be one of: {', '.join(sorted(allowed))}",
            field=field,
        )
    return value


def validate_positive_decimal(value: Decimal | None, *, field: str, allow_zero: bool = False) -> Decimal | None:
    if value is None:
        return None
    if value < 0 or (not allow_zero and value == 0):
        raise ValidationAppError(f"{field} must be positive", field=field)
    return value


def validate_date_order(start: datetime | None, end: datetime | None, *, start_field: str, end_field: str) -> None:
    if start is not None and end is not None and end < start:
        raise ValidationAppError(f"{end_field} must be on or after {start_field}")


def validate_uuid(value: str | UUID, *, field: str) -> UUID:
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ValidationAppError(f"Invalid UUID for {field}", field=field) from exc


def clamp_page_size(page_size: int, *, minimum: int = 1, maximum: int = 200) -> int:
    if page_size < minimum:
        raise ValidationAppError(f"page_size must be >= {minimum}", field="page_size")
    return min(page_size, maximum)
