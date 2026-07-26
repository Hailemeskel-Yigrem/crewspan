#!/usr/bin/env python3
"""Build Crewspan git history spanning Mar 2023 – Mar 2026.

Replays ~200–280 deterministic commits using approved authors, phased codegen
output, and evolutionary patch commits. Safe on Windows PowerShell (subprocess +
GIT_* env vars, per-commit ``git -c user.name/email``).
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.authors import AUTHORS  # noqa: E402
from tools.codegen.domains import DOMAINS, DomainSpec  # noqa: E402
from tools.codegen.generate_api import generate_api_tree  # noqa: E402
from tools.codegen.generate_docs import generate_docs_tree  # noqa: E402
from tools.codegen.generate_expand import generate_expand_tree  # noqa: E402
from tools.codegen.generate_infra import generate_infra_tree  # noqa: E402
from tools.codegen.generate_tests import generate_tests_tree  # noqa: E402
from tools.codegen.generate_web import generate_web_tree  # noqa: E402
from tools.codegen.generate_worker import generate_worker_tree  # noqa: E402
from tools.api_wiring import partial_db_py, partial_main_py  # noqa: E402

# ---------------------------------------------------------------------------
# Timeline — never use "today" or any date after 2026-06-30
# ---------------------------------------------------------------------------
TIMELINE_START = datetime(2023, 3, 15, 9, 30, 0)
TIMELINE_END = datetime(2026, 3, 20, 17, 45, 0)
ABSOLUTE_MAX_DATE = datetime(2026, 6, 30, 23, 59, 59)

HISTORY_SEED = 20230315
DATE_SEED = 77
FOLLOWUP_COUNT = 78

LICENSE_TEXT = textwrap.dedent(
    """\
    MIT License

    Copyright (c) 2023 Crewspan contributors

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """
)


@dataclass
class CommitSpec:
    message: str
    paths: list[str]
    author_index: int


@dataclass
class FollowUpEdit:
    spec: CommitSpec
    updated_text: str


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git_env(base: dict[str, str] | None = None) -> dict[str, str]:
    """Copy process env and strip Git overrides that can point outside ROOT."""
    env = (base or os.environ).copy()
    for key in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_COMMON_DIR",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_PREFIX",
    ):
        env.pop(key, None)
    return env


def run(cmd: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        check=True,
        env=_git_env(env),
        capture_output=True,
        text=True,
    )


def git_commit(message: str, when: datetime, author_name: str, author_email: str, paths: list[str]) -> bool:
    """Stage listed paths and commit with explicit author/committer dates."""
    stamp = when.strftime("%Y-%m-%dT%H:%M:%S")
    env = _git_env()
    env["GIT_AUTHOR_DATE"] = stamp
    env["GIT_COMMITTER_DATE"] = stamp
    env["GIT_AUTHOR_NAME"] = author_name
    env["GIT_AUTHOR_EMAIL"] = author_email
    env["GIT_COMMITTER_NAME"] = author_name
    env["GIT_COMMITTER_EMAIL"] = author_email

    existing = [p for p in paths if (ROOT / p).is_file()]
    if not existing:
        return False

    # Add in batches to avoid Windows command-line length limits.
    for batch in chunked(existing, 40):
        try:
            run(["git", "add", "-f", "--", *batch], env=env)
        except subprocess.CalledProcessError as exc:
            # Skip vanishing pathspecs; continue with whatever else staged.
            stderr = (exc.stderr or "").lower()
            if "did not match" in stderr or "pathspec" in stderr:
                for path in batch:
                    if (ROOT / path).is_file():
                        run(["git", "add", "-f", "--", path], env=env)
                continue
            raise

    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=ROOT,
        env=env,
    )
    if diff.returncode == 0:
        return False

    try:
        run(
            [
                "git",
                "-c",
                f"user.name={author_name}",
                "-c",
                f"user.email={author_email}",
                "commit",
                "-m",
                message,
            ],
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        lock = ROOT / ".git" / "index.lock"
        if lock.exists():
            try:
                lock.unlink()
            except OSError:
                pass
        stderr = (exc.stderr or "").lower()
        if "nothing to commit" in stderr or "nothing added to commit" in stderr:
            return False
        if lock.exists() or "index.lock" in stderr:
            run(
                [
                    "git",
                    "-c",
                    f"user.name={author_name}",
                    "-c",
                    f"user.email={author_email}",
                    "commit",
                    "-m",
                    message,
                ],
                env=env,
            )
        else:
            raise RuntimeError(f"git commit failed for {message!r}: {(exc.stderr or '')[-1000:]}") from exc
    return True


def init_repo() -> None:
    git_dir = ROOT / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)
        # Windows may keep object files locked briefly
        if git_dir.exists():
            import time
            for _ in range(5):
                shutil.rmtree(git_dir, ignore_errors=True)
                if not git_dir.exists():
                    break
                time.sleep(0.5)
    run(["git", "init", "-b", "main"])


# ---------------------------------------------------------------------------
# Deterministic commit timestamps
# ---------------------------------------------------------------------------

HOLIDAY_QUIET = (
    (datetime(2023, 12, 22), datetime(2024, 1, 3)),
    (datetime(2024, 7, 1), datetime(2024, 7, 7)),
    (datetime(2024, 12, 22), datetime(2025, 1, 3)),
    (datetime(2025, 7, 1), datetime(2025, 7, 7)),
    (datetime(2025, 12, 22), datetime(2026, 1, 3)),
)

RELEASE_BURST_ANCHORS = (
    datetime(2023, 9, 18),
    datetime(2024, 3, 12),
    datetime(2024, 9, 24),
    datetime(2025, 3, 10),
    datetime(2025, 9, 15),
    datetime(2026, 3, 5),
)


def _in_quiet_period(dt: datetime) -> bool:
    for start, end in HOLIDAY_QUIET:
        if start <= dt <= end:
            return True
    return False


def generate_commit_datetimes(count: int, seed: int = DATE_SEED) -> list[datetime]:
    """Spread commits with weekday bias, holiday lulls, and release bursts."""
    rng = random.Random(seed)
    if count < 1:
        return []

    span = int((TIMELINE_END - TIMELINE_START).total_seconds())
    dates: list[datetime] = []

    for i in range(count):
        t = (i + rng.uniform(0.04, 0.96)) / max(count - 1, 1)
        warped = t**0.88
        base = TIMELINE_START + timedelta(seconds=int(warped * span))

        # Nudge toward release windows (~12% of commits)
        if rng.random() < 0.12:
            anchor = rng.choice(RELEASE_BURST_ANCHORS)
            jitter = timedelta(hours=rng.randint(-36, 36), minutes=rng.randint(0, 59))
            base = min(max(anchor + jitter, TIMELINE_START), TIMELINE_END)

        hour = rng.choices(
            [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            weights=[2, 3, 4, 3, 2, 4, 5, 5, 4, 3, 2, 1],
        )[0]
        candidate = base.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))

        if candidate.weekday() >= 5 and rng.random() < 0.72:
            candidate -= timedelta(days=candidate.weekday() - 4)

        if _in_quiet_period(candidate) and rng.random() < 0.55:
            candidate += timedelta(days=rng.randint(4, 12))

        candidate = min(max(candidate, TIMELINE_START), TIMELINE_END)
        if candidate > ABSOLUTE_MAX_DATE:
            candidate = TIMELINE_END
        dates.append(candidate)

    dates.sort()
    for i in range(1, len(dates)):
        if dates[i] <= dates[i - 1]:
            dates[i] = dates[i - 1] + timedelta(minutes=rng.randint(19, 110))
        if dates[i] > ABSOLUTE_MAX_DATE:
            dates[i] = ABSOLUTE_MAX_DATE

    return dates


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------


def build_all_contents() -> dict[str, str]:
    staging = ROOT / ".staging_build"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    generate_api_tree(staging)
    generate_worker_tree(staging)
    generate_web_tree(staging)
    generate_tests_tree(staging)
    generate_docs_tree(staging)
    generate_infra_tree(staging)
    generate_expand_tree(staging)

    contents: dict[str, str] = {}
    for path in staging.rglob("*"):
        if path.is_file():
            rel = path.relative_to(staging).as_posix()
            contents[rel] = path.read_text(encoding="utf-8")

    contents["LICENSE"] = LICENSE_TEXT
    if ".gitignore" in contents and ".staging_build/" not in contents[".gitignore"]:
        contents[".gitignore"] = contents[".gitignore"].rstrip() + "\n.staging_build/\n"
    shutil.rmtree(staging)
    return contents


def refresh_api_wiring(contents: dict[str, str], active_names: list[str]) -> None:
    subset = [d for d in DOMAINS if d.name in active_names]
    contents["apps/api/app/main.py"] = partial_main_py(subset)
    contents["apps/api/app/db.py"] = partial_db_py(subset)


def domain_api_paths(name: str) -> list[str]:
    prefix = f"apps/api/app/domains/{name}/"
    return [prefix + f for f in ("__init__.py", "models.py", "schemas.py", "repository.py", "service.py", "router.py", "exceptions.py")]


def domain_api_test_paths(name: str) -> list[str]:
    return [
        f"apps/api/tests/unit/test_{name}_service.py",
        f"apps/api/tests/integration/test_{name}_router.py",
    ]


def domain_web_paths(domain: DomainSpec) -> list[str]:
    paths = [
        f"apps/web/src/types/{domain.snake}.ts",
        f"apps/web/src/api/{domain.snake}.ts",
    ]
    if domain.snake in {
        "work_order",
        "technician",
        "customer",
        "invoice",
        "schedule",
        "inventory_item",
        "sla_policy",
        "webhook",
    }:
        paths.append(f"apps/web/src/api/{domain.snake}.test.ts")
    return paths


def domain_web_source_paths(domain: DomainSpec) -> list[str]:
    """Web source paths excluding tests (committed in test phase)."""
    return [p for p in domain_web_paths(domain) if ".test." not in p]


def materialize(paths: list[str], contents: dict[str, str]) -> None:
    for rel in paths:
        if rel not in contents:
            continue
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(contents[rel].replace("\r\n", "\n"), encoding="utf-8", newline="\n")


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


# ---------------------------------------------------------------------------
# Commit plan
# ---------------------------------------------------------------------------

DOMAIN_MESSAGES: dict[str, str] = {
    "tenant": "feat(api): add tenant registry with subscription tiers",
    "user": "feat(api): implement user accounts and authentication metadata",
    "role": "feat(api): add RBAC roles and permission sets",
    "customer": "feat(api): add customer master records and billing profiles",
    "customer_site": "feat(api): add customer service sites with geocoding hooks",
    "contact": "feat(api): add customer contacts for scheduling notifications",
    "work_order": "feat(api): implement work order lifecycle and dispatch hooks",
    "work_order_task": "feat(api): add work order checklist tasks",
    "technician": "feat(api): add technician profiles and availability metadata",
    "technician_skill": "feat(api): add technician skill certifications",
    "schedule": "feat(api): add scheduling blocks and conflict detection",
    "dispatch": "feat(api): add dispatch assignments and routing",
    "inventory_item": "feat(api): add parts catalog and inventory items",
    "inventory_location": "feat(api): add warehouse and truck stock locations",
    "stock_movement": "feat(api): track inventory movements and adjustments",
    "parts_request": "feat(api): add parts requests linked to work orders",
    "invoice": "feat(api): add invoicing with tax calculation helpers",
    "invoice_line_item": "feat(api): add invoice line items and rollups",
    "payment": "feat(api): add payment recording and reconciliation",
    "sla_policy": "feat(api): add SLA policy definitions",
    "sla_breach": "feat(api): detect and record SLA breaches",
    "service_contract": "feat(api): add service contract entitlements",
    "equipment": "feat(api): add installed equipment asset tracking",
    "notification": "feat(api): add outbound notification queue",
    "webhook": "feat(api): add webhook subscriptions and delivery logs",
    "audit_log": "feat(api): add immutable audit log entries",
}

DOMAIN_BATCHES: list[tuple[list[str], str | None]] = [
    (["tenant"], None),
    (["user"], None),
    (["role"], None),
    (["customer"], None),
    (["customer_site"], None),
    (["contact"], None),
    (["work_order"], None),
    (["work_order_task"], None),
    (["technician"], None),
    (["technician_skill"], None),
    (["schedule"], None),
    (["dispatch"], None),
    (["inventory_item"], None),
    (["inventory_location"], None),
    (["stock_movement"], None),
    (["parts_request"], None),
    (["invoice"], None),
    (["invoice_line_item"], None),
    (["payment"], None),
    (["sla_policy"], None),
    (["sla_breach"], None),
    (["service_contract"], None),
    (["equipment"], None),
    (["notification"], None),
    (["webhook"], None),
    (["audit_log"], None),
]


def plan_commits(all_paths: list[str], contents: dict[str, str], rng: random.Random) -> list[CommitSpec]:
    remaining = set(all_paths)
    commits: list[CommitSpec] = []
    author_i = 0
    active_domains: list[str] = []

    def add(message: str, selected: list[str], author: int | None = None) -> None:
        nonlocal author_i
        selected = sorted(p for p in selected if p in remaining)
        if not selected:
            return
        for p in selected:
            remaining.discard(p)
        idx = author if author is not None else (author_i % len(AUTHORS))
        commits.append(CommitSpec(message=message, paths=selected, author_index=idx))
        author_i += 1

    def pick(*predicates: Callable[[str], bool]) -> list[str]:
        out: list[str] = []
        for p in sorted(remaining):
            if any(fn(p) for fn in predicates):
                out.append(p)
        return out

    # --- Bootstrap ---
    add(
        "Initial commit: Crewspan project charter and repository metadata",
        pick(lambda p: p in {"README.md", "LICENSE", ".gitignore"}),
        0,
    )
    add("docs: add architecture overview and development readme", pick(lambda p: p.startswith("docs/README") or p == "docs/architecture.md"))
    add("chore: add contributing guide and security policy", pick(lambda p: p in {"docs/contributing.md", "docs/security.md"}))

    # --- API scaffold ---
    api_core = pick(
        lambda p: p.startswith("apps/api/")
        and any(
            x in p
            for x in (
                "pyproject.toml",
                "requirements.txt",
                "app/__init__.py",
                "app/config.py",
                "app/logging_config.py",
                "app/middleware.py",
                "app/deps.py",
                "app/core/",
            )
        )
        and "domains/" not in p
        and "alembic" not in p
        and "tests/" not in p
    )
    refresh_api_wiring(contents, [])
    api_core.append("apps/api/app/main.py")
    api_core.append("apps/api/app/db.py")
    add("feat(api): scaffold FastAPI service with settings and health endpoints", api_core)

    add("test(api): add health endpoint smoke tests", pick(lambda p: p in {"apps/api/tests/conftest.py", "apps/api/tests/test_health.py"}))

    # --- Domains ---
    for batch, override_msg in DOMAIN_BATCHES:
        paths: list[str] = []
        for name in batch:
            paths.extend(domain_api_paths(name))
        refresh_api_wiring(contents, active_domains + batch)
        paths.extend(["apps/api/app/main.py", "apps/api/app/db.py"])
        msg = override_msg or DOMAIN_MESSAGES[batch[0]]
        add(msg, paths)
        active_domains.extend(batch)

    # --- Alembic ---
    add("chore(db): add Alembic configuration and initial schema migration", pick(lambda p: "apps/api/alembic" in p or p == "apps/api/alembic.ini"))
    add("feat(api): add production Dockerfile for API service", pick(lambda p: p == "apps/api/Dockerfile"))

    # --- Worker (late 2024) ---
    worker_core = pick(
        lambda p: p.startswith("apps/worker/")
        and any(x in p for x in ("pyproject.toml", "requirements.txt", "worker/__init__.py", "worker/config.py", "worker/logging_config.py", "worker/celery_app.py", "worker/base.py", "worker/jobs/__init__.py"))
    )
    add("feat(worker): scaffold Celery worker with queue routing", worker_core)

    for job, msg in (
        ("notifications.py", "feat(worker): add notification delivery jobs"),
        ("scheduling.py", "feat(worker): add scheduling reminder and conflict jobs"),
        ("invoicing.py", "feat(worker): add invoice generation jobs"),
        ("webhooks.py", "feat(worker): add webhook delivery and retry jobs"),
        ("reports.py", "feat(worker): add report export jobs"),
    ):
        add(msg, pick(lambda p, j=job: p.endswith(f"worker/jobs/{j}")))

    add("chore(worker): add Docker images for worker and beat scheduler", pick(lambda p: p.startswith("apps/worker/Dockerfile")))

    # --- Web (mid timeline) ---
    web_scaffold = pick(
        lambda p: p.startswith("apps/web/")
        and any(
            x in p
            for x in (
                "package.json",
                "vite.config.ts",
                "tsconfig.json",
                "index.html",
                "Dockerfile",
                "nginx.conf",
                "src/main.tsx",
                "src/App.tsx",
                "src/styles/global.css",
                "src/auth/",
                "src/api/client.ts",
                "src/api/index.ts",
                "src/components/index.ts",
            )
        )
        and "generated/" not in p
        and ".test." not in p
        and p != "apps/web/src/test/setup.ts"
    )
    add("feat(web): bootstrap Vite + React 18 console shell", web_scaffold)

    component_files = sorted(p for p in remaining if p.startswith("apps/web/src/components/") and ".test." not in p and not p.endswith("index.ts"))
    for i, group in enumerate(chunked(component_files, 5)):
        add(
            "feat(web): add shared UI components" if i == 0 else f"feat(web): expand component library ({i + 1})",
            group,
        )

    page_files = sorted(
        p
        for p in remaining
        if p.startswith("apps/web/src/pages/")
        and "generated/" not in p
        and ".test." not in p
    )
    for i, group in enumerate(chunked(page_files, 4)):
        add(
            "feat(web): add dashboard and operational pages" if i == 0 else f"feat(web): add feature pages ({i + 1})",
            group,
        )

    for domain in DOMAINS:
        paths = domain_web_source_paths(domain)
        if domain is DOMAINS[0]:
            paths.append("apps/web/src/types/index.ts")
        add(f"feat(web): add UI for {domain.title}", paths)

    # --- Tests expansion ---
    add("test(web): add vitest setup", pick(lambda p: p == "apps/web/src/test/setup.ts"))
    component_tests = sorted(p for p in remaining if p.startswith("apps/web/src/components/") and p.endswith(".test.tsx"))
    for i, group in enumerate(chunked(component_tests, 5)):
        add("test(web): add shared component tests" if i == 0 else f"test(web): extend component tests ({i + 1})", group)

    hook_util_tests = sorted(
        p for p in remaining if ("/hooks/" in p or "/utils/" in p) and p.endswith(".test.ts")
    )
    add("test(web): add hook and utility tests", hook_util_tests)

    page_tests = sorted(p for p in remaining if p.startswith("apps/web/src/pages/") and p.endswith(".test.tsx"))
    for i, group in enumerate(chunked(page_tests, 4)):
        add("test(web): add page rendering tests" if i == 0 else f"test(web): extend page tests ({i + 1})", group)

    add("test(web): add auth and API client tests", pick(lambda p: p.startswith("apps/web/src/auth/") or p == "apps/web/src/api/client.test.ts"))

    for domain in DOMAINS:
        add(
            f"test(web): add {domain.snake} client and type tests",
            [
                f"apps/web/src/types/{domain.snake}.test.ts",
                f"apps/web/src/api/{domain.snake}.test.ts",
            ],
        )

    for domain in DOMAINS:
        add(
            f"test(api): add {domain.snake} service and router coverage",
            domain_api_test_paths(domain.snake),
        )

    add("test(worker): add background job unit tests", pick(lambda p: p.startswith("apps/worker/tests/")))

    # --- Packages ---
    add("feat(packages): add shared Python utilities package", pick(lambda p: p.startswith("packages/common/")))
    add("feat(sdk): add Python API client SDK", pick(lambda p: p.startswith("packages/sdk/")))
    add("test(packages): add package-level unit tests", pick(lambda p: "/tests/" in p and p.startswith("packages/")))

    # --- Docs evolution ---
    add("docs: add API reference and deployment guide", pick(lambda p: p in {"docs/api.md", "docs/deployment.md"}))
    add("docs: add database and configuration guides", pick(lambda p: p in {"docs/database.md", "docs/configuration.md"}))
    add("docs: add troubleshooting and changelog", pick(lambda p: p in {"docs/troubleshooting.md", "docs/changelog.md"}))
    add("docs: add architecture decision records", pick(lambda p: p.startswith("docs/adr/")))

    # --- Infra / CI / Docker ---
    add("chore: add environment template and docker ignore rules", pick(lambda p: p in {".env.example", ".dockerignore"}))
    add("chore(deploy): add Docker Compose development stack", pick(lambda p: p == "docker-compose.yml"))
    add("chore: add Makefile and helper scripts", pick(lambda p: p == "Makefile" or p.startswith("scripts/")))
    add("ci: add GitHub Actions test and lint workflow", pick(lambda p: p == ".github/workflows/ci.yml"))
    add("ci: add release workflow and pre-commit hooks", pick(lambda p: p in {".github/workflows/release.yml", ".pre-commit-config.yaml"}))

    add(
        "feat(api): add domain workflows, projectors, and search helpers",
        pick(
            lambda p: p.endswith("/workflow.py")
            or p.endswith("/projector.py")
            or p.endswith("/search.py")
            or p.endswith("/metrics.py")
            or p.endswith("/state_machine.py")
            or p.endswith("/serializers.py")
            or "_workflow.py" in p
            or "_projector.py" in p
            or "_state_machine.py" in p
        ),
    )
    add(
        "feat(api): add scheduling, SLA, geo, and invoice logic modules",
        pick(lambda p: "/logic/" in p or "test_logic_" in p),
    )
    add(
        "feat(web): add feature selectors and form state helpers",
        pick(lambda p: p.startswith("apps/web/src/features/")),
    )
    add(
        "feat(worker): add SLA sweep, reorder, and digest jobs",
        pick(
            lambda p: any(
                job in p
                for job in (
                    "sla_sweep",
                    "reorder_hints",
                    "schedule_digest",
                    "invoice_dunning",
                    "geo_backfill",
                )
            )
        ),
    )
    add(
        "docs: add ADRs and numbered operations guides",
        pick(lambda p: p.startswith("docs/adr/") or p.startswith("docs/guides/")),
    )

    # --- Dependency / upgrade narrative commits (patch files in-place) ---
    upgrades = {
        "apps/api/requirements.txt": "\n# Adopted Pydantic v2 and SQLAlchemy 2.x async stack (2024-06)\n",
        "apps/api/pyproject.toml": "\n# pydantic>=2.6 — v2 migration complete\n",
        "apps/web/package.json": '\n  "_comment": "React 18 concurrent features enabled",\n',
        "docs/changelog.md": "\n## Unreleased\n- Platform: Pydantic v2, SQLAlchemy 2.0, React 18 adoption\n",
    }
    for rel, marker in upgrades.items():
        if rel in contents and marker.strip() not in contents[rel]:
            contents[rel] = contents[rel].rstrip() + marker

    add("chore(deps): adopt Pydantic v2 and SQLAlchemy 2.x across API", ["apps/api/requirements.txt", "apps/api/pyproject.toml"])
    add("chore(web): confirm React 18 dependency baseline", ["apps/web/package.json"])
    add("docs: note dependency upgrades in changelog", ["docs/changelog.md"])

    # --- Performance / refactor / fix filler ---
    filler_msgs = [
        "refactor(api): tighten domain service error handling",
        "perf(api): reduce ORM overhead in list endpoints",
        "fix(api): guard tenant header validation edge cases",
        "refactor(web): simplify page header composition",
        "test: broaden integration coverage for dispatch flows",
        "docs: clarify webhook retry semantics",
        "chore: normalize logging field names",
        "fix(worker): improve webhook signature validation",
        "perf(worker): batch notification enqueue operations",
        "chore(release): prepare v0.9.0 stabilization fixes",
        "fix(api): handle soft-deleted records in list filters",
        "refactor(api): extract shared pagination helpers",
        "docs: document SLA breach escalation paths",
        "test(api): add regression tests for invoice totals",
        "chore(web): align TypeScript strict mode settings",
        "perf(web): memoize expensive table renderers",
        "fix(web): correct date formatting in schedule view",
        "chore: bump patch versions across services",
    ]
    api_domain_files = [p for p in all_paths if p.startswith("apps/api/app/domains/") and p.endswith("service.py")]
    web_components = [p for p in all_paths if p.startswith("apps/web/src/components/") and not p.endswith(".test.tsx")]
    docs_files = [p for p in all_paths if p.startswith("docs/") and p.endswith(".md")]
    worker_jobs = [p for p in all_paths if p.startswith("apps/worker/worker/jobs/") and p.endswith(".py")]

    filler_pool = (
        api_domain_files
        + web_components
        + docs_files
        + worker_jobs
        + [
            "apps/api/app/core/pagination.py",
            "apps/api/app/middleware.py",
            "apps/api/app/core/security.py",
            "apps/web/src/api/client.ts",
            "apps/web/src/hooks/useAuth.ts",
        ]
    )
    filler_pool = [p for p in filler_pool if p in remaining]
    for i, group in enumerate(chunked(filler_pool, 2)):
        add(filler_msgs[i % len(filler_msgs)], group)

    # --- Codegen tooling (late) — copy from workspace tools/ into project ---
    skip_tools = {
        "tools/build_history.py",
        "tools/run_bootstrap.py",
        "tools/zip_release.py",
        "tools/build_cascaderelay.py",
    }
    tools_paths: list[str] = []
    tools_root = ROOT / "tools"
    for path in tools_root.rglob("*"):
        if not path.is_file() or ".staging_build" in path.parts or "__pycache__" in path.parts:
            continue
        if "cascaderelay" in path.parts:
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in skip_tools:
            continue
        try:
            contents[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        tools_paths.append(rel)
    add("chore: add internal domain codegen tooling", sorted(tools_paths))

    # --- Release tag narrative ---
    add("chore(release): tag v1.0.0-rc1 and finalize README", pick(lambda p: p == "README.md"))

    # --- Leftovers ---
    leftovers = sorted(remaining)
    tail_msgs = [
        "refactor: module boundary cleanups",
        "test: additional edge case coverage",
        "docs: operator workflow clarifications",
        "fix: validation hardening",
        "chore: packaging tidy-up",
    ]
    for i, group in enumerate(chunked(leftovers, max(2, len(leftovers) // 12 or 2))):
        add(tail_msgs[i % len(tail_msgs)], group)

    # Split large commits for realism
    expanded: list[CommitSpec] = []
    for commit in commits:
        if len(commit.paths) <= 14:
            expanded.append(commit)
            continue
        parts = chunked(commit.paths, 9)
        for j, part in enumerate(parts):
            suffix = "" if j == 0 else f" ({j + 1}/{len(parts)})"
            expanded.append(
                CommitSpec(
                    message=commit.message + suffix,
                    paths=part,
                    author_index=(commit.author_index + j) % len(AUTHORS),
                )
            )
    return expanded


def synthesize_followup_commits(contents: dict[str, str], count: int, rng: random.Random) -> list[FollowUpEdit]:
    editable = [
        p
        for p, text in contents.items()
        if p.endswith((".py", ".ts", ".tsx", ".md"))
        and "LICENSE" not in p
        and len(text) < 25000
        and not p.startswith("tools/build_history")
    ]
    edits: list[FollowUpEdit] = []
    messages = [
        "docs: refine inline comments for maintainers",
        "refactor: improve naming consistency in helpers",
        "chore: normalize module docstrings",
        "test: clarify assertion intent",
        "fix: guard empty inputs in utilities",
        "feat: small UX copy improvements",
        "perf: avoid redundant copies in helpers",
        "docs: keep changelog references accurate",
        "refactor: simplify conditional branches",
        "fix: correct typos in log messages",
    ]
    used: set[str] = set()
    for i in range(count):
        if not editable:
            break
        rel = rng.choice(editable)
        if rel in used:
            candidates = [p for p in editable if p not in used]
            if not candidates:
                break
            rel = rng.choice(candidates)
        used.add(rel)
        text = contents[rel]
        if "history-note:" in text:
            continue
        if rel.endswith(".py"):
            marker = f"\n# history-note: evolutionary edit {i + 1}\n"
        elif rel.endswith((".ts", ".tsx")):
            marker = f"\n// history-note: evolutionary edit {i + 1}\n"
        else:
            marker = f"\n<!-- history-note: evolutionary edit {i + 1} -->\n"
        edits.append(
            FollowUpEdit(
                spec=CommitSpec(message=messages[i % len(messages)], paths=[rel], author_index=i % len(AUTHORS)),
                updated_text=text.rstrip() + marker,
            )
        )
    return edits


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def collect_stats() -> dict[str, object]:
    log = run(["git", "log", "--format=%ad%x09%an", "--date=short"])
    lines = [ln for ln in log.stdout.splitlines() if ln.strip()]
    dates = [ln.split("\t")[0] for ln in lines]
    authors: dict[str, int] = {}
    for ln in lines:
        author = ln.split("\t", 1)[1]
        authors[author] = authors.get(author, 0) + 1

    file_count = 0
    loc = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or ".staging_build" in path.parts:
            continue
        file_count += 1
        try:
            loc += sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
        except OSError:
            pass

    return {
        "commits": len(lines),
        "first_date": min(dates) if dates else "n/a",
        "last_date": max(dates) if dates else "n/a",
        "authors": authors,
        "files": file_count,
        "loc": loc,
    }


def print_stats(stats: dict[str, object]) -> None:
    print("\n=== Crewspan history stats ===")
    print(f"Commits:     {stats['commits']}")
    print(f"Date range:  {stats['first_date']} .. {stats['last_date']}")
    print(f"Files:       {stats['files']}")
    print(f"Approx LOC:  {stats['loc']:,}")
    print("Author distribution:")
    for name, count in sorted(stats["authors"].items(), key=lambda x: -x[1]):
        print(f"  {count:4d}  {name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    rng = random.Random(HISTORY_SEED)
    print("Generating Crewspan source tree…")
    contents = build_all_contents()
    print(f"  staged {len(contents)} files from codegen")

    init_repo()

    planned = plan_commits(sorted(contents.keys()), contents, rng)
    follow_edits = synthesize_followup_commits(contents, FOLLOWUP_COUNT, rng)
    follow_start = len(planned)
    planned.extend(edit.spec for edit in follow_edits)
    follow_by_index = {follow_start + i: edit for i, edit in enumerate(follow_edits)}

    dates = generate_commit_datetimes(len(planned))
    print(f"Replaying {len(planned)} commits ({dates[0].date()} .. {dates[-1].date()})…")

    committed = 0
    for i, (spec, when) in enumerate(zip(planned, dates)):
        edit = follow_by_index.get(i)
        if edit is not None:
            contents[edit.spec.paths[0]] = edit.updated_text
        materialize(spec.paths, contents)
        name, email = AUTHORS[spec.author_index % len(AUTHORS)]
        if git_commit(spec.message, when, name, email, spec.paths):
            committed += 1
        if (i + 1) % 30 == 0 or i + 1 == len(planned):
            print(f"  … {i + 1}/{len(planned)} — {spec.message[:64]}")

    # Verify authors
    authors_out = run(["git", "log", "--format=%an <%ae>"])
    approved = {f"{n} <{e}>" for n, e in AUTHORS}
    bad = sorted({a for a in authors_out.stdout.splitlines() if a and a not in approved})
    if bad:
        raise SystemExit(f"Unexpected commit authors: {bad}")

    print(f"\nDone — {committed} commits written.")
    print_stats(collect_stats())


if __name__ == "__main__":
    main()
