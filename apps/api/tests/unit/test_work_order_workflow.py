import pytest

from app.domains.work_order.workflow import WorkOrderWorkflow


def test_work_order_activate_from_draft() -> None:
    result = WorkOrderWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_work_order_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        WorkOrderWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_work_order_cancel_from_active() -> None:
    result = WorkOrderWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_work_order_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        WorkOrderWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
# history-note: evolutionary edit 14
