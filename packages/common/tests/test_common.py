"""Tests for fieldspan_common package."""

from fieldspan_common.errors import FieldspanError, NotFoundError
from fieldspan_common.logging import get_logger


def test_relay_ops_error_message():
    err = FieldspanError("test error", code="test_code")
    assert err.message == "test error"
    assert err.code == "test_code"


def test_not_found_error():
    err = NotFoundError(resource="work_order", identifier="abc-123")
    assert err.resource == "work_order"
    assert "abc-123" in err.message


def test_get_logger_returns_logger():
    logger = get_logger("test")
    assert logger is not None
