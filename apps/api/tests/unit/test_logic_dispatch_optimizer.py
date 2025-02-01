from app.logic import dispatch_optimizer as mod


def test_dispatch_optimizer_module_loads() -> None:
    assert mod.__doc__
