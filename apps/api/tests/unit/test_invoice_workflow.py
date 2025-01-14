import pytest

from app.domains.invoice.workflow import InvoiceWorkflow


def test_invoice_activate_from_draft() -> None:
    result = InvoiceWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_invoice_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        InvoiceWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_invoice_cancel_from_active() -> None:
    result = InvoiceWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_invoice_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        InvoiceWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
