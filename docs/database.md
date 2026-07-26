# Database

Crewspan uses PostgreSQL 15+ with SQLAlchemy 2.0 async ORM and Alembic migrations.

## Schema Overview

| Table | Domain | Tenant-scoped | Soft delete |
|-------|--------|---------------|-------------|
| `tenants` | Tenant | No | Yes |
| `users` | User | Yes | Yes |
| `roles` | Role | Yes | Yes |
| `customers` | Customer | Yes | Yes |
| `customer_sites` | CustomerSite | Yes | Yes |
| `contacts` | Contact | Yes | Yes |
| `work_orders` | WorkOrder | Yes | Yes |
| `work_order_tasks` | WorkOrderTask | Yes | Yes |
| `technicians` | Technician | Yes | Yes |
| `technician_skills` | TechnicianSkill | Yes | Yes |
| `schedules` | Schedule | Yes | Yes |
| `dispatches` | Dispatch | Yes | Yes |
| `inventory_items` | InventoryItem | Yes | Yes |
| `inventory_locations` | InventoryLocation | Yes | Yes |
| `stock_movements` | StockMovement | Yes | Yes |
| `parts_requests` | PartsRequest | Yes | Yes |
| `invoices` | Invoice | Yes | Yes |
| `invoice_line_items` | InvoiceLineItem | Yes | Yes |
| `payments` | Payment | Yes | Yes |
| `sla_policies` | SlaPolicy | Yes | Yes |
| `sla_breaches` | SlaBreach | Yes | Yes |
| `service_contracts` | ServiceContract | Yes | Yes |
| `equipment` | Equipment | Yes | Yes |
| `notifications` | Notification | Yes | Yes |
| `webhooks` | Webhook | Yes | Yes |
| `audit_logs` | AuditLog | Yes | No |

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

Alembic revision chain lives in `apps/api/alembic/versions/`. Initial migration `001_initial` creates all 26 domain tables. Subsequent migrations must be backward-compatible for rolling deploys.
