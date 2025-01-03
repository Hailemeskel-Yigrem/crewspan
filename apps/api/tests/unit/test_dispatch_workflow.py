import pytest

from app.domains.dispatch.workflow import DispatchWorkflow


def test_dispatch_activate_from_draft() -> None:
    result = DispatchWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_dispatch_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        DispatchWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_dispatch_cancel_from_active() -> None:
    result = DispatchWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_dispatch_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        DispatchWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
