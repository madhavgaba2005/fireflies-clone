# ADR-008: Transactional outbox for publishing events

**Status:** Accepted (Phase 0)

## Context
Creating a meeting must both commit to SQLite and publish an event. Two separate systems cannot be updated atomically; naive "commit then publish" loses events on a crash or broker outage.

## Decision
Write an `outbox_events` row in the same transaction as the domain change. A relay loop publishes unpublished rows and marks them published (at-least-once). Consumers are idempotent (ADR-005).

## Alternatives
- **Publish inside the request after commit:** simple, but loses events on failure, and the request fails or hangs when Kafka is down.
- **Publish before commit:** may announce data that then rolls back.
- **CDC (Debezium):** production-grade, far too heavy for SQLite and this scope.

## Trade-offs
+ No lost events; meeting creation never depends on Kafka availability.
− ~1 s extra latency; one more table and a background loop.

## Consequences
The consuming side needs `processed_events` de-duplication because at-least-once delivery may duplicate.
