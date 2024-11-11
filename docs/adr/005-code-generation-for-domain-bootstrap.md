# ADR-005: Code Generation for Domain Bootstrap

**Status:** Accepted
**Date:** 2024-06-01

## Context

28 domain modules with similar CRUD + action patterns would require excessive boilerplate if written manually.

## Decision

Define domain specifications in `tools/codegen/domains.py` and generate API, web, test, and infra scaffolds.

## Consequences

Positive: Consistency, rapid bootstrap, schema-driven. Negative: Generated code must be reviewed; custom logic added post-generation.
