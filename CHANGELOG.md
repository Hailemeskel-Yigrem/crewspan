# Changelog

All notable changes to Crewspan are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- Initial Alembic revision imported the SQLAlchemy types it referenced, so
  `make migrate` no longer fails with `NameError` before creating any table.
- Domain routers import the request body schemas they annotate; `/docs` and
  `/openapi.json` return 200 instead of 500 and the spec covers 174 paths.
- Domain validation errors interpolate the offending value instead of printing
  the literal `{entity.status}`.
- `WorkOrderTaskService.complete` no longer references an undefined `notes`.
- Web API client modules parse: comma-separated methods, TypeScript type names,
  real template literals for path parameters, and snake_case request bodies.
- Pages read the snake_case fields the API returns, so detail and list views no
  longer render `undefined`.
- `ToastProvider` renders the toasts it collects.

### Changed
- `npm run build`, `tsc --noEmit`, and both test suites pass from a fresh clone.
- CI installs from committed lockfiles and gates lint, typecheck, coverage, and
  a dependency audit.

### Removed
- One-time codegen and history-bootstrap tooling under `tools/`; `apps/` is the
  source of truth.

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
## Unreleased
- Platform: Pydantic v2, SQLAlchemy 2.0, React 18 adoption
