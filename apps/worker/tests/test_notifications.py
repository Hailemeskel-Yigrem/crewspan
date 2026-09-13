"""Worker notification job tests."""

from worker.jobs.notifications import process_pending_batch, send_email


def test_send_email_returns_status():
    result = send_email("notif-id", tenant_id="tenant-1")
    assert result["status"] == "sent"


def test_process_pending_batch():
    result = process_pending_batch(limit=10)
    assert "processed" in result
