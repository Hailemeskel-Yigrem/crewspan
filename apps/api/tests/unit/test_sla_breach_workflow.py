import pytest

from app.domains.sla_breach.workflow import SlaBreachWorkflow


def test_sla_breach_activate_from_draft() -> None:
    result = SlaBreachWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_sla_breach_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        SlaBreachWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_sla_breach_cancel_from_active() -> None:
    result = SlaBreachWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_sla_breach_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        SlaBreachWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
