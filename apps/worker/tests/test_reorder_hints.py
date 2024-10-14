from worker.jobs.reorder_hints import run


def test_reorder_hints_runs() -> None:
    assert run({"count": 2})["status"] == "ok"
