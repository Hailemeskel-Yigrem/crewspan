import pytest

from app.domains.notification.workflow import NotificationWorkflow


def test_notification_activate_from_draft() -> None:
    result = NotificationWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_notification_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        NotificationWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_notification_cancel_from_active() -> None:
    result = NotificationWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_notification_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        NotificationWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
