"""Notification template registry with safe rendering and fallbacks."""

from __future__ import annotations

from string import Formatter
from typing import Any


TEMPLATES: dict[str, str] = {
    "work_order.assigned": "Work order {number} assigned to {technician}.",
    "work_order.completed": "Work order {number} completed by {technician}.",
    "work_order.cancelled": "Work order {number} was cancelled: {reason}.",
    "sla.warning": "SLA for {number} breaches in {minutes} minutes.",
    "sla.breached": "SLA breached for {number}. Escalation level {level}.",
    "invoice.ready": "Invoice {number} is ready for customer {customer}.",
    "invoice.overdue": "Invoice {number} is {days} days overdue.",
    "dispatch.offer": "New job available: {title} at {site}. Respond within {minutes} minutes.",
    "parts.low_stock": "SKU {sku} is below reorder point ({on_hand} on hand).",
    "schedule.reminder": "Upcoming appointment: {title} at {starts_at}.",
}


class SafeFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            return kwargs.get(key, f"{{{key}}}")
        return super().get_value(key, args, kwargs)


def render(template_key: str, **context: Any) -> str:
    try:
        template = TEMPLATES[template_key]
    except KeyError as exc:
        raise KeyError(f"Unknown template: {template_key}") from exc
    return SafeFormatter().format(template, **context)


def available_templates(prefix: str | None = None) -> list[str]:
    if prefix is None:
        return sorted(TEMPLATES)
    return sorted(k for k in TEMPLATES if k.startswith(prefix))


def preview(template_key: str, sample: dict[str, Any] | None = None) -> str:
    sample = sample or {}
    defaults = {field: f"[{field}]" for _, field, _, _ in SafeFormatter().parse(TEMPLATES[template_key]) if field}
    defaults.update(sample)
    return render(template_key, **defaults)
