# Trade-offs

No choice here is "best" in general — each is right for **this** assignment (≈ 24 h, single developer, SQLite
mandated, graded on functionality, Fireflies fidelity and explainability). Each entry says when we would choose
differently.

## Summary table

| Decision | We gain | We give up | Revisit when |
|----------|---------|-----------|--------------|
| SQLite (mandated) over PostgreSQL | Zero-ops single file; trivial seeding/reset; fast for reads | Single writer; one host; needs a persistent volume when deployed | Multiple Meeting Service instances or heavy concurrent writes |
| Kafka over a direct function call / background task | Durable, replayable, decoupled hand-off between independently deployable services | A broker to run, more failure modes, harder free hosting | Never needed at this scale — included deliberately and isolated behind `EventPublisher` |
| Two services over a monolith | A real async seam; AI isolated, replaceable, scalable | Two deployables + a broker; network contract to version | If the AI step were trivial and instant, a monolith is better |
| Async over synchronous summary generation | Fast `201` on create; AI failures don't fail the request | Eventual consistency → status field, polling, Retry | Never for LLM-backed summaries; sync is fine for a pure mock |
| Mock AI over a real LLM by default | Free, offline, deterministic tests, demo can't break | Visibly simpler summaries | Set `SUMMARY_PROVIDER=llm` + key — same interface |
| Client-side over server-side transcript search | Instant, no API, highlight logic co-located with rendering | Doesn't scale to very long transcripts / cross-meeting | Global search (bonus) uses server-side SQLite FTS5 |
| Repository layer over direct ORM queries in routes | Testable services, SQL in one place, consumers reuse services | More files, some pass-through methods | A 3-endpoint toy API wouldn't need it |
| Simulated playback over real audio | No TTS/media generation; sync logic fully real and testable | No sound | Real `<audio>` plugs into the same `PlaybackClock` interface |
| Free deployment over paid infrastructure | Zero cost | Cold starts, ephemeral disks, may not run Kafka → HTTP fallback | If a reliable free host with volume + broker isn't available |
| Transactional outbox over publish-after-commit | No lost events when Kafka or the process fails | ~1 s latency, extra table, a background loop | Production → CDC (Debezium) instead of polling |
| Event-carried transcript snapshot over AI calling back | Stateless AI service, no reverse dependency | Larger messages (capped below Kafka's 1 MB) | Very large transcripts → pass a reference + object storage |
| Polling over WebSockets/SSE for status | Trivial, works through every proxy/host | A few extra requests while pending | Many concurrent live updates |
| Duplicated event schemas per service over a shared package | Independent deployability | Drift risk | Contract tests pin both sides; schema registry in production |

## Details

### SQLite vs PostgreSQL
SQLite is required by the PDF. It is genuinely good here: the dataset is small, reads dominate, and a single file
makes seeding, resetting and CI trivial. Its limits are real: one writer at a time (mitigated with WAL +
`busy_timeout`), no network access (so only one service may own it — which matches our design), and on hosts
with ephemeral disks the data vanishes on restart. **Migration path:** portable SQLAlchemy types + Alembic; change
`DATABASE_URL`, swap `COLLATE NOCASE` for a `lower()` index, FTS5 for `tsvector`.

### Kafka vs direct function call
A direct call (or FastAPI `BackgroundTasks`) is simpler and would be the right answer for a mock summarizer.
Kafka earns its place only because we model summarization as a separate, independently deployable, slow and
failure-prone workload: requests are durable, survive restarts of either service, are ordered per meeting and can
be replayed. We do **not** use it for CRUD (users need read-your-own-writes). Cost: operational weight, which we
contain with the `EventPublisher` interface and an HTTP fallback.

### Microservices vs monolith
Two services, split on the one boundary with different runtime characteristics. Splitting further (by entity)
would cut through a single transactional boundary. A monolith would be perfectly acceptable for the PDF.

### Synchronous vs asynchronous processing
Asynchronous processing forces us to model state (`pending → processing → completed/failed`), idempotency and
stale results — all documented and tested. The benefit is a UI that never waits on AI and a pipeline that
tolerates AI outages.

### Mock AI vs real LLM
Mock by default: deterministic heuristics (chapters by time windows/speaker turns, keyword frequency, commitment-
phrase action items). Seeded meetings carry hand-written realistic summaries. An LLM provider is optional.

### Client-side vs server-side transcript search
Transcripts are already loaded for rendering, so searching in the browser is instant and keeps highlighting logic
next to the rendering. Server-side search is needed only across meetings (bonus).

### Repository layer vs direct ORM queries
Adds a file per aggregate but keeps routers free of SQL and lets the Kafka consumer and HTTP routes share one
service implementation.

### Simulated playback vs real audio
The PDF allows a placeholder. The simulated clock drives the exact same seek/active-segment/scroll logic a real
media element would; swapping in `<audio>` changes one class.

### Free deployment vs paid infrastructure
See [DEPLOYMENT.md](DEPLOYMENT.md). Free tiers commonly lack persistent disks and can't host a broker; we will
verify persistence on the chosen host before claiming it, and use the documented HTTP mode if needed.
