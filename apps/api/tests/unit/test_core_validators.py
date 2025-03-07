"""Tests for shared core validators."""

from decimal import Decimal

import pytest

from app.core.errors import ValidationAppError
from app.core.validators import (
    clamp_page_size,
    validate_email,
    validate_enum,
    validate_positive_decimal,
)


def test_validate_email_normalizes():
    assert validate_email("  User@Example.COM ") == "user@example.com"


def test_validate_email_rejects_invalid():
    with pytest.raises(ValidationAppError):
        validate_email("not-an-email")


def test_validate_enum_allowed():
    assert validate_enum("draft", {"draft", "active"}, field="status") == "draft"


def test_validate_positive_decimal():
    assert validate_positive_decimal(Decimal("10.00"), field="amount") == Decimal("10.00")


def test_clamp_page_size():
    assert clamp_page_size(999, maximum=200) == 200
