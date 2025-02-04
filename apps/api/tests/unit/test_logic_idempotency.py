from app.logic import idempotency as mod


def test_idempotency_module_loads() -> None:
    assert mod.__doc__
