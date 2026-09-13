# Crewspan

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
Crewspan/
├── apps/
│   ├── api/          FastAPI backend (26 domain modules)
│   ├── web/          Vite + React 18 frontend
│   └── worker/       Celery background jobs
├── packages/
│   ├── common/       Shared Python utilities
│   └── sdk/          Python API client
├── docs/             Architecture and operations guides
└── scripts/          Migration, seed, healthcheck scripts
```

## Core Domains

- **Tenant** — Multi-tenant organization registry with subscription tier and feature flags.
- **User** — Platform user accounts scoped to tenants with authentication metadata.
- **Role** — Role-based access control definitions with permission sets.
- **Customer** — Customer master records for field service accounts and billing.
- **CustomerSite** — Physical service locations belonging to customers.
- **Contact** — Customer contacts for scheduling and notification routing.
- **WorkOrder** — Core work order lifecycle from intake through completion.
- **WorkOrderTask** — Checklist tasks attached to work orders.
- … and 18 more (see [docs/architecture.md](docs/architecture.md))

## Development

```bash
make install       # Install from the committed lockfiles
make dev-api       # Run API with hot reload
make dev-web       # Run Vite dev server
make test          # pytest (api, worker, packages) + vitest
make lint          # Ruff + ESLint
make typecheck     # mypy + tsc --noEmit
make coverage      # Test suites with their coverage floors enforced
```

Dependencies are pinned in `apps/api/requirements.lock.txt`,
`apps/worker/requirements.lock.txt` and `apps/web/package-lock.json`; CI
installs from those same files.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow and
[CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT — see [LICENSE](LICENSE).
