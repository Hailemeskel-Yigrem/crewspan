import pytest

from app.domains.inventory_item.workflow import InventoryItemWorkflow


def test_inventory_item_activate_from_draft() -> None:
    result = InventoryItemWorkflow().plan({"id": "1", "status": "draft"}, "activate")
    assert result.next_status == "active"
    assert result.previous_status == "draft"


def test_inventory_item_cannot_complete_from_draft() -> None:
    with pytest.raises(ValueError):
        InventoryItemWorkflow().plan({"id": "1", "status": "draft"}, "complete")


def test_inventory_item_cancel_from_active() -> None:
    result = InventoryItemWorkflow().apply({"id": "2", "status": "active"}, "cancel", reason="test")
    assert result.next_status == "cancelled"


def test_inventory_item_unknown_action_rejected() -> None:
    with pytest.raises(ValueError):
        InventoryItemWorkflow().plan({"id": "1", "status": "draft"}, "not-a-real-action")
