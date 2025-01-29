"""Geo helpers for field routing, bounding boxes, and travel estimates."""

from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True, slots=True)
class Coordinate:
    latitude: float
    longitude: float

    def validate(self) -> None:
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"latitude out of range: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"longitude out of range: {self.longitude}")


@dataclass(frozen=True, slots=True)
class BoundingBox:
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def contains(self, point: Coordinate) -> bool:
        return (
            self.min_lat <= point.latitude <= self.max_lat
            and self.min_lon <= point.longitude <= self.max_lon
        )

    @classmethod
    def around(cls, center: Coordinate, radius_km: float) -> "BoundingBox":
        center.validate()
        delta_lat = radius_km / EARTH_RADIUS_KM * (180.0 / math.pi)
        cos_lat = math.cos(math.radians(center.latitude))
        delta_lon = delta_lat / max(cos_lat, 1e-6)
        return cls(
            min_lat=center.latitude - delta_lat,
            max_lat=center.latitude + delta_lat,
            min_lon=center.longitude - delta_lon,
            max_lon=center.longitude + delta_lon,
        )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, a)))


def estimate_travel_minutes(distance_km: float, average_kmh: float = 35.0) -> int:
    if average_kmh <= 0:
        raise ValueError("average_kmh must be positive")
    return max(1, int(round((distance_km / average_kmh) * 60)))


def total_route_km(points: list[Coordinate]) -> float:
    if len(points) < 2:
        return 0.0
    total = 0.0
    for left, right in zip(points, points[1:]):
        total += haversine_km(left.latitude, left.longitude, right.latitude, right.longitude)
    return total
