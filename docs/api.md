# API Reference

Base URL: `/api/v1`

## Authentication

```http
POST /api/v1/auth/login
Content-Type: application/json

{"email": "user@example.com", "password": "...", "tenant_id": "uuid"}
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
{
  "data": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "pages": 3
}
```

## Domain Endpoints

| Resource | Operations | Description |
|----------|-----------|-------------|
| `tenants` | CRUD + 3 actions | Multi-tenant organization registry with subscription tier an… |
| `users` | CRUD + 3 actions | Platform user accounts scoped to tenants with authentication… |
| `roles` | CRUD + 3 actions | Role-based access control definitions with permission sets.… |
| `customers` | CRUD + 3 actions | Customer master records for field service accounts and billi… |
| `customer-sites` | CRUD + 2 actions | Physical service locations belonging to customers.… |
| `contacts` | CRUD + 2 actions | Customer contacts for scheduling and notification routing.… |
| `work-orders` | CRUD + 5 actions | Core work order lifecycle from intake through completion.… |
| `work-order-tasks` | CRUD + 3 actions | Checklist tasks attached to work orders.… |
| `technicians` | CRUD + 3 actions | Field technician profiles linked to user accounts.… |
| `technician-skills` | CRUD + 2 actions | Skill and certification assignments for technicians.… |
| `schedules` | CRUD + 3 actions | Calendar blocks for technician availability and appointments… |
| `dispatchs` | CRUD + 4 actions | Dispatch board assignments linking technicians to work order… |
| `inventory-items` | CRUD + 3 actions | Catalog of parts and consumables tracked in inventory.… |
| `inventory-locations` | CRUD + 2 actions | Warehouses, vans, and stock locations.… |
| `stock-movements` | CRUD + 2 actions | Inventory transactions: receipts, issues, transfers, adjustm… |
| `parts-requests` | CRUD + 3 actions | Parts requisitions linked to work orders.… |
| `invoices` | CRUD + 4 actions | Customer invoices generated from completed work.… |
| `invoice-line-items` | CRUD + 1 actions | Individual line items on customer invoices.… |
| `payments` | CRUD + 2 actions | Payment records applied to invoices.… |
| `sla-policies` | CRUD + 2 actions | Service level agreement policy definitions.… |
| `sla-breachs` | CRUD + 2 actions | Recorded SLA violations for reporting and escalation.… |
| `service-contracts` | CRUD + 3 actions | Recurring service agreements with customers.… |
| `equipments` | CRUD + 2 actions | Customer-owned equipment and assets under service.… |
| `notifications` | CRUD + 3 actions | Outbound notification delivery records.… |
| `webhooks` | CRUD + 3 actions | Tenant webhook subscriptions for outbound event delivery.… |
| `audit-logs` | CRUD + 1 actions | Immutable audit trail for compliance and forensics.… |

## Error Responses

```json
{
  "code": "not_found",
  "message": "WorkOrder abc-123 was not found",
  "resource": "work_order",
  "identifier": "abc-123"
}
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
POST /api/v1/work-orders/{id}/submit
POST /api/v1/work-orders/{id}/assign-technician
POST /api/v1/work-orders/{id}/complete
Content-Type: application/json

{"notes": "Replaced capacitor, system tested OK"}
```

Successful actions return `200` with the updated entity read model. Invalid state transitions return `422` with code `validation_error`. Conflicts (e.g., duplicate status) return `409`.

## Soft Delete & Restore

Tenant-scoped entities support soft delete by default:

```http
DELETE /api/v1/work-orders/{id}        → 204 No Content
POST   /api/v1/work-orders/{id}/restore → 200 WorkOrderRead
```

Deleted records are excluded from list/count unless `include_deleted=true` (admin-only, planned).

## Rate Limiting

Production deployments should enforce rate limits at the gateway. RelayOps includes a token-bucket helper (`app/logic/rate_limit.py`) suitable for edge adapters. Default config: 120 requests/minute per tenant (configurable via `RELAYOPS_RATE_LIMIT_PER_MINUTE`).

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
