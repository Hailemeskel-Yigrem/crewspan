# ADR-004: Celery for Background Jobs

**Status:** Accepted
**Date:** 2024-03-05

## Context

RelayOps needs async processing for notifications, webhooks, report exports, and scheduled tasks.

## Decision

Use Celery with Redis broker, separate queues per job category, Celery Beat for periodic tasks.

## Consequences

Positive: Battle-tested, queue isolation, retry support. Negative: Additional infrastructure (Redis), operational complexity.
