# Changelog

All notable changes to RelayOps are documented here.

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
