# ADR-003: Tenant ID Header Scoping

**Status:** Accepted
**Date:** 2024-01-10

## Context

Multi-tenant SaaS requires strict data isolation without separate databases per tenant.

## Decision

Require `X-Tenant-Id` header on all authenticated requests. Embed tenant_id in JWT. Filter all repository queries by tenant_id.

## Consequences

Positive: Strong isolation, simple schema. Negative: Header must be present on every request; misconfiguration risks cross-tenant access.
