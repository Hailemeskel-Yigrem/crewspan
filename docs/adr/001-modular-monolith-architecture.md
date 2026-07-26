# ADR-001: Modular Monolith Architecture

**Status:** Accepted
**Date:** 2023-11-15

## Context

Fieldspan needs to ship quickly while maintaining clear domain boundaries for a team of 3-5 engineers.

## Decision

Adopt a modular monolith: single deployable with domain modules (`app/domains/*`) each containing models, schemas, repository, service, and router.

## Consequences

Positive: Simple deployment, shared transaction boundaries, easy refactoring. Negative: All modules scale together; may need extraction to services later.
<!-- history-note: evolutionary edit 69 -->
