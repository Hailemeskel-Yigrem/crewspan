import pytest

from app.domains.schedule.state_machine import (
    assert_transition,
    can_transition,
    is_terminal,
    validate_path,
)


def test_schedule_draft_to_active() -> None:
    assert can_transition("draft", "active")


def test_schedule_completed_is_terminal() -> None:
    assert is_terminal("completed")
    with pytest.raises(ValueError):
        assert_transition("completed", "active")


def test_schedule_validate_path_success() -> None:
    records = validate_path(["draft", "active", "completed"])
    assert all(r.valid for r in records)


def test_schedule_validate_path_detects_invalid() -> None:
    records = validate_path(["completed", "draft"])
    assert records and not records[0].valid
