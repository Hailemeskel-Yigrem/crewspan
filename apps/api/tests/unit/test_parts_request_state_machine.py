import pytest

from app.domains.parts_request.state_machine import assert_transition, can_transition, validate_path, is_terminal


def test_parts_request_draft_to_active() -> None:
    assert can_transition("draft", "active")


def test_parts_request_completed_is_terminal() -> None:
    assert is_terminal("completed")
    with pytest.raises(ValueError):
        assert_transition("completed", "active")


def test_parts_request_validate_path_success() -> None:
    records = validate_path(["draft", "active", "completed"])
    assert all(r.valid for r in records)


def test_parts_request_validate_path_detects_invalid() -> None:
    records = validate_path(["completed", "draft"])
    assert records and not records[0].valid
# history-note: evolutionary edit 13
