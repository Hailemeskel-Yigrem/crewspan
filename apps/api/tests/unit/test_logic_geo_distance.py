from app.logic.geo import haversine_km


def test_haversine_same_point() -> None:
    assert haversine_km(9.03, 38.74, 9.03, 38.74) == 0.0


def test_haversine_known_distance() -> None:
    distance = haversine_km(9.03, 38.74, 9.6, 41.85)
    assert 300 < distance < 450
