"""Daily technician capacity planning, overbooking detection, and shift rollups."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable


@dataclass(frozen=True, slots=True)
class CapacityDay:
    technician_id: str
    work_date: date
    available_minutes: int
    booked_minutes: int

    @property
    def remaining_minutes(self) -> int:
        return max(0, self.available_minutes - self.booked_minutes)

    @property
    def utilization(self) -> float:
        if self.available_minutes <= 0:
            return 1.0
        return min(1.0, self.booked_minutes / self.available_minutes)

    @property
    def is_overbooked(self) -> bool:
        return self.booked_minutes > self.available_minutes


@dataclass
class CapacityPlan:
    days: list[CapacityDay] = field(default_factory=list)

    def add(self, day: CapacityDay) -> None:
        self.days.append(day)

    def overbooked(self, threshold: float = 0.9) -> list[CapacityDay]:
        return [day for day in self.days if day.utilization >= threshold or day.is_overbooked]

    def total_booked_minutes(self) -> int:
        return sum(day.booked_minutes for day in self.days)

    def average_utilization(self) -> float:
        if not self.days:
            return 0.0
        return sum(day.utilization for day in self.days) / len(self.days)


def overbooked(days: list[CapacityDay], threshold: float = 0.9) -> list[CapacityDay]:
    return [day for day in days if day.utilization >= threshold]


def plan_from_shifts(shifts: Iterable[dict[str, object]]) -> CapacityPlan:
    plan = CapacityPlan()
    for row in shifts:
        plan.add(
            CapacityDay(
                technician_id=str(row.get("technician_id", "")),
                work_date=row.get("work_date") or date.today(),
                available_minutes=int(row.get("available_minutes") or 480),
                booked_minutes=int(row.get("booked_minutes") or 0),
            )
        )
    return plan
