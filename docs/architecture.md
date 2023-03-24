# Architecture

RelayOps is a multi-tenant SaaS platform for field service operations. The system follows a modular monolith architecture with clear domain boundaries.

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

RelayOps implements 26 bounded contexts:

### Tenant

Multi-tenant organization registry with subscription tier and feature flags.

Table: `tenants`

### User

Platform user accounts scoped to tenants with authentication metadata.

Table: `users`

### Role

Role-based access control definitions with permission sets.

Table: `roles`

### Customer

Customer master records for field service accounts and billing.

Table: `customers`

### CustomerSite

Physical service locations belonging to customers.

Table: `customer_sites`

### Contact

Customer contacts for scheduling and notification routing.

Table: `contacts`

### WorkOrder

Core work order lifecycle from intake through completion.

Table: `work_orders`

### WorkOrderTask

Checklist tasks attached to work orders.

Table: `work_order_tasks`

### Technician

Field technician profiles linked to user accounts.

Table: `technicians`

### TechnicianSkill

Skill and certification assignments for technicians.

Table: `technician_skills`

### Schedule

Calendar blocks for technician availability and appointments.

Table: `schedules`

### Dispatch

Dispatch board assignments linking technicians to work orders.

Table: `dispatches`

### InventoryItem

Catalog of parts and consumables tracked in inventory.

Table: `inventory_items`

### InventoryLocation

Warehouses, vans, and stock locations.

Table: `inventory_locations`

### StockMovement

Inventory transactions: receipts, issues, transfers, adjustments.

Table: `stock_movements`

### PartsRequest

Parts requisitions linked to work orders.

Table: `parts_requests`

### Invoice

Customer invoices generated from completed work.

Table: `invoices`

### InvoiceLineItem

Individual line items on customer invoices.

Table: `invoice_line_items`

### Payment

Payment records applied to invoices.

Table: `payments`

### SlaPolicy

Service level agreement policy definitions.

Table: `sla_policies`

### SlaBreach

Recorded SLA violations for reporting and escalation.

Table: `sla_breaches`

### ServiceContract

Recurring service agreements with customers.

Table: `service_contracts`

### Equipment

Customer-owned equipment and assets under service.

Table: `equipment`

### Notification

Outbound notification delivery records.

Table: `notifications`

### Webhook

Tenant webhook subscriptions for outbound event delivery.

Table: `webhooks`

### AuditLog

Immutable audit trail for compliance and forensics.

Table: `audit_logs`

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

Beyond per-domain modules, RelayOps ships shared application services:

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
- Domain transition events: `{domain}.status_transition`, `{domain}.service.*`
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
