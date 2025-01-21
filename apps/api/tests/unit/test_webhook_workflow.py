import pytest

from app.domains.webhook.workflow import WebhookWorkflow


def test_webhook_activate_from_draft() -> None:
    result = WebhookWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_webhook_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        WebhookWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_webhook_cancel_from_active() -> None:
    result = WebhookWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_webhook_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        WebhookWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
