"""Invoice arithmetic, tax jurisdictions, and line-item rollups."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    quantity: int
    unit_price: Decimal
    description: str = ""
    taxable: bool = True

    def line_total(self) -> Decimal:
        return _money(Decimal(self.quantity) * self.unit_price)


@dataclass(frozen=True, slots=True)
class InvoiceTotals:
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    line_count: int = 0


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_subtotal(lines: Iterable[InvoiceLine]) -> Decimal:
    return _money(sum((line.line_total() for line in lines), Decimal("0")))


def compute_invoice_totals(
    lines: list[InvoiceLine],
    *,
    tax_rate: Decimal = Decimal("0"),
    discount: Decimal = Decimal("0"),
    tax_exempt: bool = False,
) -> InvoiceTotals:
    subtotal = compute_subtotal(lines)
    discount = _money(max(Decimal("0"), discount))
    taxable_base = Decimal("0") if tax_exempt else sum(
        (line.line_total() for line in lines if line.taxable),
        Decimal("0"),
    )
    taxable = max(Decimal("0"), taxable_base - discount)
    tax = _money(taxable * tax_rate)
    total = _money(max(Decimal("0"), subtotal - discount) + tax)
    return InvoiceTotals(
        subtotal=subtotal,
        tax=tax,
        discount=discount,
        total=total,
        line_count=len(lines),
    )


def split_tax_by_rate(lines: list[InvoiceLine], rates: dict[str, Decimal]) -> dict[str, Decimal]:
    """Apply labeled tax rates to taxable lines sharing a category key in description prefix."""
    buckets: dict[str, Decimal] = {key: Decimal("0") for key in rates}
    for line in lines:
        if not line.taxable:
            continue
        for label, rate in rates.items():
            if line.description.startswith(label):
                buckets[label] += _money(line.line_total() * rate)
    return buckets
