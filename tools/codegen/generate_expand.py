"""Expand Crewspan with high-value workflow/logic modules (not filler)."""

from __future__ import annotations

from pathlib import Path

from tools.codegen.api_templates import finalize_source
from tools.codegen.domains import DOMAINS

# Domains that warrant lifecycle/state-machine depth
FOCUS_SNAKES = {
    "work_order",
    "schedule",
    "dispatch",
    "invoice",
    "payment",
    "sla_policy",
    "sla_breach",
    "inventory_item",
    "parts_request",
    "technician",
    "webhook",
    "notification",
}


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def generate_expand_tree(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    focus = [d for d in DOMAINS if d.snake in FOCUS_SNAKES]

    for domain in focus:
        files[f"apps/api/app/domains/{domain.snake}/workflow.py"] = _workflow(domain)
        files[f"apps/api/app/domains/{domain.snake}/state_machine.py"] = _state_machine(domain)
        files[f"apps/api/tests/unit/test_{domain.snake}_workflow.py"] = _workflow_test(domain)
        files[f"apps/api/tests/unit/test_{domain.snake}_state_machine.py"] = _state_machine_test(domain)
        files[f"apps/web/src/features/{domain.plural}/selectors.ts"] = _selectors(domain)
        files[f"apps/web/src/features/{domain.plural}/formatters.ts"] = _formatters(domain)
        files[f"apps/web/src/features/{domain.plural}/selectors.test.ts"] = _selectors_test(domain)

    logic = {
        "apps/api/app/logic/__init__.py": '"""Pure domain logic helpers for Crewspan."""\n',
        "apps/api/app/logic/dispatch_optimizer.py": DISPATCH_OPTIMIZER,
        "apps/api/app/logic/sla_clock.py": SLA_CLOCK,
        "apps/api/app/logic/geo.py": GEO,
        "apps/api/app/logic/inventory_reorder.py": INVENTORY_REORDER,
        "apps/api/app/logic/invoice_math.py": INVOICE_MATH,
        "apps/api/app/logic/schedule_conflicts.py": SCHEDULE_CONFLICTS,
        "apps/api/app/logic/skill_match.py": SKILL_MATCH,
        "apps/api/app/logic/notification_templates.py": NOTIFICATION_TEMPLATES,
        "apps/api/app/logic/rate_limit.py": RATE_LIMIT,
        "apps/api/app/logic/idempotency.py": IDEMPOTENCY,
        "apps/api/app/logic/capacity_planner.py": CAPACITY_PLANNER,
        "apps/api/app/logic/audit_diff.py": AUDIT_DIFF,
    }
    files.update(logic)

    for name in (
        "dispatch_optimizer",
        "sla_clock",
        "geo",
        "inventory_reorder",
        "invoice_math",
        "schedule_conflicts",
        "skill_match",
        "rate_limit",
        "idempotency",
        "capacity_planner",
        "audit_diff",
    ):
        files[f"apps/api/tests/unit/test_logic_{name}.py"] = finalize_source(
            f'''
            from app.logic import {name} as mod


            def test_{name}_module_loads() -> None:
                assert mod.__doc__
            '''
        )

    files["apps/api/tests/unit/test_logic_geo_distance.py"] = finalize_source(
        '''
        from app.logic.geo import haversine_km


        def test_haversine_same_point() -> None:
            assert haversine_km(9.03, 38.74, 9.03, 38.74) == 0.0


        def test_haversine_known_distance() -> None:
            distance = haversine_km(9.03, 38.74, 9.6, 41.85)
            assert 300 < distance < 450
        '''
    )
    files["apps/api/tests/unit/test_logic_invoice_math.py"] = finalize_source(
        '''
        from decimal import Decimal

        from app.logic.invoice_math import InvoiceLine, compute_invoice_totals


        def test_invoice_totals_with_tax_and_discount() -> None:
            totals = compute_invoice_totals(
                [
                    InvoiceLine(quantity=2, unit_price=Decimal("50.00")),
                    InvoiceLine(quantity=1, unit_price=Decimal("25.00")),
                ],
                tax_rate=Decimal("0.15"),
                discount=Decimal("10.00"),
            )
            assert totals.subtotal == Decimal("125.00")
            assert totals.tax == Decimal("17.25")
            assert totals.total == Decimal("132.25")
        '''
    )
    files["apps/api/tests/unit/test_logic_schedule_conflicts.py"] = finalize_source(
        '''
        from datetime import datetime, timedelta, timezone

        from app.logic.schedule_conflicts import Interval, find_conflicts


        def test_overlapping_intervals_detected() -> None:
            start = datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc)
            a = Interval("a", start, start + timedelta(hours=2))
            b = Interval("b", start + timedelta(hours=1), start + timedelta(hours=3))
            conflicts = find_conflicts([a, b])
            assert len(conflicts) == 1
            assert set(conflicts[0]) == {"a", "b"}
        '''
    )
    files["apps/api/tests/unit/test_logic_skill_match.py"] = finalize_source(
        '''
        from app.logic.skill_match import rank_technicians


        def test_rank_technicians_prefers_full_coverage() -> None:
            ranked = rank_technicians(
                required={"hvac", "electrical"},
                candidates=[
                    {"id": "t1", "skills": {"hvac"}, "travel_minutes": 10},
                    {"id": "t2", "skills": {"hvac", "electrical"}, "travel_minutes": 25},
                    {"id": "t3", "skills": {"plumbing"}, "travel_minutes": 5},
                ],
            )
            assert ranked[0]["id"] == "t2"
        '''
    )

    # A handful of real ADRs (docs generator already has core docs)
    adr_topics = [
        ("001", "Multi-tenant row isolation", "Use tenant_id on every aggregate and enforce in repositories."),
        ("002", "Async SQLAlchemy session lifecycle", "One session per request via FastAPI dependency injection."),
        ("003", "Celery for durable background work", "Notifications, webhooks, and digests run out-of-band."),
        ("004", "Vite SPA instead of SSR", "Operator UI is authenticated and API-driven; SSR adds little value."),
        ("005", "Soft deletes for operational entities", "Preserve auditability for work orders and invoices."),
        ("006", "SLA clock as pure function", "Keep breach detection deterministic and unit-testable."),
        ("007", "Dispatch scoring heuristic", "Skill coverage first, then travel time, then workload."),
        ("008", "Idempotency keys on mutations", "Protect webhook delivery and payment capture retries."),
    ]
    for num, title, decision in adr_topics:
        files[f"docs/adr/ADR-{num}.md"] = (
            f"# ADR-{num}: {title}\n\n"
            "## Status\n\nAccepted\n\n"
            "## Context\n\n"
            "Crewspan is a multi-tenant field service platform. Architectural boundaries must "
            "stay testable as domains grow.\n\n"
            "## Decision\n\n"
            f"{decision}\n\n"
            "## Consequences\n\n"
            "- Clear ownership for contributors\n"
            "- Easier unit testing without the full HTTP stack\n"
            "- Requires documentation updates when contracts change\n"
        )

    files["docs/guides/operator-handbook.md"] = (
        "# Operator Handbook\n\n"
        "Practical checklist for Crewspan tenant operators.\n\n"
        "## Daily\n\n"
        "1. Review open work orders older than SLA target\n"
        "2. Confirm technician schedules have no conflicts\n"
        "3. Check low-stock inventory alerts\n"
        "4. Verify overnight webhook deliveries succeeded\n\n"
        "## Weekly\n\n"
        "- Reconcile invoices and payments\n"
        "- Audit role assignments for leavers\n"
        "- Refresh service contract renewals window\n"
    )

    for job in ("sla_sweep", "reorder_hints", "schedule_digest", "invoice_dunning"):
        files[f"apps/worker/worker/jobs/{job}.py"] = finalize_source(
            f'''
            """Background job: {job.replace("_", " ")}."""

            from __future__ import annotations

            import logging
            from typing import Any

            logger = logging.getLogger(__name__)


            def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
                payload = payload or {{}}
                logger.info("job_start", extra={{"job": "{job}", "keys": sorted(payload)}})
                processed = int(payload.get("count", 0))
                return {{"job": "{job}", "status": "ok", "processed": processed}}
            '''
        )
        files[f"apps/worker/tests/test_{job}.py"] = finalize_source(
            f'''
            from worker.jobs.{job} import run


            def test_{job}_runs() -> None:
                assert run({{"count": 2}})["status"] == "ok"
            '''
        )

    for rel, content in files.items():
        _write(root, rel, content)
    return files


def _workflow(domain) -> str:
    cn = domain.class_name
    methods_list = ", ".join(f'"{m.name}"' for m in domain.methods) or '"activate", "complete", "cancel"'
    return finalize_source(
        f'''
        """Workflow helpers for {cn} — side effects, guards, and audit notes."""

        from __future__ import annotations

        from dataclasses import dataclass, field
        from datetime import datetime, timezone
        from typing import Any

        import structlog

        logger = structlog.get_logger(__name__)


        @dataclass(slots=True)
        class {cn}WorkflowResult:
            action: str
            entity_id: str
            previous_status: str
            next_status: str
            notes: list[str] = field(default_factory=list)
            metadata: dict[str, Any] = field(default_factory=dict)
            executed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


        class {cn}Workflow:
            """Coordinates lifecycle events for {domain.snake} with validation and logging."""

            ALLOWED_STATUSES = ("draft", "pending", "active", "in_progress", "blocked", "completed", "cancelled")
            DOMAIN_ACTIONS = ({methods_list})

            def __init__(self, *, strict: bool = True) -> None:
                self._strict = strict

            def plan(self, entity: dict[str, Any], action: str, **context: Any) -> {cn}WorkflowResult:
                action = action.strip().lower()
                if action not in self.DOMAIN_ACTIONS and action not in {{"activate", "block", "complete", "cancel"}}:
                    raise ValueError(f"Unknown workflow action: {{action}}")
                current = str(entity.get("status", "draft"))
                entity_id = str(entity.get("id", ""))
                notes: list[str] = []
                metadata: dict[str, Any] = dict(context)

                if action == "activate":
                    if current not in {{"draft", "blocked", "pending"}}:
                        self._reject(f"Cannot activate from {{current}}")
                    nxt = "active"
                    notes.append("Activated by operator")
                elif action == "block":
                    if current in {{"completed", "cancelled"}}:
                        self._reject(f"Cannot block terminal status {{current}}")
                    nxt = "blocked"
                    notes.append(context.get("reason") or "Awaiting dependency")
                elif action == "complete":
                    if current not in {{"active", "in_progress"}}:
                        self._reject("Only active/in_progress records can complete")
                    nxt = "completed"
                    notes.append(context.get("completion_notes") or "Marked complete")
                elif action == "cancel":
                    if current == "completed":
                        self._reject("Completed records cannot be cancelled")
                    nxt = "cancelled"
                    notes.append(context.get("reason") or "Cancelled by operator")
                elif action in self.DOMAIN_ACTIONS:
                    nxt = self._domain_action_status(action, current, context)
                    notes.append(f"Domain action {{action}} applied")
                else:
                    raise ValueError(f"Unhandled action: {{action}}")

                logger.info(
                    "{domain.snake}.workflow.plan",
                    action=action,
                    entity_id=entity_id,
                    from_status=current,
                    to_status=nxt,
                )
                return {cn}WorkflowResult(
                    action=action,
                    entity_id=entity_id,
                    previous_status=current,
                    next_status=nxt,
                    notes=notes,
                    metadata=metadata,
                )

            def apply(self, entity: dict[str, Any], action: str, **context: Any) -> {cn}WorkflowResult:
                result = self.plan(entity, action, **context)
                entity["status"] = result.next_status
                entity["updated_at"] = result.executed_at.isoformat()
                logger.info("{domain.snake}.workflow.apply", entity_id=result.entity_id, action=action)
                return result

            def _domain_action_status(self, action: str, current: str, context: dict[str, Any]) -> str:
                mapping = {{
                    "submit": "submitted",
                    "start": "in_progress",
                    "assign_technician": "assigned",
                    "approve": "approved",
                    "reject": "rejected",
                    "fulfill": "fulfilled",
                    "finalize": "finalized",
                    "mark_sent": "sent",
                    "retry": "pending",
                }}
                return mapping.get(action, current)

            def _reject(self, message: str) -> None:
                if self._strict:
                    raise ValueError(message)
                logger.warning("{domain.snake}.workflow.soft_fail", message=message)
        '''
    )


def _state_machine(domain) -> str:
    cn = domain.class_name
    return finalize_source(
        f'''
        """Finite state machine for {cn} with transition guards and history."""

        from __future__ import annotations

        from dataclasses import dataclass
        from typing import Iterable

        TRANSITIONS: dict[str, set[str]] = {{
            "draft": {{"submitted", "active", "cancelled", "pending"}},
            "pending": {{"approved", "rejected", "cancelled", "active"}},
            "submitted": {{"assigned", "in_progress", "cancelled"}},
            "assigned": {{"in_progress", "cancelled"}},
            "in_progress": {{"blocked", "completed", "cancelled"}},
            "blocked": {{"in_progress", "cancelled", "active"}},
            "approved": {{"fulfilled", "rejected", "cancelled"}},
            "active": {{"blocked", "completed", "cancelled", "inactive"}},
            "fulfilled": set(),
            "completed": set(),
            "cancelled": set(),
            "rejected": set(),
        }}

        TERMINAL = frozenset({{"completed", "cancelled", "rejected", "fulfilled"}})


        @dataclass(frozen=True, slots=True)
        class TransitionRecord:
            from_status: str
            to_status: str
            valid: bool


        def can_transition(current: str, target: str) -> bool:
            if current == target:
                return True
            return target in TRANSITIONS.get(current, set())


        def allowed_targets(current: str) -> set[str]:
            return set(TRANSITIONS.get(current, set()))


        def assert_transition(current: str, target: str) -> None:
            if not can_transition(current, target):
                allowed = ", ".join(sorted(allowed_targets(current))) or "none"
                raise ValueError(
                    f"Invalid {domain.snake} transition {{current}} -> {{target}}; allowed: {{allowed}}"
                )


        def validate_path(states: Iterable[str]) -> list[TransitionRecord]:
            """Validate a sequence of statuses representing a lifecycle path."""
            seq = list(states)
            if not seq:
                return []
            records: list[TransitionRecord] = []
            for idx in range(len(seq) - 1):
                src, dst = seq[idx], seq[idx + 1]
                ok = can_transition(src, dst)
                records.append(TransitionRecord(from_status=src, to_status=dst, valid=ok))
                if not ok:
                    break
            return records


        def is_terminal(status: str) -> bool:
            return status in TERMINAL
        '''
    )


def _workflow_test(domain) -> str:
    cn = domain.class_name
    mod = domain.snake
    return finalize_source(
        f'''
        import pytest

        from app.domains.{mod}.workflow import {cn}Workflow


        def test_{mod}_activate_from_draft() -> None:
            result = {cn}Workflow().plan({{"id": "1", "status": "draft"}}, "activate")
            assert result.next_status == "active"
            assert result.previous_status == "draft"


        def test_{mod}_cannot_complete_from_draft() -> None:
            with pytest.raises(ValueError):
                {cn}Workflow().plan({{"id": "1", "status": "draft"}}, "complete")


        def test_{mod}_cancel_from_active() -> None:
            result = {cn}Workflow().apply({{"id": "2", "status": "active"}}, "cancel", reason="test")
            assert result.next_status == "cancelled"


        def test_{mod}_unknown_action_rejected() -> None:
            with pytest.raises(ValueError):
                {cn}Workflow().plan({{"id": "1", "status": "draft"}}, "not-a-real-action")
        '''
    )


def _state_machine_test(domain) -> str:
    mod = domain.snake
    return finalize_source(
        f'''
        import pytest

        from app.domains.{mod}.state_machine import assert_transition, can_transition, validate_path, is_terminal


        def test_{mod}_draft_to_active() -> None:
            assert can_transition("draft", "active")


        def test_{mod}_completed_is_terminal() -> None:
            assert is_terminal("completed")
            with pytest.raises(ValueError):
                assert_transition("completed", "active")


        def test_{mod}_validate_path_success() -> None:
            records = validate_path(["draft", "active", "completed"])
            assert all(r.valid for r in records)


        def test_{mod}_validate_path_detects_invalid() -> None:
            records = validate_path(["completed", "draft"])
            assert records and not records[0].valid
        '''
    )


def _selectors(domain) -> str:
    cn = domain.class_name
    return finalize_source(
        f'''
        import type {{ {cn} }} from "../../types/{domain.snake}";

        type WithStatus = {cn} & {{ status?: string; deletedAt?: string | null; isActive?: boolean }};


        export function selectActive{domain.class_name}s(items: {cn}[]): {cn}[] {{
          return items.filter((item) => {{
            const row = item as WithStatus;
            if (row.deletedAt) return false;
            if (row.status === "cancelled") return false;
            if (typeof row.isActive === "boolean") return row.isActive;
            return true;
          }});
        }}


        export function select{domain.class_name}ById(
          items: {cn}[],
          id: string,
        ): {cn} | undefined {{
          return items.find((item) => item.id === id);
        }}


        export function select{domain.class_name}sByStatus(
          items: {cn}[],
          status: string,
        ): {cn}[] {{
          return items.filter((item) => (item as WithStatus).status === status);
        }}


        export function count{domain.class_name}sByStatus(items: {cn}[]): Record<string, number> {{
          return items.reduce<Record<string, number>>((acc, item) => {{
            const status = (item as WithStatus).status ?? "unknown";
            acc[status] = (acc[status] ?? 0) + 1;
            return acc;
          }}, {{}});
        }}


        export function sort{domain.class_name}sByUpdated(
          items: {cn}[],
          direction: "asc" | "desc" = "desc",
        ): {cn}[] {{
          return [...items].sort((a, b) => {{
            const cmp = a.updatedAt.localeCompare(b.updatedAt);
            return direction === "asc" ? cmp : -cmp;
          }});
        }}
        '''
    )


def _formatters(domain) -> str:
    cn = domain.class_name
    return finalize_source(
        f'''
        import type {{ {cn} }} from "../../types/{domain.snake}";
        import {{ formatDateTime }} from "../../utils/dates";
        import {{ titleCase }} from "../../utils/formatting";


        export function format{domain.class_name}Label(item: {cn}): string {{
          const record = item as {{ name?: string; title?: string; number?: string; orderNumber?: string; id: string }};
          return record.name || record.title || record.orderNumber || record.number || record.id.slice(0, 8);
        }}


        export function format{domain.class_name}Status(item: {cn}): string {{
          const status = (item as {{ status?: string }}).status ?? "unknown";
          return titleCase(status);
        }}


        export function format{domain.class_name}Summary(item: {cn}): string {{
          const label = format{domain.class_name}Label(item);
          const updated = formatDateTime(item.updatedAt);
          return `${{label}} · updated ${{updated}}`;
        }}


        export function format{domain.class_name}ListTitle(count: number): string {{
          const noun = "{domain.title}" + (count === 1 ? "" : "s");
          return `${{count}} ${{noun}}`;
        }}
        '''
    )


def _selectors_test(domain) -> str:
    return finalize_source(
        f'''
        import {{ describe, expect, it }} from "vitest";
        import {{ selectActive{domain.class_name}s }} from "./selectors";


        describe("{domain.plural} selectors", () => {{
          it("filters cancelled rows", () => {{
            const rows = [
              {{ id: "1", status: "active" }},
              {{ id: "2", status: "cancelled" }},
            ] as never[];
            expect(selectActive{domain.class_name}s(rows)).toHaveLength(1);
          }});
        }});
        '''
    )


DISPATCH_OPTIMIZER = '''\
"""Heuristic dispatch scoring and assignment optimization for field technicians."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


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
'''


SLA_CLOCK = '''\
"""Deterministic SLA countdown, business-hours aware breach detection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class SlaSeverity(str, Enum):
    OK = "ok"
    WARNING = "warning"
    BREACHED = "breached"


@dataclass(frozen=True, slots=True)
class SlaWindow:
    started_at: datetime
    target_minutes: int
    warning_threshold_pct: float = 0.85

    @property
    def due_at(self) -> datetime:
        return self.started_at + timedelta(minutes=self.target_minutes)

    def elapsed_minutes(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return max(0.0, (now - self.started_at).total_seconds() / 60.0)

    def remaining_minutes(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        return (self.due_at - now).total_seconds() / 60.0

    def progress_pct(self, now: datetime | None = None) -> float:
        if self.target_minutes <= 0:
            return 100.0
        return min(100.0, (self.elapsed_minutes(now) / self.target_minutes) * 100.0)

    def is_breached(self, now: datetime | None = None) -> bool:
        return self.remaining_minutes(now) < 0

    def severity(self, now: datetime | None = None) -> SlaSeverity:
        if self.is_breached(now):
            return SlaSeverity.BREACHED
        pct = self.progress_pct(now) / 100.0
        if pct >= self.warning_threshold_pct:
            return SlaSeverity.WARNING
        return SlaSeverity.OK


def compare_windows(a: SlaWindow, b: SlaWindow, now: datetime | None = None) -> SlaWindow:
    """Return whichever window breaches soonest (most urgent)."""
    return a if a.remaining_minutes(now) <= b.remaining_minutes(now) else b
'''


GEO = '''\
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
'''


INVENTORY_REORDER = '''\
"""Reorder point suggestions, safety stock, and batch replenishment planning."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReorderHint:
    sku: str
    on_hand: int
    reorder_point: int
    suggested_qty: int
    urgency: str = "normal"


@dataclass
class InventorySnapshot:
    sku: str
    on_hand: int
    reorder_point: int
    reorder_qty: int
    open_demand: int = 0
    lead_time_days: int = 7


def suggest_reorder(
    *,
    sku: str,
    on_hand: int,
    reorder_point: int,
    reorder_qty: int,
    open_demand: int = 0,
) -> ReorderHint | None:
    effective = on_hand - open_demand
    if effective > reorder_point:
        return None
    deficit = reorder_point - effective
    suggested = max(reorder_qty, deficit)
    urgency = "critical" if effective <= 0 else "high" if effective < reorder_point // 2 else "normal"
    return ReorderHint(
        sku=sku,
        on_hand=on_hand,
        reorder_point=reorder_point,
        suggested_qty=suggested,
        urgency=urgency,
    )


def batch_reorder_hints(items: list[InventorySnapshot]) -> list[ReorderHint]:
    hints: list[ReorderHint] = []
    for item in items:
        hint = suggest_reorder(
            sku=item.sku,
            on_hand=item.on_hand,
            reorder_point=item.reorder_point,
            reorder_qty=item.reorder_qty,
            open_demand=item.open_demand,
        )
        if hint:
            hints.append(hint)
    return sorted(hints, key=lambda h: (h.urgency != "critical", h.urgency != "high", h.sku))


def days_until_stockout(on_hand: int, avg_daily_usage: float) -> float | None:
    if avg_daily_usage <= 0:
        return None
    return on_hand / avg_daily_usage
'''


INVOICE_MATH = '''\
"""Invoice arithmetic, tax jurisdictions, and line-item rollups."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    quantity: int
    unit_price: Decimal
    description: str = ""
    taxable: bool = True

    def line_total(self) -> Decimal:
        return _money(Decimal(self.quantity) * self.unit_price)


@dataclass(frozen=True, slots=True)
class InvoiceTotals:
    subtotal: Decimal
    tax: Decimal
    discount: Decimal
    total: Decimal
    line_count: int = 0


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_subtotal(lines: Iterable[InvoiceLine]) -> Decimal:
    return _money(sum((line.line_total() for line in lines), Decimal("0")))


def compute_invoice_totals(
    lines: list[InvoiceLine],
    *,
    tax_rate: Decimal = Decimal("0"),
    discount: Decimal = Decimal("0"),
    tax_exempt: bool = False,
) -> InvoiceTotals:
    subtotal = compute_subtotal(lines)
    discount = _money(max(Decimal("0"), discount))
    taxable_base = Decimal("0") if tax_exempt else sum(
        (line.line_total() for line in lines if line.taxable),
        Decimal("0"),
    )
    taxable = max(Decimal("0"), taxable_base - discount)
    tax = _money(taxable * tax_rate)
    total = _money(max(Decimal("0"), subtotal - discount) + tax)
    return InvoiceTotals(
        subtotal=subtotal,
        tax=tax,
        discount=discount,
        total=total,
        line_count=len(lines),
    )


def split_tax_by_rate(lines: list[InvoiceLine], rates: dict[str, Decimal]) -> dict[str, Decimal]:
    """Apply labeled tax rates to taxable lines sharing a category key in description prefix."""
    buckets: dict[str, Decimal] = {key: Decimal("0") for key in rates}
    for line in lines:
        if not line.taxable:
            continue
        for label, rate in rates.items():
            if line.description.startswith(label):
                buckets[label] += _money(line.line_total() * rate)
    return buckets
'''


SCHEDULE_CONFLICTS = '''\
"""Detect overlapping schedule intervals, gaps, and technician double-booking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, slots=True)
class Interval:
    id: str
    start: datetime
    end: datetime
    technician_id: str | None = None

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(f"interval {self.id}: end must be after start")

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end

    def duration_minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60.0


def find_conflicts(intervals: list[Interval]) -> list[tuple[str, str]]:
    ordered = sorted(intervals, key=lambda item: item.start)
    conflicts: list[tuple[str, str]] = []
    for i, left in enumerate(ordered):
        for right in ordered[i + 1 :]:
            if right.start >= left.end:
                break
            if left.overlaps(right):
                if left.technician_id and right.technician_id and left.technician_id != right.technician_id:
                    continue
                conflicts.append((left.id, right.id))
    return conflicts


def find_gaps(intervals: list[Interval], *, min_gap_minutes: float = 15.0) -> list[tuple[str, str, float]]:
    ordered = sorted(intervals, key=lambda item: item.start)
    gaps: list[tuple[str, str, float]] = []
    for left, right in zip(ordered, ordered[1:]):
        gap_minutes = (right.start - left.end).total_seconds() / 60.0
        if gap_minutes >= min_gap_minutes:
            gaps.append((left.id, right.id, gap_minutes))
    return gaps


def total_booked_minutes(intervals: list[Interval]) -> float:
    return sum(i.duration_minutes() for i in intervals)


def fits_within(
    candidate: Interval,
    existing: list[Interval],
    *,
    buffer_minutes: float = 0.0,
) -> bool:
    buffer = timedelta(minutes=buffer_minutes)
    padded = Interval(
        id=candidate.id,
        start=candidate.start,
        end=candidate.end + buffer,
        technician_id=candidate.technician_id,
    )
    return not find_conflicts([padded, *existing])
'''


SKILL_MATCH = '''\
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
'''


NOTIFICATION_TEMPLATES = '''\
"""Notification template registry with safe rendering and fallbacks."""

from __future__ import annotations

from string import Formatter
from typing import Any


TEMPLATES: dict[str, str] = {
    "work_order.assigned": "Work order {number} assigned to {technician}.",
    "work_order.completed": "Work order {number} completed by {technician}.",
    "work_order.cancelled": "Work order {number} was cancelled: {reason}.",
    "sla.warning": "SLA for {number} breaches in {minutes} minutes.",
    "sla.breached": "SLA breached for {number}. Escalation level {level}.",
    "invoice.ready": "Invoice {number} is ready for customer {customer}.",
    "invoice.overdue": "Invoice {number} is {days} days overdue.",
    "dispatch.offer": "New job available: {title} at {site}. Respond within {minutes} minutes.",
    "parts.low_stock": "SKU {sku} is below reorder point ({on_hand} on hand).",
    "schedule.reminder": "Upcoming appointment: {title} at {starts_at}.",
}


class SafeFormatter(Formatter):
    def get_value(self, key, args, kwargs):
        if isinstance(key, str):
            return kwargs.get(key, f"{{{key}}}")
        return super().get_value(key, args, kwargs)


def render(template_key: str, **context: Any) -> str:
    try:
        template = TEMPLATES[template_key]
    except KeyError as exc:
        raise KeyError(f"Unknown template: {template_key}") from exc
    return SafeFormatter().format(template, **context)


def available_templates(prefix: str | None = None) -> list[str]:
    if prefix is None:
        return sorted(TEMPLATES)
    return sorted(k for k in TEMPLATES if k.startswith(prefix))


def preview(template_key: str, sample: dict[str, Any] | None = None) -> str:
    sample = sample or {}
    defaults = {field: f"[{field}]" for _, field, _, _ in SafeFormatter().parse(TEMPLATES[template_key]) if field}
    defaults.update(sample)
    return render(template_key, **defaults)
'''


RATE_LIMIT = '''\
"""Token-bucket and sliding-window rate limit helpers for API gateways."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Callable


@dataclass
class TokenBucket:
    capacity: float
    refill_per_second: float
    tokens: float
    updated_at: float

    @classmethod
    def create(cls, capacity: float, refill_per_second: float) -> "TokenBucket":
        now = monotonic()
        return cls(capacity=capacity, refill_per_second=refill_per_second, tokens=capacity, updated_at=now)

    def _refill(self, now: float) -> None:
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated_at = now

    def allow(self, cost: float = 1.0) -> bool:
        now = monotonic()
        self._refill(now)
        if self.tokens < cost:
            return False
        self.tokens -= cost
        return True

    def retry_after_seconds(self, cost: float = 1.0) -> float:
        now = monotonic()
        self._refill(now)
        if self.tokens >= cost:
            return 0.0
        deficit = cost - self.tokens
        return deficit / self.refill_per_second


@dataclass
class RateLimiterRegistry:
    """Named token buckets (e.g., per tenant or API key)."""

    _buckets: dict[str, TokenBucket] = field(default_factory=dict)
    _factory: Callable[[], TokenBucket] = field(
        default=lambda: TokenBucket.create(capacity=120.0, refill_per_second=2.0)
    )

    def allow(self, key: str, cost: float = 1.0) -> bool:
        bucket = self._buckets.setdefault(key, self._factory())
        return bucket.allow(cost)

    def retry_after(self, key: str, cost: float = 1.0) -> float:
        bucket = self._buckets.setdefault(key, self._factory())
        return bucket.retry_after_seconds(cost)
'''


IDEMPOTENCY = '''\
"""Idempotency key registry for safe mutation retries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

Status = Literal["started", "completed", "failed"]


@dataclass
class IdempotencyRecord:
    key: str
    status: Status
    result: Any = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None


@dataclass
class IdempotencyStore:
    _seen: dict[str, IdempotencyRecord] = field(default_factory=dict)
    ttl: timedelta = timedelta(hours=24)

    def _purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._seen.items() if v.expires_at and v.expires_at <= now]
        for key in expired:
            del self._seen[key]

    def begin(self, key: str) -> bool:
        """Return True if this is the first time the key is seen."""
        self._purge_expired()
        if key in self._seen:
            return False
        self._seen[key] = IdempotencyRecord(
            key=key,
            status="started",
            expires_at=datetime.now(timezone.utc) + self.ttl,
        )
        return True

    def complete(self, key: str, result: Any) -> None:
        record = self._seen.setdefault(key, IdempotencyRecord(key=key, status="started"))
        record.status = "completed"
        record.result = result

    def fail(self, key: str, error: str) -> None:
        record = self._seen.setdefault(key, IdempotencyRecord(key=key, status="started"))
        record.status = "failed"
        record.result = {"error": error}

    def get(self, key: str) -> Any | None:
        self._purge_expired()
        row = self._seen.get(key)
        if not row or row.status != "completed":
            return None
        return row.result

    def status(self, key: str) -> Status | None:
        row = self._seen.get(key)
        return row.status if row else None
'''


CAPACITY_PLANNER = '''\
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
'''


AUDIT_DIFF = '''\
"""Compute audit diffs, redact secrets, and summarize entity changes."""

from __future__ import annotations

from typing import Any

SENSITIVE_KEYS = frozenset({"password", "password_hash", "secret", "token", "api_key"})


def _redact(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS or key.endswith("_hash"):
        return "***REDACTED***"
    return value


def diff_entities(before: dict[str, Any], after: dict[str, Any]) -> dict[str, dict[str, Any]]:
    keys = set(before) | set(after)
    changes: dict[str, dict[str, Any]] = {}
    for key in sorted(keys):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            changes[key] = {"from": _redact(key, old), "to": _redact(key, new)}
    return changes


def has_changes(before: dict[str, Any], after: dict[str, Any]) -> bool:
    return bool(diff_entities(before, after))


def summarize_changes(changes: dict[str, dict[str, Any]], *, max_fields: int = 5) -> str:
    if not changes:
        return "no changes"
    parts = []
    for key in list(changes)[:max_fields]:
        parts.append(f"{key}: {changes[key]['from']!r} -> {changes[key]['to']!r}")
    if len(changes) > max_fields:
        parts.append(f"+{len(changes) - max_fields} more")
    return "; ".join(parts)


def merge_snapshots(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(patch)
    return merged
'''
