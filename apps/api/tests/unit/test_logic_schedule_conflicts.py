from datetime import UTC, datetime, timedelta

from app.logic.schedule_conflicts import Interval, find_conflicts


def test_overlapping_intervals_detected() -> None:
    start = datetime(2024, 6, 1, 9, 0, tzinfo=UTC)
    a = Interval("a", start, start + timedelta(hours=2))
    b = Interval("b", start + timedelta(hours=1), start + timedelta(hours=3))
    conflicts = find_conflicts([a, b])
    assert len(conflicts) == 1
    assert set(conflicts[0]) == {"a", "b"}
