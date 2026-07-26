"""Generate Crewspan infrastructure, scripts, and shared packages."""

from __future__ import annotations

import textwrap
from pathlib import Path


def _write(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = textwrap.dedent(content).rstrip() + "\n" if content.strip() else content
    path.write_text(normalized, encoding="utf-8")
    return len(normalized.splitlines())


def _docker_compose() -> str:
    return """services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: crewspan
      POSTGRES_PASSWORD: crewspan
      POSTGRES_DB: crewspan
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U crewspan"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      CREWSPAN_DATABASE_URL: postgresql+asyncpg://crewspan:crewspan@postgres:5432/crewspan
      CREWSPAN_REDIS_URL: redis://redis:6379/0
      CREWSPAN_SECRET_KEY: dev-secret-change-in-production
      CREWSPAN_CORS_ORIGINS: '["http://localhost:3000"]'
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - api

  worker:
    build:
      context: ./apps/worker
      dockerfile: Dockerfile
    environment:
      CREWSPAN_DATABASE_URL: postgresql+asyncpg://crewspan:crewspan@postgres:5432/crewspan
      CREWSPAN_CELERY_BROKER_URL: redis://redis:6379/1
      CREWSPAN_CELERY_RESULT_BACKEND: redis://redis:6379/2
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker-beat:
    build:
      context: ./apps/worker
      dockerfile: Dockerfile.beat
    environment:
      CREWSPAN_CELERY_BROKER_URL: redis://redis:6379/1
      CREWSPAN_CELERY_RESULT_BACKEND: redis://redis:6379/2
    depends_on:
      - redis
      - worker

volumes:
  postgres_data:
"""


def _ci_yml() -> str:
    return """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  api-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: crewspan
          POSTGRES_PASSWORD: crewspan
          POSTGRES_DB: crewspan_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install API dependencies
        run: pip install -r apps/api/requirements.txt pytest pytest-asyncio ruff
      - name: Lint
        run: ruff check apps/api packages
      - name: Test
        env:
          CREWSPAN_DATABASE_URL: postgresql+asyncpg://crewspan:crewspan@localhost:5432/crewspan_test
        run: pytest apps/api/tests -v

  web-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: Install and test
        working-directory: apps/web
        run: |
          npm ci
          npm test

  worker-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install and test
        run: |
          pip install -r apps/worker/requirements.txt pytest
          pytest apps/worker/tests -v
"""


def _release_yml() -> str:
    return """name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api, web, worker]
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Build image
        uses: docker/build-push-action@v5
        with:
          context: ./apps/${{ matrix.service }}
          push: false
          tags: crewspan/${{ matrix.service }}:${{ github.ref_name }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""


def _env_example() -> str:
    return """# Crewspan Environment Configuration
# Copy to .env and adjust for your environment

CREWSPAN_ENVIRONMENT=development
CREWSPAN_DEBUG=false

# Database
CREWSPAN_DATABASE_URL=postgresql+asyncpg://crewspan:crewspan@localhost:5432/crewspan

# Redis
CREWSPAN_REDIS_URL=redis://localhost:6379/0
CREWSPAN_CELERY_BROKER_URL=redis://localhost:6379/1
CREWSPAN_CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
CREWSPAN_SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32

# API
CREWSPAN_CORS_ORIGINS=["http://localhost:3000"]
CREWSPAN_ACCESS_TOKEN_EXPIRE_MINUTES=60
CREWSPAN_LOG_LEVEL=INFO
CREWSPAN_LOG_JSON=true
"""


def _makefile() -> str:
    return """.PHONY: up down migrate seed test lint install dev-api dev-web health

up:
\tdocker compose up -d

down:
\tdocker compose down

migrate:
\tcd apps/api && alembic upgrade head

seed:
\tpython scripts/seed.py

test:
\tpytest apps/api/tests apps/worker/tests packages -v
\tcd apps/web && npm test

lint:
\truff check apps packages
\tcd apps/web && npm run lint

install:
\tpip install -r apps/api/requirements.txt
\tpip install -r apps/worker/requirements.txt
\tpip install -e packages/common -e packages/sdk
\tcd apps/web && npm ci

dev-api:
\tcd apps/api && uvicorn app.main:app --reload --port 8000

dev-web:
\tcd apps/web && npm run dev

health:
\tbash scripts/healthcheck.sh

generate:
\tpython -m tools.codegen.generate_api
\tpython -m tools.codegen.generate_web
\tpython -m tools.codegen.generate_tests
\tpython -m tools.codegen.generate_docs
\tpython -m tools.codegen.generate_infra
"""


def _gitignore() -> str:
    return """# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
dist/
build/
.venv/
venv/
.env
*.db

# Node
node_modules/
apps/web/dist/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db

# Test / coverage
.coverage
htmlcov/
.pytest_cache/
apps/web/coverage/

# Docker
postgres_data/

# Exports
/tmp/crewspan/
"""


def _dockerignore() -> str:
    return """.git
.gitignore
.env
.venv
venv
__pycache__
*.pyc
node_modules
dist
coverage
.pytest_cache
*.md
docs/
tests/
"""


def _precommit_config() -> str:
    return """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
"""


def _migrate_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../apps/api"
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete."
"""


def _seed_script() -> str:
    return '''#!/usr/bin/env python3
"""Seed demo tenant and sample data for local development."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

print("Crewspan seed script")
print("=" * 40)

TENANT_ID = str(uuid.uuid4())
USER_ID = str(uuid.uuid4())

demo_data = {
    "tenant": {
        "id": TENANT_ID,
        "slug": "demo-ops",
        "display_name": "Demo Field Services",
        "subscription_tier": "standard",
        "timezone": "America/Chicago",
    },
    "user": {
        "id": USER_ID,
        "email": "admin@demo-ops.local",
        "full_name": "Demo Administrator",
        "tenant_id": TENANT_ID,
    },
    "work_orders": [
        {"order_number": "WO-2024-001", "title": "HVAC Preventive Maintenance", "status": "in_progress", "priority": "normal"},
        {"order_number": "WO-2024-002", "title": "Emergency Plumbing Repair", "status": "submitted", "priority": "critical"},
        {"order_number": "WO-2024-003", "title": "Electrical Panel Inspection", "status": "draft", "priority": "high"},
    ],
}

print(f"Tenant ID:  {TENANT_ID}")
print(f"User ID:    {USER_ID}")
print(f"Login:      admin@demo-ops.local / demo1234")
print(f"Work orders: {len(demo_data['work_orders'])} sample records defined")
print()
print("Note: Run against live database with SQLAlchemy session in production.")
print("Seed complete (dry-run output above).")
'''


def _healthcheck_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

API_URL="${CREWSPAN_API_URL:-http://localhost:8000}"
WEB_URL="${CREWSPAN_WEB_URL:-http://localhost:3000}"

echo "Checking Crewspan services..."
echo

check() {
  local name="$1" url="$2"
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "  ✓ $name ($url)"
  else
    echo "  ✗ $name ($url) — FAILED"
    return 1
  fi
}

fail=0
check "API health" "$API_URL/health" || fail=1
check "API ready"  "$API_URL/ready"  || fail=1
check "Web UI"     "$WEB_URL/"       || fail=1

if command -v pg_isready > /dev/null 2>&1; then
  pg_isready -h localhost -p 5432 > /dev/null 2>&1 && echo "  ✓ PostgreSQL" || { echo "  ✗ PostgreSQL"; fail=1; }
fi

if command -v redis-cli > /dev/null 2>&1; then
  redis-cli ping > /dev/null 2>&1 && echo "  ✓ Redis" || { echo "  ✗ Redis"; fail=1; }
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "All checks passed."
else
  echo "Some checks failed."
  exit 1
fi
"""


def _common_package() -> dict[str, str]:
    return {
        "pyproject.toml": """[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "crewspan-common"
version = "0.1.0"
description = "Shared utilities for Crewspan services"
requires-python = ">=3.11"
dependencies = [
    "structlog>=24.1.0",
]

[tool.setuptools.packages.find]
where = ["src"]
""",
        "src/crewspan_common/__init__.py": '"""Crewspan shared utilities."""\n\n__version__ = "0.1.0"\n',
        "src/crewspan_common/errors.py": '''"""Shared error types for Crewspan services."""

from __future__ import annotations


class CrewspanError(Exception):
    """Base exception for Crewspan platform errors."""

    def __init__(self, message: str, *, code: str = "crewspan_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(CrewspanError):
    """Raised when a requested resource does not exist."""

    def __init__(self, *, resource: str, identifier: str) -> None:
        self.resource = resource
        self.identifier = identifier
        super().__init__(
            message=f"{resource} '{identifier}' was not found",
            code="not_found",
        )


class ValidationError(CrewspanError):
    """Raised when input fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class TenantIsolationError(CrewspanError):
    """Raised when a cross-tenant access is attempted."""

    def __init__(self, *, tenant_id: str, resource: str) -> None:
        super().__init__(
            message=f"Tenant {tenant_id} cannot access {resource}",
            code="tenant_isolation_violation",
        )
''',
        "src/crewspan_common/logging.py": '''"""Structured logging helpers."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(*, level: str = "INFO", json_output: bool = True) -> None:
    """Configure structlog for Crewspan services."""
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=getattr(logging, level.upper(), logging.INFO))
    processors: list[structlog.types.Processor] = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper(), logging.INFO)),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
''',
    }


def _sdk_package() -> dict[str, str]:
    return {
        "pyproject.toml": """[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "crewspan-sdk"
version = "0.1.0"
description = "Python client for the Crewspan API"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.6.0",
]

[tool.setuptools.packages.find]
where = ["src"]
""",
        "src/crewspan_sdk/__init__.py": '"""Crewspan Python SDK."""\n\nfrom crewspan_sdk.client import CrewspanClient, CrewspanAPIError\n\n__all__ = ["CrewspanClient", "CrewspanAPIError"]\n',
        "src/crewspan_sdk/client.py": '''"""Minimal Crewspan API client."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx


class CrewspanAPIError(Exception):
    def __init__(self, message: str, *, status_code: int) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CrewspanClient:
    """HTTP client for Crewspan REST API."""

    def __init__(
        self,
        base_url: str,
        tenant_id: str,
        *,
        token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"X-Tenant-Id": self.tenant_id, "Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            response = client.request(method, path, headers=self._headers(), **kwargs)
            if response.status_code >= 400:
                raise CrewspanAPIError(response.text, status_code=response.status_code)
            if response.status_code == 204:
                return None
            return response.json()

    def health(self) -> dict[str, str]:
        return self._request("GET", "/health")

    def list_work_orders(self, *, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/work-orders?page={page}&page_size={page_size}")

    def get_work_order(self, work_order_id: str | UUID) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/work-orders/{work_order_id}")

    def create_work_order(self, data: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/v1/work-orders", json=data)

    def list_technicians(self, *, page: int = 1) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/technicians?page={page}")

    def list_customers(self, *, page: int = 1) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/customers?page={page}")
''',
    }


def generate_infra_tree(root: Path) -> dict[str, int]:
    """Write infrastructure files, scripts, and shared packages under *root*."""
    stats: dict[str, int] = {}

    def record(rel: str, content: str) -> None:
        stats[rel] = _write(root / rel, content)

    record("docker-compose.yml", _docker_compose())
    record(".github/workflows/ci.yml", _ci_yml())
    record(".github/workflows/release.yml", _release_yml())
    record(".env.example", _env_example())
    record("Makefile", _makefile())
    record(".gitignore", _gitignore())
    record(".dockerignore", _dockerignore())
    record(".pre-commit-config.yaml", _precommit_config())

    record("scripts/migrate.sh", _migrate_script())
    record("scripts/seed.py", _seed_script())
    record("scripts/healthcheck.sh", _healthcheck_script())

    for rel, content in _common_package().items():
        record(f"packages/common/{rel}", content)

    for rel, content in _sdk_package().items():
        record(f"packages/sdk/{rel}", content)

    return stats


def print_generation_summary(stats: dict[str, int]) -> None:
    total_lines = sum(stats.values())
    print(f"Generated {len(stats)} infrastructure files, ~{total_lines:,} lines")
    for rel, lines in sorted(stats.items()):
        print(f"  {rel}: {lines} lines")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    print_generation_summary(generate_infra_tree(repo_root))
