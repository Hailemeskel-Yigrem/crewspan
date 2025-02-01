"""Rank technicians by skill coverage, certifications, and travel time."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class SkillMatchResult:
    technician_id: str
    coverage: float
    matched: frozenset[str]
    missing: frozenset[str]
    travel_minutes: int


def coverage_score(required: set[str], skills: set[str]) -> tuple[float, set[str], set[str]]:
    if not required:
        return 1.0, set(), set()
    matched = required & skills
    missing = required - skills
    return len(matched) / len(required), matched, missing


def rank_technicians(
    *,
    required: set[str],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> tuple[float, int, str]:
        skills = set(row.get("skills") or [])
        cov, _, _ = coverage_score(required, skills)
        travel = int(row.get("travel_minutes") or 0)
        return (-cov, travel, str(row.get("id", "")))

    return sorted(candidates, key=key)


def rank_with_details(
    *,
    required: set[str],
    candidates: Iterable[dict[str, Any]],
) -> list[SkillMatchResult]:
    results: list[SkillMatchResult] = []
    for row in candidates:
        skills = set(row.get("skills") or [])
        cov, matched, missing = coverage_score(required, skills)
        results.append(
            SkillMatchResult(
                technician_id=str(row.get("id", "")),
                coverage=cov,
                matched=frozenset(matched),
                missing=frozenset(missing),
                travel_minutes=int(row.get("travel_minutes") or 0),
            )
        )
    return sorted(results, key=lambda r: (-r.coverage, r.travel_minutes))


def meets_minimum(required: set[str], skills: set[str], *, threshold: float = 1.0) -> bool:
    score, _, _ = coverage_score(required, skills)
    return score >= threshold
