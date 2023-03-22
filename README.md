# RelayOps

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
RelayOps/
├── apps/
│   ├── api/          FastAPI backend (26 domain modules)
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
make dev-api       # Run API with hot reload
make dev-web       # Run Vite dev server
make test          # Run all test suites
make lint          # Ruff + ESLint
```

See [docs/contributing.md](docs/contributing.md) for full development workflow.

## License

Proprietary — All rights reserved.
