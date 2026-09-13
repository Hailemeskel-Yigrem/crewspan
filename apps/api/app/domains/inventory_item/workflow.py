"""Workflow helpers for InventoryItem — side effects, guards, and audit notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class InventoryItemWorkflowResult:
    action: str
    entity_id: str
    previous_status: str
    next_status: str
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InventoryItemWorkflow:
    """Coordinates lifecycle events for inventory_item with validation and logging."""

    ALLOWED_STATUSES = ("draft", "pending", "active", "in_progress", "blocked", "completed", "cancelled")
    DOMAIN_ACTIONS = ("adjust_reorder_levels", "deactivate", "calculate_stock_value")

    def __init__(self, *, strict: bool = True) -> None:
        self._strict = strict

    def plan(self, entity: dict[str, Any], action: str, **context: Any) -> InventoryItemWorkflowResult:
        action = action.strip().lower()
        if action not in self.DOMAIN_ACTIONS and action not in {"activate", "block", "complete", "cancel"}:
            raise ValueError(f"Unknown workflow action: {action}")
        current = str(entity.get("status", "draft"))
        entity_id = str(entity.get("id", ""))
        notes: list[str] = []
        metadata: dict[str, Any] = dict(context)

        if action == "activate":
            if current not in {"draft", "blocked", "pending"}:
                self._reject(f"Cannot activate from {current}")
            nxt = "active"
            notes.append("Activated by operator")
        elif action == "block":
            if current in {"completed", "cancelled"}:
                self._reject(f"Cannot block terminal status {current}")
            nxt = "blocked"
            notes.append(context.get("reason") or "Awaiting dependency")
        elif action == "complete":
            if current not in {"active", "in_progress"}:
                self._reject("Only active/in_progress records can complete")
            nxt = "completed"
            notes.append(context.get("completion_notes") or "Marked complete")
        elif action == "cancel":
            if current == "completed":
                self._reject("Completed records cannot be cancelled")
            nxt = "cancelled"
            notes.append(context.get("reason") or "Cancelled by operator")
        elif action in self.DOMAIN_ACTIONS:
            nxt = self._domain_action_status(action, current, context)
            notes.append(f"Domain action {action} applied")
        else:
            raise ValueError(f"Unhandled action: {action}")

        logger.info(
            "inventory_item.workflow.plan",
            action=action,
            entity_id=entity_id,
            from_status=current,
            to_status=nxt,
        )
        return InventoryItemWorkflowResult(
            action=action,
            entity_id=entity_id,
            previous_status=current,
            next_status=nxt,
            notes=notes,
            metadata=metadata,
        )

    def apply(self, entity: dict[str, Any], action: str, **context: Any) -> InventoryItemWorkflowResult:
        result = self.plan(entity, action, **context)
        entity["status"] = result.next_status
        entity["updated_at"] = result.executed_at.isoformat()
        logger.info("inventory_item.workflow.apply", entity_id=result.entity_id, action=action)
        return result

    def _domain_action_status(self, action: str, current: str, context: dict[str, Any]) -> str:
        mapping = {
            "submit": "submitted",
            "start": "in_progress",
            "assign_technician": "assigned",
            "approve": "approved",
            "reject": "rejected",
            "fulfill": "fulfilled",
            "finalize": "finalized",
            "mark_sent": "sent",
            "retry": "pending",
        }
        return mapping.get(action, current)

    def _reject(self, message: str) -> None:
        if self._strict:
            raise ValueError(message)
        logger.warning("inventory_item.workflow.soft_fail", message=message)
