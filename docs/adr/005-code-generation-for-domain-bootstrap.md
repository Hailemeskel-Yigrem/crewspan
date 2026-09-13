# ADR-005: Code Generation for Domain Bootstrap

**Status:** Superseded
**Date:** 2024-06-01
**Superseded:** 2026-09-13

## Context

28 domain modules with similar CRUD + action patterns would require excessive boilerplate if written manually.

## Decision

Define domain specifications in `tools/codegen/domains.py` and generate API, web, test, and infra scaffolds.

## Consequences

Positive: Consistency, rapid bootstrap, schema-driven. Negative: Generated code must be reviewed; custom logic added post-generation.

## Superseded

The generators were a one-time bootstrap and have been removed. `apps/` is now
the single source of truth: domain modules are edited directly and every change
lands as an ordinary commit with its test. Regenerating them would have
overwritten the hand-written fixes made since the bootstrap.
