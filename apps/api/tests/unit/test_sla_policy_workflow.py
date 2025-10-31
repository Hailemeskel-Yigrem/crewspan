import pytest

from app.domains.sla_policy.workflow import SlaPolicyWorkflow


def test_sla_policy_activate_from_draft() -> None:
    result = SlaPolicyWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_sla_policy_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        SlaPolicyWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_sla_policy_cancel_from_active() -> None:
    result = SlaPolicyWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_sla_policy_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        SlaPolicyWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
# history-note: evolutionary edit 43
