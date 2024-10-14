from worker.jobs.schedule_digest import run


def test_schedule_digest_runs() -> None:
    assert run({"count": 2})["status"] == "ok"
