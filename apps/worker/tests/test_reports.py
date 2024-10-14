from worker.jobs.reports import export_work_orders_csv


def test_export_creates_file(tmp_path, monkeypatch):
    monkeypatch.setattr("worker.config.settings.report_export_dir", str(tmp_path))
    result = export_work_orders_csv(
        tenant_id="t-1", start_date="2024-01-01", end_date="2024-01-31", requested_by_id="u-1"
    )
    assert result["format"] == "csv"
