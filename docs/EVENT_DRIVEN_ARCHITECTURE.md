# Event-Driven Architecture

> Status: **Accepted (Phase 1)** — implemented in Phases 5–6.

## 1. Why Kafka here — and only here

Summary generation is **slow, failure-prone and replaceable** (today a mock, tomorrow an LLM call taking 5–30 s that
may rate-limit). Running it inside the request would make `POST /api/meetings` slow and fragile. Making it an event:

* the user gets `201` immediately; the summary arrives later,
* the AI service can be down, redeployed, scaled or swapped without the Meeting Service noticing,
* work is durable — a crash doesn't lose a pending summary.

**Why not Kafka for CRUD:** the user is waiting for the result and expects read-your-own-writes. Async CRUD would add
latency and eventual consistency to operations that a single SQLite transaction already does correctly.

**Honest framing:** at this scale a background task queue would suffice. Kafka is chosen to demonstrate a decoupled,
durable, replayable pipeline between two independently deployable services, and is hidden behind an
`EventPublisher` interface so tests run with an in-memory publisher and a constrained deployment can use the HTTP
fallback (§9) without changing anything else.

## 2. Topics

| Topic | Producer | Consumer (group) | Key | Events |
|-------|----------|------------------|-----|--------|
| `meeting.events` | Meeting Service (outbox relay) | AI Service (`ai-service`) | `meeting_id` | `meeting.created`, `transcript.updated`, `summary.requested` |
| `ai.events` | AI Service | Meeting Service (`meeting-service`) | `meeting_id` | `summary.generated`, `summary.failed` |

Two topics (rather than one shared `meeting.events`) so each service consumes only what it must act on and never
reads its own output. Keying by `meeting_id` puts all events for one meeting in one partition → **per-meeting ordering**.
Partitions: 3 (dev) — more than enough; a single broker in KRaft mode (no ZooKeeper).

## 3. Envelope (identical shape in both services, version-pinned by contract tests)

```json
{
  "event_id": "5f0c…uuid4",
  "event_type": "meeting.created",
  "version": 1,
  "occurred_at": "2026-10-08T12:00:00Z",
  "aggregate_id": "42",
  "payload": { }
}
```

### Payloads (v1)

`meeting.created` / `transcript.updated` / `summary.requested` → **event-carried state transfer**: the transcript
travels in the event, so the AI service is stateless and never calls back into the Meeting Service.
```json
{ "meeting_id": 42, "transcript_revision": 3, "title": "Q3 Roadmap Planning",
  "participants": [{ "id": 1, "name": "Priya Sharma" }],
  "segments": [{ "speaker_id": 1, "speaker": "Priya Sharma", "start_ms": 0, "end_ms": 6400, "text": "…" }] }
```
Size: transcripts are capped at `MAX_TRANSCRIPT_CHARS` (≈ 300 KB), below Kafka's default 1 MB message limit.

`summary.generated`
```json
{ "meeting_id": 42, "transcript_revision": 3, "provider": "mock",
  "overview": "…", "keywords": ["…"],
  "topics": [{ "title": "…", "summary": "…", "start_ms": 0 }],
  "action_items": [{ "title": "…", "assignee_speaker_id": 2, "start_ms": 81000 }] }
```
`summary.failed` → `{ "meeting_id": 42, "transcript_revision": 3, "reason": "…", "attempts": 3 }`

## 4. Delivery guarantees

### Producer side — transactional outbox (Meeting Service)
Writing to SQLite and to Kafka are two systems; doing both in a request risks "DB committed, event lost" (or the reverse).
So the request **only writes to SQLite**: the meeting rows and an `outbox_events` row commit in one transaction.
A relay loop (asyncio task started in the FastAPI lifespan) polls unpublished rows every ~1 s, produces them, then sets
`published_at`. If the broker is down, rows stay unpublished and are retried with exponential backoff (capped).
Result: **at-least-once** publishing, no lost events.

