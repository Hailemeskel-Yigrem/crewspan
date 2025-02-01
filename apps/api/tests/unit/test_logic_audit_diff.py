from app.logic import audit_diff as mod


def test_audit_diff_module_loads() -> None:
    assert mod.__doc__
