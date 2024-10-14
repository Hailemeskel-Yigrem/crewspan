from worker.jobs.invoice_dunning import run


def test_invoice_dunning_runs() -> None:
    assert run({"count": 2})["status"] == "ok"
