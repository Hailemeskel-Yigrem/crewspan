# ADR-002: UUID Primary Keys

**Status:** Accepted
**Date:** 2023-11-20

## Context

Sequential integer IDs leak information about record counts and complicate multi-region replication.

## Decision

Use UUID v4 for all primary keys and foreign keys.

## Consequences

Positive: No ID enumeration, safe for distributed systems. Negative: Larger index size, non-sequential inserts.
