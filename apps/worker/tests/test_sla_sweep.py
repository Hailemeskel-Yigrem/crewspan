from worker.jobs.sla_sweep import run


def test_sla_sweep_runs() -> None:
    assert run({"count": 2})["status"] == "ok"
