# ADR-005: Kafka for asynchronous AI processing only

**Status:** Accepted (Phase 0)

## Context
Summary generation is slow and failure-prone (especially with a future LLM). We want request latency independent of it, durable retry, and a decoupled, replaceable worker. Demonstrating event-driven design is an explicit project goal (not a PDF requirement).

## Decision
Kafka (single-node KRaft) with topics `meeting.events` and `ai.events`, keyed by `meeting_id`. Transactional outbox on the producer side (ADR-008); idempotent, revision-checked consumer on the Meeting Service side. CRUD never goes through Kafka. Publishing goes through an `EventPublisher` interface (`KafkaEventPublisher`, `HttpEventPublisher` for the documented synchronous fallback, `InMemoryEventPublisher` for tests), selected by `PROCESSING_MODE`.

## Alternatives
- **FastAPI `BackgroundTasks`:** simplest, but in-process, lost on crash, no separate service.
- **Celery + Redis / RabbitMQ:** classic task queue and a fine fit, but adds Redis (explicitly out of scope) and is task-oriented rather than event-oriented.
- **Direct HTTP call Meeting → AI:** synchronous coupling; AI downtime breaks meeting creation.

## Trade-offs
+ Durable, replayable, ordered per meeting; services deploy independently.
− Heaviest piece of infrastructure in the project; free hosting may not run a broker, hence the `PROCESSING_MODE=http` fallback that reuses the same envelope, processor and idempotent apply path.

## Implementation notes (Milestone C)
Verified end-to-end against a real broker and the real AI service (`pytest -m kafka`, also a CI job). Topics are
auto-created by the broker in this single-node setup; production would create them explicitly with replication 3.

## Consequences
The UI must model eventual consistency (`processing_status` + polling). See EVENT_DRIVEN_ARCHITECTURE.md.
