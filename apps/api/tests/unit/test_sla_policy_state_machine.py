import pytest

from app.domains.sla_policy.state_machine import assert_transition, can_transition, validate_path, is_terminal


def test_sla_policy_draft_to_active() -> None:
    assert can_transition("draft", "active")


def test_sla_policy_completed_is_terminal() -> None:
    assert is_terminal("completed")
    with pytest.raises(ValueError):
        assert_transition("completed", "active")


def test_sla_policy_validate_path_success() -> None:
    records = validate_path(["draft", "active", "completed"])
    assert all(r.valid for r in records)


def test_sla_policy_validate_path_detects_invalid() -> None:
    records = validate_path(["completed", "draft"])
    assert records and not records[0].valid
