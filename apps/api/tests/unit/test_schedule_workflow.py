import pytest

from app.domains.schedule.workflow import ScheduleWorkflow


def test_schedule_activate_from_draft() -> None:
    result = ScheduleWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_schedule_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        ScheduleWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_schedule_cancel_from_active() -> None:
    result = ScheduleWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_schedule_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        ScheduleWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
