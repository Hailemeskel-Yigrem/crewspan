from app.logic import inventory_reorder as mod


def test_inventory_reorder_module_loads() -> None:
    assert mod.__doc__
