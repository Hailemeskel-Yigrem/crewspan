"""Generate Fieldspan documentation tree."""

from __future__ import annotations

import textwrap
from pathlib import Path

from tools.codegen.domains import DOMAINS


def _write(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = textwrap.dedent(content).rstrip() + "\n"
    path.write_text(normalized, encoding="utf-8")
    return len(normalized.splitlines())


def _root_readme() -> str:
    domains_list = "\n".join(f"- **{d.title}** — {d.description}" for d in DOMAINS[:8])
    return f"""# Fieldspan

Multi-tenant field service operations platform for scheduling technicians, managing work orders, inventory, invoicing, and SLA compliance.

## Quick Start

```bash
cp .env.example .env
make up          # Start postgres, redis, api, web, worker
make migrate     # Run database migrations
make seed        # Load demo tenant data
```

- **Web UI:** http://localhost:3000
- **API docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## Repository Structure

```
Fieldspan/
├── apps/
│   ├── api/          FastAPI backend ({len(DOMAINS)} domain modules)
│   ├── web/          Vite + React 18 frontend
│   └── worker/       Celery background jobs
├── packages/
│   ├── common/       Shared Python utilities
│   └── sdk/          Python API client
├── docs/             Architecture and operations guides
├── scripts/          Migration, seed, healthcheck scripts
└── tools/codegen/    Code generators for bootstrapping
```

## Core Domains

{domains_list}
- … and {len(DOMAINS) - 8} more (see [docs/architecture.md](docs/architecture.md))

## Development

```bash
make dev-api       # Run API with hot reload
make dev-web       # Run Vite dev server
make test          # Run all test suites
make lint          # Ruff + ESLint
```

See [docs/contributing.md](docs/contributing.md) for full development workflow.

## License

Proprietary — All rights reserved.
"""


def _docs_readme() -> str:
    return """# Fieldspan Documentation

Welcome to the Fieldspan documentation hub.

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | System design, domain model, and data flow |
| [api.md](api.md) | REST API conventions and authentication |
| [deployment.md](deployment.md) | Production deployment with Docker |
| [database.md](database.md) | Schema, migrations, and multi-tenancy |
| [configuration.md](configuration.md) | Environment variables and settings |
| [troubleshooting.md](troubleshooting.md) | Common issues and diagnostics |
| [contributing.md](contributing.md) | Development setup and code standards |
| [security.md](security.md) | Security model and best practices |
| [changelog.md](changelog.md) | Release history |
| [adr/](adr/) | Architecture Decision Records |
"""


def _architecture_md() -> str:
    domain_sections = "\n\n".join(
        f"### {d.title}\n\n{d.description}\n\nTable: `{d.table_name or d.plural}`"
        for d in DOMAINS
    )
    return f"""# Architecture

Fieldspan is a multi-tenant SaaS platform for field service operations. The system follows a modular monolith architecture with clear domain boundaries.

## High-Level Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Web (React)│────▶│  API (FastAPI)│────▶│  PostgreSQL │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │ Redis/Celery│
                    │   Worker    │
                    └─────────────┘
```

## Multi-Tenancy

Every tenant-scoped resource carries a `tenant_id` UUID. The API enforces tenant isolation via:

1. `X-Tenant-Id` request header (required for authenticated routes)
2. Repository-layer filtering on all queries
3. JWT tokens embedding tenant context

## Domain Model

Fieldspan implements {len(DOMAINS)} bounded contexts:

{domain_sections}

## Request Flow

1. Client sends request with `Authorization: Bearer <token>` and `X-Tenant-Id`
2. Middleware binds request context (request ID, tenant ID) to structured logs
3. Router validates input via Pydantic schemas
4. Service layer enforces business rules
5. Repository layer executes tenant-scoped database queries
6. Response wrapped in standard envelope

## Background Processing

Celery workers handle:

- Notification delivery (email, SMS)
- Schedule reminders and conflict detection
- Invoice generation and payment reminders
- Webhook delivery with retry
- Report exports (CSV)

## Frontend Architecture

The React SPA uses:

- React Router for navigation
- Context-based auth state
- Typed API client modules per domain
- Component library with slate/teal industrial theme

## Layer Responsibilities

| Layer | Responsibility | Key modules |
|-------|----------------|-------------|
| Router | HTTP mapping, auth deps, response models | `app/domains/*/router.py` |
| Service | Business rules, validation, orchestration | `app/domains/*/service.py`, `app/services/*` |
| Repository | Tenant-scoped SQL, pagination, soft-delete | `app/domains/*/repository.py` |
| Model | SQLAlchemy 2.0 mapped tables | `app/domains/*/models.py` |
| Schema | Pydantic v2 I/O contracts with validators | `app/domains/*/schemas.py` |
| Worker | Durable async jobs (Celery) | `apps/worker/worker/jobs/*` |
| Web | React 18 SPA, typed API clients | `apps/web/src/*` |

## Cross-Cutting Services

Beyond per-domain modules, Fieldspan ships shared application services:

- **AuthService** — login, refresh tokens, password rotation with bcrypt
- **ReportingService** — dashboard KPIs, technician utilization aggregates
- **SearchService** — cross-entity ILIKE search with tenant caps
- **ExportService** — bounded CSV/JSON extracts for work orders

## Data Consistency

- Request-scoped SQLAlchemy async sessions commit on success, rollback on exception
- Domain methods flush state transitions before returning read models
- Idempotency keys protect webhook retries and payment capture (see `app/logic/idempotency.py`)
- Audit log entries are append-only; updates/deletes are rejected at service layer

## Caching & Performance

- Redis used for Celery broker, optional session cache (planned), rate-limit buckets
- Repository list endpoints support indexed filters and `order_by` whitelists
- Pagination defaults: 50 rows, max 200; exports capped at 10,000 rows

## Observability

Structured JSON logs via structlog include:

- `request_id`, `tenant_id`, `path`, `method`, `duration_ms`
- Domain transition events: `{{domain}}.status_transition`, `{{domain}}.service.*`
- Worker job lifecycle: `job_start`, `job_complete`

## Security Boundaries

```
Client ──HTTPS──▶ Load Balancer ──▶ API (JWT + tenant header)
                                      │
                                      ├──▶ PostgreSQL (tenant_id filter)
                                      └──▶ Redis (Celery broker)
Worker ◀── Redis ──▶ PostgreSQL
```

## Deployment Topology (Production)

Typical production layout:

1. **API replicas** (2+) behind ALB/nginx with health/readiness probes
2. **Worker replicas** per queue: `notifications`, `webhooks`, `reports`, `scheduling`
3. **Celery Beat** singleton for cron-style schedules
4. **Managed PostgreSQL** with PITR backups
5. **Managed Redis** cluster for broker + result backend
6. **Static web** served from nginx container or CDN

## Evolution Path

The modular monolith is designed for eventual extraction:

- High-churn domains (notifications, webhooks) can move to dedicated workers first
- Read-heavy reporting may split to a read replica or warehouse sync
- Domain boundaries map 1:1 to potential microservices if scale demands
"""


def _api_md() -> str:
    endpoints = "\n".join(
        f"| `{d.plural.replace('_', '-')}` | CRUD + {len(d.methods)} actions | {d.description[:60]}… |"
        for d in DOMAINS
    )
    return f"""# API Reference

Base URL: `/api/v1`

## Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{ '{"email": "user@example.com", "password": "...", "tenant_id": "uuid"}' }
```

Response includes `access_token` (JWT, HS256). Include in subsequent requests:

```http
Authorization: Bearer <token>
X-Tenant-Id: <tenant-uuid>
```

## Pagination

List endpoints accept `page` (default 1) and `page_size` (default 50, max 200).

Response envelope:

```json
{{
  "data": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "pages": 3
}}
```

## Domain Endpoints

| Resource | Operations | Description |
|----------|-----------|-------------|
{endpoints}

## Error Responses

```json
{{
  "code": "not_found",
  "message": "WorkOrder abc-123 was not found",
  "resource": "work_order",
  "identifier": "abc-123"
}}
```

HTTP status codes: 400 (validation), 401 (auth), 404 (not found), 409 (conflict), 422 (domain error).

## Cross-Cutting Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness probe |
| `/ready` | GET | Readiness probe |
| `/api/v1/auth/login` | POST | Issue JWT access + refresh tokens |
| `/api/v1/auth/refresh` | POST | Rotate access token |
| `/api/v1/search` | GET | Cross-entity search (`q`, `type`) |
| `/api/v1/reports/dashboard` | GET | Dashboard KPI snapshot |
| `/api/v1/exports/work-orders` | POST | Bounded CSV/JSON export |

## Filtering & Sorting

List endpoints accept domain-specific indexed filters plus:

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (1-based) |
| `page_size` | int | Rows per page (max 200) |
| `search` | string | ILIKE search on indexed text fields |
| `order_by` | string | Column name (whitelisted per domain) |
| `order_dir` | `asc`/`desc` | Sort direction |

Example:

```http
GET /api/v1/work-orders?status=in_progress&priority=high&order_by=scheduled_start&order_dir=asc
X-Tenant-Id: 550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer eyJ...
```

## Action Endpoints

Domain lifecycle actions use nested routes on entity IDs:

```http
POST /api/v1/work-orders/{{id}}/submit
POST /api/v1/work-orders/{{id}}/assign-technician
POST /api/v1/work-orders/{{id}}/complete
Content-Type: application/json

{ '{"notes": "Replaced capacitor, system tested OK"}' }
```

Successful actions return `200` with the updated entity read model. Invalid state transitions return `422` with code `validation_error`. Conflicts (e.g., duplicate status) return `409`.

## Soft Delete & Restore

Tenant-scoped entities support soft delete by default:

```http
DELETE /api/v1/work-orders/{{id}}        → 204 No Content
POST   /api/v1/work-orders/{{id}}/restore → 200 WorkOrderRead
```

Deleted records are excluded from list/count unless `include_deleted=true` (admin-only, planned).

## Rate Limiting

Production deployments should enforce rate limits at the gateway. Fieldspan includes a token-bucket helper (`app/logic/rate_limit.py`) suitable for edge adapters. Default config: 120 requests/minute per tenant (configurable via `FIELDSPAN_RATE_LIMIT_PER_MINUTE`).

## Idempotency

Mutating endpoints that may be retried (webhooks, payments) accept:

```http
Idempotency-Key: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

Duplicate keys within a 24-hour window return the original response without re-executing side effects.

## WebSocket & Realtime (Planned)

Dispatch board live updates will use WebSocket channels scoped by tenant. Until then, clients poll `/api/v1/dispatches` with short intervals.

## SDK & Client Libraries

- **Python SDK:** `packages/sdk` — synchronous httpx client with tenant header injection
- **Web client:** `apps/web/src/api/*` — fetch-based typed clients per domain
- **OpenAPI:** Available at `/docs` (Swagger UI) and `/openapi.json` when running the API
"""


def _deployment_md() -> str:
    return """# Deployment

## Docker Compose (Development)

```bash
docker compose up -d
```

Services: `api`, `web`, `worker`, `worker-beat`, `postgres`, `redis`

## Production Checklist

1. Set strong `FIELDSPAN_SECRET_KEY` (32+ random bytes)
2. Configure managed PostgreSQL with SSL
3. Use Redis Cluster or ElastiCache for Celery broker
4. Enable HTTPS termination at load balancer
5. Set `FIELDSPAN_CORS_ORIGINS` to production domain
6. Configure log aggregation (JSON structured logs)
7. Set up database backups and point-in-time recovery

## Kubernetes

Build images:

```bash
docker build -t fieldspan-api:latest apps/api
docker build -t fieldspan-web:latest apps/web
docker build -t fieldspan-worker:latest apps/worker
```

Deploy with secrets mounted for database URL, Redis URL, and JWT secret.

## Health Checks

- `GET /health` — liveness (always 200 if process running)
- `GET /ready` — readiness (checks DB connectivity in production)

## Environment Matrix

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| `FIELDSPAN_DEBUG` | true | false | false |
| `FIELDSPAN_LOG_JSON` | false | true | true |
| DB | Docker postgres | Managed PG | Managed PG + SSL |
| Redis | Docker redis | ElastiCache | ElastiCache cluster |
| HTTPS | Vite proxy | TLS at LB | TLS at LB |
| Replicas | 1 | 2 | 3+ |

## Docker Compose Services

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| postgres | postgres:15 | 5432 | Persistent volume |
| redis | redis:7 | 6379 | Broker + cache |
| api | fieldspan-api | 8000 | Uvicorn, hot reload in dev |
| web | fieldspan-web | 3000/80 | Vite dev or nginx prod |
| worker | fieldspan-worker | — | Celery consumer |
| worker-beat | fieldspan-worker | — | Celery beat scheduler |

## Kubernetes Manifests (Outline)

```yaml
# api-deployment.yaml (excerpt)
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: api
          image: fieldspan-api:0.4.0
          envFrom:
            - secretRef:
                name: fieldspan-secrets
          livenessProbe:
            httpGet: {{ path: /health, port: 8000 }}
          readinessProbe:
            httpGet: {{ path: /ready, port: 8000 }}
```

Secrets should include: `FIELDSPAN_DATABASE_URL`, `FIELDSPAN_REDIS_URL`, `FIELDSPAN_SECRET_KEY`.

## Database Migrations in CI/CD

```bash
# Run before rolling out new API version
kubectl exec deploy/fieldspan-api -- alembic upgrade head
```

Never run migrations concurrently from multiple pods — use a CI job or init container.

## Backup & Recovery

1. Enable automated daily snapshots on PostgreSQL
2. Test restore quarterly to staging
3. Redis is ephemeral (broker only) — no backup required
4. Export critical tenant data via `/api/v1/exports/*` before major migrations

## Scaling Guidelines

| Bottleneck | Symptom | Mitigation |
|------------|---------|------------|
| API CPU | High p95 latency | Horizontal pod autoscaling |
| DB connections | Pool exhaustion | PgBouncer, increase pool_size cautiously |
| Worker backlog | Queue depth growing | Add workers per queue |
| Web bundle size | Slow first load | CDN, code splitting (already via Vite) |

## Zero-Downtime Deploys

1. Build and push new images with semver tags
2. Run migrations (backward-compatible only)
3. Rolling update API/worker deployments
4. Invalidate CDN cache for web static assets
5. Monitor error rate and SLA breach metrics for 30 minutes
"""


def _database_md() -> str:
    tables = "\n".join(f"| `{d.table_name or d.plural}` | {d.title} | {'Yes' if d.tenant_scoped else 'No'} | {'Yes' if d.soft_delete else 'No'} |" for d in DOMAINS)
    return f"""# Database

Fieldspan uses PostgreSQL 15+ with SQLAlchemy 2.0 async ORM and Alembic migrations.

## Schema Overview

| Table | Domain | Tenant-scoped | Soft delete |
|-------|--------|---------------|-------------|
{tables}

## Migrations

```bash
cd apps/api
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Multi-Tenancy

All tenant-scoped tables include `tenant_id UUID NOT NULL` with an index. Queries MUST filter by tenant_id — enforced at the repository layer.

## Conventions

- Primary keys: UUID v4
- Timestamps: `created_at`, `updated_at` (timezone-aware)
- Soft deletes: `deleted_at` nullable timestamp
- JSON columns for flexible metadata (settings, addresses, line items)

## Indexing Strategy

Recommended indexes beyond primary keys:

- `(tenant_id, created_at DESC)` on high-volume list tables (work_orders, audit_log)
- `(tenant_id, status)` for dashboard aggregations
- Unique constraints scoped per tenant where applicable (order_number + tenant_id via application validation)
- Partial indexes on `deleted_at IS NULL` for large tables (production tuning)

## Connection Pooling

`app/db.py` configures:

```python
create_async_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20)
```

For production with many API replicas, place **PgBouncer** in transaction pooling mode between app and PostgreSQL.

## Migration Workflow

1. Modify SQLAlchemy models in `app/domains/*/models.py`
2. Generate revision: `alembic revision --autogenerate -m "add_field_x"`
3. Review generated SQL — autogenerate may miss renames
4. Apply: `alembic upgrade head`
5. Regenerate domain scaffolds if using codegen for greenfield domains

## Sample Queries

Tenant-scoped work order count by status:

```sql
SELECT status, COUNT(*)
FROM work_orders
WHERE tenant_id = $1 AND deleted_at IS NULL
GROUP BY status;
```

Technician utilization (simplified):

```sql
SELECT assigned_technician_id, COUNT(*)
FROM work_orders
WHERE tenant_id = $1
  AND status IN ('assigned', 'in_progress')
  AND deleted_at IS NULL
GROUP BY assigned_technician_id;
```

## Data Retention

| Data | Retention | Notes |
|------|-----------|-------|
| Audit log | 7 years | Compliance default |
| Soft-deleted entities | 90 days | Hard purge via worker job |
| Notification delivery logs | 30 days | Configurable per tenant |
| Webhook delivery attempts | 14 days | Debug/replay window |

## Replication & DR

- Production: multi-AZ PostgreSQL with automated failover
- Read replica optional for reporting queries (ReportingService may target replica URL)
- Point-in-time recovery window: minimum 7 days

## Schema Versioning

Alembic revision chain lives in `apps/api/alembic/versions/`. Initial migration `001_initial` creates all {len(DOMAINS)} domain tables. Subsequent migrations must be backward-compatible for rolling deploys.
"""


def _configuration_md() -> str:
    return """# Configuration

All settings use the `FIELDSPAN_` environment prefix.

## Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIELDSPAN_DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://fieldspan:fieldspan@localhost:5432/fieldspan` |
| `FIELDSPAN_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `FIELDSPAN_SECRET_KEY` | JWT signing key | `change-me-in-production` |

## Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FIELDSPAN_ENVIRONMENT` | `development` / `staging` / `production` | `development` |
| `FIELDSPAN_DEBUG` | Enable SQL echo | `false` |
| `FIELDSPAN_LOG_LEVEL` | Logging level | `INFO` |
| `FIELDSPAN_LOG_JSON` | JSON log format | `true` |
| `FIELDSPAN_CORS_ORIGINS` | Allowed CTA origins (JSON array) | `["http://localhost:3000"]` |
| `FIELDSPAN_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT TTL | `60` |
| `FIELDSPAN_DEFAULT_PAGE_SIZE` | API pagination default | `50` |

## Worker Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `FIELDSPAN_CELERY_BROKER_URL` | Celery broker | `redis://localhost:6379/1` |
| `FIELDSPAN_CELERY_RESULT_BACKEND` | Celery results | `redis://localhost:6379/2` |
| `FIELDSPAN_WEBHOOK_TIMEOUT_SECONDS` | Webhook HTTP timeout | `30` |
"""


def _troubleshooting_md() -> str:
    return """# Troubleshooting

## API won't start

**Symptom:** `RuntimeError: Database not initialized`

Ensure PostgreSQL is running and `FIELDSPAN_DATABASE_URL` is correct:

```bash
scripts/healthcheck.sh
```

## Migration failures

**Symptom:** `alembic.util.exc.CommandError: Can't locate revision`

Reset development database:

```bash
docker compose down -v
docker compose up -d postgres
make migrate
```

## Worker tasks not processing

1. Check Redis connectivity: `redis-cli ping`
2. Verify worker is consuming correct queues:
   ```bash
   celery -A worker.celery_app:celery_app inspect active_queues
   ```
3. Check worker logs for task failures

## Frontend API errors (CORS)

Ensure `FIELDSPAN_CORS_ORIGINS` includes your frontend URL. In development, Vite proxies `/api` to port 8000.

## Authentication failures

- Verify `X-Tenant-Id` header is sent with every authenticated request
- Check token expiry (`FIELDSPAN_ACCESS_TOKEN_EXPIRE_MINUTES`)
- Confirm `FIELDSPAN_SECRET_KEY` matches between token creation and validation

## High database connection count

Adjust pool settings in `app/db.py`: `pool_size=10`, `max_overflow=20`. Use PgBouncer in production.
"""


def _contributing_md() -> str:
    return """# Contributing

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+ and Redis 7+ (or use Docker)

## Setup

```bash
git clone <repo-url> Fieldspan && cd Fieldspan
cp .env.example .env
make install
make up
make migrate
make seed
```

## Code Generation

Regenerate domain modules from specifications:

```bash
python -m tools.codegen.generate_api
python -m tools.codegen.generate_web
python -m tools.codegen.generate_tests
python -m tools.codegen.generate_docs
python -m tools.codegen.generate_infra
```

Or bootstrap everything:

```python
from pathlib import Path
from tools.codegen import generate_api_tree, generate_web_tree, generate_tests_tree, generate_docs_tree, generate_infra_tree

root = Path(".")
generate_api_tree(root)
generate_web_tree(root)
generate_tests_tree(root)
generate_docs_tree(root)
generate_infra_tree(root)
```

## Code Standards

- **Python:** Ruff formatter/linter, type hints required, async SQLAlchemy
- **TypeScript:** Strict mode, functional React components, CSS variables for theming
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **Tests:** Required for new domain methods and UI components

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```
"""


def _changelog_md() -> str:
    return """# Changelog

All notable changes to Fieldspan are documented here.

## [0.4.0] — 2026-07-15

### Added
- SLA breach escalation workflow with multi-level notifications
- Technician utilization reporting in worker jobs
- Webhook HMAC signature verification and auto-disable on failures
- React DateRangePicker and ConfirmDialog components

### Changed
- Migrated pagination to cursor-based option for audit log queries
- Updated industrial theme CSS variables (slate/teal palette)

### Fixed
- Schedule conflict detection edge case for overlapping midnight boundaries
- Invoice recalculation rounding for tax line items

## [0.3.0] — 2025-11-20

### Added
- Service contract preventive maintenance work order generation
- Parts request approval and fulfillment workflow
- Inventory location low-stock alerts
- Multi-stage Docker build for web (nginx)

### Changed
- JWT tokens now embed tenant_id claim
- Repository layer enforces soft-delete filtering by default

## [0.2.0] — 2024-08-10

### Added
- Dispatch board with accept/decline/en-route lifecycle
- Customer site geocoding and service window validation
- Payment reconciliation and refund processing
- Celery beat schedules for reminders and invoice processing

### Fixed
- Tenant isolation leak in cross-tenant role listing
- Work order status transition validation

## [0.1.0] — 2023-12-01

### Added
- Initial release with 28 domain modules
- Multi-tenant authentication and RBAC
- Work order lifecycle management
- Technician scheduling and skills tracking
- Inventory catalog and stock movements
- Invoice generation with line items
- Notification delivery framework
- Audit log for compliance
- Code generation toolchain for bootstrapping
"""


def _security_md() -> str:
    return """# Security

## Authentication

- Passwords hashed with bcrypt (passlib)
- JWT access tokens (HS256) with configurable expiry
- Bearer token required for all `/api/v1/*` routes (except health)

## Authorization

- Role-based access control (RBAC) via permission keys on roles
- Tenant isolation enforced at repository layer
- System roles cannot be deleted

## Data Protection

- All database connections use TLS in production
- Soft deletes preserve audit history
- Immutable audit log (no update/delete operations)
- Webhook payloads signed with HMAC-SHA256

## Headers

| Header | Purpose |
|--------|---------|
| `Authorization` | Bearer JWT token |
| `X-Tenant-Id` | Tenant context for multi-tenancy |
| `X-Request-Id` | Request tracing (auto-generated if absent) |

## Recommendations

1. Rotate `FIELDSPAN_SECRET_KEY` periodically
2. Use short JWT expiry (≤ 60 minutes) with refresh token flow (planned)
3. Enable rate limiting at API gateway
4. Audit webhook secret rotation via `rotate_secret` endpoint
5. Never commit `.env` files or credentials
"""


def _adr(index: int, title: str, status: str, date: str, context: str, decision: str, consequences: str) -> str:
    slug = title.lower().replace(" ", "-").replace("/", "-")
    return f"""# ADR-{index:03d}: {title}

**Status:** {status}
**Date:** {date}

## Context

{context}

## Decision

{decision}

## Consequences

{consequences}
"""


def generate_docs_tree(root: Path) -> dict[str, int]:
    """Write documentation under *root*/docs and root README."""
    stats: dict[str, int] = {}

    def record(path: Path, rel: str, content: str) -> None:
        key = rel.replace("\\\\", "/")
        stats[key] = _write(path / rel if path != root else root / rel, content)

    record(root, "README.md", _root_readme())
    record(root / "docs", "README.md", _docs_readme())
    record(root / "docs", "architecture.md", _architecture_md())
    record(root / "docs", "api.md", _api_md())
    record(root / "docs", "deployment.md", _deployment_md())
    record(root / "docs", "database.md", _database_md())
    record(root / "docs", "configuration.md", _configuration_md())
    record(root / "docs", "troubleshooting.md", _troubleshooting_md())
    record(root / "docs", "contributing.md", _contributing_md())
    record(root / "docs", "changelog.md", _changelog_md())
    record(root / "docs", "security.md", _security_md())

    adrs = [
        (1, "Modular Monolith Architecture", "Accepted", "2023-11-15",
         "Fieldspan needs to ship quickly while maintaining clear domain boundaries for a team of 3-5 engineers.",
         "Adopt a modular monolith: single deployable with domain modules (`app/domains/*`) each containing models, schemas, repository, service, and router.",
         "Positive: Simple deployment, shared transaction boundaries, easy refactoring. Negative: All modules scale together; may need extraction to services later."),
        (2, "UUID Primary Keys", "Accepted", "2023-11-20",
         "Sequential integer IDs leak information about record counts and complicate multi-region replication.",
         "Use UUID v4 for all primary keys and foreign keys.",
         "Positive: No ID enumeration, safe for distributed systems. Negative: Larger index size, non-sequential inserts."),
        (3, "Tenant ID Header Scoping", "Accepted", "2024-01-10",
         "Multi-tenant SaaS requires strict data isolation without separate databases per tenant.",
         "Require `X-Tenant-Id` header on all authenticated requests. Embed tenant_id in JWT. Filter all repository queries by tenant_id.",
         "Positive: Strong isolation, simple schema. Negative: Header must be present on every request; misconfiguration risks cross-tenant access."),
        (4, "Celery for Background Jobs", "Accepted", "2024-03-05",
         "Fieldspan needs async processing for notifications, webhooks, report exports, and scheduled tasks.",
         "Use Celery with Redis broker, separate queues per job category, Celery Beat for periodic tasks.",
         "Positive: Battle-tested, queue isolation, retry support. Negative: Additional infrastructure (Redis), operational complexity."),
        (5, "Code Generation for Domain Bootstrap", "Accepted", "2024-06-01",
         "28 domain modules with similar CRUD + action patterns would require excessive boilerplate if written manually.",
         "Define domain specifications in `tools/codegen/domains.py` and generate API, web, test, and infra scaffolds.",
         "Positive: Consistency, rapid bootstrap, schema-driven. Negative: Generated code must be reviewed; custom logic added post-generation."),
    ]

    for idx, title, status, date, ctx, dec, cons in adrs:
        slug = title.lower().replace(" ", "-").replace("/", "-")
        record(root / "docs" / "adr", f"{idx:03d}-{slug}.md", _adr(idx, title, status, date, ctx, dec, cons))

    return stats


def print_generation_summary(stats: dict[str, int]) -> None:
    total_lines = sum(stats.values())
    print(f"Generated {len(stats)} documentation files, ~{total_lines:,} lines")
    for rel, lines in sorted(stats.items()):
        print(f"  {rel}: {lines} lines")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[2]
    print_generation_summary(generate_docs_tree(repo_root))
