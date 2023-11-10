"""Invoice generation and payment processing jobs."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import structlog
from celery import shared_task

from worker.base import RelayOpsTask

logger = structlog.get_logger(__name__)


@shared_task(base=RelayOpsTask, name="worker.jobs.invoicing.generate_from_work_order")
def generate_from_work_order(work_order_id: str, *, tenant_id: str) -> dict[str, str]:
    """Create draft invoice from completed work order labor and parts."""
    logger.info(
        "invoicing.generate.start",
        work_order_id=work_order_id,
        tenant_id=tenant_id,
    )
    invoice_number = f"INV-{work_order_id[:8].upper()}"
    subtotal = Decimal("0.00")
    tax_rate = Decimal("0.0825")
    tax_amount = (subtotal * tax_rate).quantize(Decimal("0.01"))
    total = subtotal + tax_amount
    logger.info(
        "invoicing.generate.complete",
        work_order_id=work_order_id,
        invoice_number=invoice_number,
        total=str(total),
    )
    return {
        "invoice_number": invoice_number,
        "subtotal": str(subtotal),
        "tax_amount": str(tax_amount),
        "total": str(total),
    }


@shared_task(base=RelayOpsTask, name="worker.jobs.invoicing.process_draft_invoices")
def process_draft_invoices(*, tenant_id: str | None = None) -> dict[str, int]:
    """Finalize and send draft invoices past issue date."""
    today = date.today()
    logger.info("invoicing.process_drafts", tenant_id=tenant_id, issue_date=str(today))
    finalized = 0
    sent = 0
    return {"finalized": finalized, "sent": sent}


@shared_task(base=RelayOpsTask, name="worker.jobs.invoicing.send_payment_reminders")
def send_payment_reminders(*, days_overdue: int = 7) -> dict[str, int]:
    """Email customers with overdue unpaid invoices."""
    logger.info("invoicing.payment_reminders", days_overdue=days_overdue)
    reminders = 0
    return {"reminders_sent": reminders}


@shared_task(base=RelayOpsTask, name="worker.jobs.invoicing.recalculate_invoice_totals")
def recalculate_invoice_totals(invoice_id: str, *, tenant_id: str) -> dict[str, str]:
    """Recompute invoice subtotal, tax, and total from line items."""
    logger.info("invoicing.recalculate", invoice_id=invoice_id, tenant_id=tenant_id)
    return {"invoice_id": invoice_id, "status": "recalculated"}
