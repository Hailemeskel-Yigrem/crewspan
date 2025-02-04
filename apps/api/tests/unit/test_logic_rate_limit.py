from app.logic import rate_limit as mod


def test_rate_limit_module_loads() -> None:
    assert mod.__doc__
