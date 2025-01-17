import pytest

from app.domains.technician.workflow import TechnicianWorkflow


def test_technician_activate_from_draft() -> None:
    result = TechnicianWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_technician_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        TechnicianWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_technician_cancel_from_active() -> None:
    result = TechnicianWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_technician_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        TechnicianWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
