# Trade-offs

| Decision | We gain | We give up | Mitigation / when to revisit |
|----------|---------|-----------|------------------------------|
| Two services instead of a monolith | A real async seam; AI work isolated, independently deployable | More moving parts than the PDF needs | Strictly two; in-memory bus keeps local dev & tests simple |
| Kafka instead of a background task | Durable, replayable, decoupled pipeline; demonstrates event-driven design | Operational weight (broker, deployment) | `EventBus` abstraction; Kafka only on the async path |
| Transactional outbox (polling relay) | No lost events when Kafka/process fails | ~1 s publish latency, an extra table | CDC (Debezium) in production |
| Event-carried transcript snapshot | Stateless AI service, no call-back coupling | Larger messages | Transcript size cap below Kafka's 1 MB default |
| Polling for summary status | Trivial, proxy-friendly | Extra requests while pending | Only polls while `pending`; SSE later |
| SQLite (mandated) | Zero-ops, single file | Single writer; no horizontal scale of Meeting Service | WAL + busy_timeout; Postgres path documented |
| Speaker as FK to participants | Normalized, renames propagate, joinable stats | Name-collision assumption on upload | Case-insensitive unique name; documented |
| Mock summary provider by default | Works with no API key, deterministic tests, free demo | Less "intelligent" summaries | `LLMSummaryProvider` behind the same interface |
| Client-side transcript search | Instant, no extra API | Doesn't scale to huge transcripts | Server FTS5 used for global search bonus |
| Duplicated event schemas per service | Independent deployability | Drift risk | Contract tests pin the shape in both services |
