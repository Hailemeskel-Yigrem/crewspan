"""Heuristic dispatch scoring and assignment optimization for field technicians."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DispatchRequest:
    work_order_id: str
    required_skills: frozenset[str]
    priority: str = "normal"
    estimated_minutes: int = 60


@dataclass(frozen=True, slots=True)
class TechnicianCandidate:
    technician_id: str
    skills: frozenset[str]
    travel_minutes: int
    open_jobs: int
    max_daily_hours: int = 8
    status: str = "available"


@dataclass(frozen=True, slots=True)
class CandidateScore:
    technician_id: str
    score: float
    skill_coverage: float
    travel_minutes: int
    open_jobs: int
    reasons: tuple[str, ...] = ()


PRIORITY_WEIGHT = {"critical": 1.4, "high": 1.2, "normal": 1.0, "low": 0.85}


def score_candidate(
    *,
    technician_id: str,
    required_skills: set[str],
    technician_skills: set[str],
    travel_minutes: int,
    open_jobs: int,
    priority: str = "normal",
    max_daily_hours: int = 8,
) -> CandidateScore:
    if not required_skills:
        coverage = 1.0
    else:
        coverage = len(required_skills & technician_skills) / len(required_skills)
    load_penalty = (open_jobs / max(1, max_daily_hours)) * 25.0
    travel_penalty = travel_minutes * 0.35
    priority_boost = PRIORITY_WEIGHT.get(priority, 1.0)
    score = (coverage * 100.0 * priority_boost) - travel_penalty - load_penalty
    reasons = (
        f"skill_coverage={coverage:.0%}",
        f"travel={travel_minutes}m",
        f"open_jobs={open_jobs}",
    )
    return CandidateScore(
        technician_id=technician_id,
        score=score,
        skill_coverage=coverage,
        travel_minutes=travel_minutes,
        open_jobs=open_jobs,
        reasons=reasons,
    )


def rank_candidates(candidates: list[CandidateScore]) -> list[CandidateScore]:
    return sorted(candidates, key=lambda c: (-c.score, c.travel_minutes, c.open_jobs))


def select_best(
    request: DispatchRequest,
    technicians: Iterable[TechnicianCandidate],
    *,
    min_coverage: float = 0.5,
) -> CandidateScore | None:
    scored: list[CandidateScore] = []
    for tech in technicians:
        if tech.status not in ("available", "busy"):
            continue
        result = score_candidate(
            technician_id=tech.technician_id,
            required_skills=set(request.required_skills),
            technician_skills=set(tech.skills),
            travel_minutes=tech.travel_minutes,
            open_jobs=tech.open_jobs,
            priority=request.priority,
            max_daily_hours=tech.max_daily_hours,
        )
        if result.skill_coverage >= min_coverage:
            scored.append(result)
    ranked = rank_candidates(scored)
    return ranked[0] if ranked else None


def batch_assign(
    requests: list[DispatchRequest],
    technicians: list[TechnicianCandidate],
) -> dict[str, str | None]:
    """Greedy assignment: highest priority request first, best technician per request."""
    ordered = sorted(requests, key=lambda r: -PRIORITY_WEIGHT.get(r.priority, 1.0))
    load: dict[str, int] = {t.technician_id: t.open_jobs for t in technicians}
    assignments: dict[str, str | None] = {}
    for req in ordered:
        adjusted = [
            TechnicianCandidate(
                technician_id=t.technician_id,
                skills=t.skills,
                travel_minutes=t.travel_minutes,
                open_jobs=load.get(t.technician_id, t.open_jobs),
                max_daily_hours=t.max_daily_hours,
                status=t.status,
            )
            for t in technicians
        ]
        best = select_best(req, adjusted)
        assignments[req.work_order_id] = best.technician_id if best else None
        if best:
            load[best.technician_id] = load.get(best.technician_id, 0) + 1
    return assignments
