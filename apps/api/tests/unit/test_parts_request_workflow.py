import pytest

from app.domains.parts_request.workflow import PartsRequestWorkflow


def test_parts_request_activate_from_draft() -> None:
    result = PartsRequestWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_parts_request_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        PartsRequestWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_parts_request_cancel_from_active() -> None:
    result = PartsRequestWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_parts_request_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        PartsRequestWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