### Consumer side — idempotency
At-least-once means duplicates are possible. Both consumers are idempotent:
* **Meeting Service:** inside the same transaction that applies a result it inserts `event_id` into `processed_events`
  (PK). Already present → skip and commit offset. Additionally, a result whose `transcript_revision` is older than the
  meeting's current revision is discarded (stale), so out-of-order results are harmless.
* **AI Service:** stateless, so re-processing a duplicate just yields an equivalent result event, which the Meeting
  Service then de-duplicates via revision + upsert semantics (the summary row is unique per meeting).

Offsets are committed **after** successful handling (manual commit), never before.

### Retries & failure handling (AI Service)
1. Provider raises → retry up to `AI_MAX_RETRIES` (default 3) with backoff `1s, 2s, 4s`.
2. Still failing → publish `summary.failed`, commit offset (no poison-pill blocking the partition).
3. Meeting Service marks `processing_status = failed`, stores `processing_error`; UI offers **Retry** →
   `POST /summary/regenerate` → `summary.requested`.
4. Malformed event (fails envelope validation) → logged and skipped (would go to a DLQ topic in production).

## 5. Processing status state machine (Meeting Service)

```
not_requested ──create/upload with transcript──▶ pending          (request row committed to outbox)
pending ──relay hands event to Kafka / AI service──▶ processing
pending | processing ──summary.generated (current rev)──▶ completed
pending | processing ──summary.failed (current rev)──▶ failed
completed | failed ──regenerate / transcript.updated──▶ pending
```
| State | Meaning | UI |
|-------|---------|----|
| `not_requested` | No transcript yet (form-created meeting) | "Add a transcript to generate notes" |
| `pending` | Request durably queued in the outbox, not yet delivered | "✨ Generating notes…" |
| `processing` | Delivered to Kafka / AI service; waiting for result | "✨ Generating notes…" |
| `completed` | Summary persisted | Notes rendered, toast "Notes ready" |
| `failed` | `summary.failed` received (reason stored) | Error card + **Retry** |

`pending → processing` is set by the Meeting Service itself when the relay confirms the hand-off, so no extra
"started" event is needed. Results are accepted from both `pending` and `processing` because at-least-once delivery
means the result can race the relay's status update.

## 6. Eventual consistency in the UI
Detail page polls `GET /api/meetings/{id}` every 2 s **only while** status is `pending` or `processing`, shows a skeleton with
"Fireflies AI is generating notes…", and fires a toast when it flips to `completed`/`failed`.

## 7. Local & test setup
* `docker compose up` → single-node Kafka (KRaft) + both services + frontend.
* `PROCESSING_MODE=inline-test` → `InMemoryEventPublisher`; used by the unit/integration test suites so they need no broker.
* CI runs one end-to-end Kafka test with a Kafka service container: create meeting → assert summary persisted.

## 8. Publisher abstraction
```
EventPublisher (protocol: publish(envelope) -> None)
 ├─ KafkaEventPublisher     aiokafka producer, acks=all, key=meeting_id      PROCESSING_MODE=kafka
 ├─ HttpEventPublisher      POST envelope → AI /internal/process; applies    PROCESSING_MODE=http
 │                          the returned result envelope via the same handler
 └─ InMemoryEventPublisher  records envelopes; tests drive a fake processor  PROCESSING_MODE=inline-test
```
The outbox relay depends only on `EventPublisher`; the result handler (`SummaryService.apply_result`) depends only on
the envelope. Both are therefore identical in every mode.

## 9. HTTP fallback mode (free hosting without a broker)
Same envelope, same outbox, same `MeetingProcessor` in the AI service (called by the Kafka consumer **or** the HTTP
endpoint), same idempotent apply. Differences, stated honestly: no broker-level durability between services (the
outbox still guarantees the request is retried until the AI service answers), and no replay. The endpoint is
internal: protected by a shared `INTERNAL_API_TOKEN` header and not exposed to the browser.

## 10. What production would add
DLQ topic, schema registry (Avro/Protobuf) instead of duplicated Pydantic contracts, consumer lag alerts,
multiple brokers with replication factor 3, outbox via CDC (Debezium) instead of polling.
