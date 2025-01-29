"""Reorder point suggestions, safety stock, and batch replenishment planning."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReorderHint:
    sku: str
    on_hand: int
    reorder_point: int
    suggested_qty: int
    urgency: str = "normal"


@dataclass
class InventorySnapshot:
    sku: str
    on_hand: int
    reorder_point: int
    reorder_qty: int
    open_demand: int = 0
    lead_time_days: int = 7


def suggest_reorder(
    *,
    sku: str,
    on_hand: int,
    reorder_point: int,
    reorder_qty: int,
    open_demand: int = 0,
) -> ReorderHint | None:
    effective = on_hand - open_demand
    if effective > reorder_point:
        return None
    deficit = reorder_point - effective
    suggested = max(reorder_qty, deficit)
    urgency = "critical" if effective <= 0 else "high" if effective < reorder_point // 2 else "normal"
    return ReorderHint(
        sku=sku,
        on_hand=on_hand,
        reorder_point=reorder_point,
        suggested_qty=suggested,
        urgency=urgency,
    )


def batch_reorder_hints(items: list[InventorySnapshot]) -> list[ReorderHint]:
    hints: list[ReorderHint] = []
    for item in items:
        hint = suggest_reorder(
            sku=item.sku,
            on_hand=item.on_hand,
            reorder_point=item.reorder_point,
            reorder_qty=item.reorder_qty,
            open_demand=item.open_demand,
        )
        if hint:
            hints.append(hint)
    return sorted(hints, key=lambda h: (h.urgency != "critical", h.urgency != "high", h.sku))


def days_until_stockout(on_hand: int, avg_daily_usage: float) -> float | None:
    if avg_daily_usage <= 0:
        return None
    return on_hand / avg_daily_usage
