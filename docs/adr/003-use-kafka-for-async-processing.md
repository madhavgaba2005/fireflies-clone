# ADR-003: Kafka for asynchronous AI processing only

**Status:** Accepted (Phase 0)

## Context
Summary generation is slow and failure-prone (especially with a future LLM). We want request latency independent of it, durable retry, and a decoupled, replaceable worker. Demonstrating event-driven design is an explicit project goal (not a PDF requirement).

## Decision
Kafka (single-node KRaft) with topics `meeting.events` and `ai.events`, keyed by `meeting_id`. Transactional outbox on the producer side (ADR-007); idempotent, revision-checked consumer on the Meeting Service side. CRUD never goes through Kafka. An `EventBus` interface has Kafka and in-memory implementations.

## Alternatives
- **FastAPI `BackgroundTasks`:** simplest, but in-process, lost on crash, no separate service.
- **Celery + Redis / RabbitMQ:** classic task queue and a fine fit, but adds Redis (explicitly out of scope) and is task-oriented rather than event-oriented.
- **Direct HTTP call Meeting → AI:** synchronous coupling; AI downtime breaks meeting creation.

## Trade-offs
+ Durable, replayable, ordered per meeting; services deploy independently.
− Heaviest piece of infrastructure in the project; deployment must host a broker or use the documented in-memory fallback.

## Consequences
The UI must model eventual consistency (`processing_status` + polling). See EVENT_DRIVEN_ARCHITECTURE.md.
