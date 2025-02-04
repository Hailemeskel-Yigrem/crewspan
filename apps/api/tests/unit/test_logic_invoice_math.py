from decimal import Decimal

from app.logic.invoice_math import InvoiceLine, compute_invoice_totals


def test_invoice_totals_with_tax_and_discount() -> None:
    totals = compute_invoice_totals(
        [
            InvoiceLine(quantity=2, unit_price=Decimal("50.00")),
            InvoiceLine(quantity=1, unit_price=Decimal("25.00")),
        ],
        tax_rate=Decimal("0.15"),
        discount=Decimal("10.00"),
    )
    assert totals.subtotal == Decimal("125.00")
    assert totals.tax == Decimal("17.25")
    assert totals.total == Decimal("132.25")
