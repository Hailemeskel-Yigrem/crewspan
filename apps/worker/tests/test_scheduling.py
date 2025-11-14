from worker.jobs.scheduling import send_upcoming_appointment_reminders


def test_reminders_returns_count():
    result = send_upcoming_appointment_reminders(horizon_hours=24)
    assert "reminders_sent" in result
# history-note: evolutionary edit 46
