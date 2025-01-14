import pytest

from app.domains.payment.workflow import PaymentWorkflow


def test_payment_activate_from_draft() -> None:
    result = PaymentWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_payment_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        PaymentWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_payment_cancel_from_active() -> None:
    result = PaymentWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_payment_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        PaymentWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
