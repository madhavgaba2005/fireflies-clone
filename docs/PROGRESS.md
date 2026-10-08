# Progress Log

One entry per milestone: what was built, how it was verified, what's left. Newest last.

| Milestone | Branch | Status |
|-----------|--------|--------|
| Phase 0–1 Requirements & architecture | `docs/1-requirements-analysis` | ✅ merged |
| Phase 2 Scaffolding | `chore/2-project-scaffolding` | ✅ merged |
| A Database + seed | `feature/3-database-schema` | ✅ merged |
| B Meeting API | `feature/4-meeting-api` | ✅ merged |
| C Kafka + AI service | `feature/6-kafka-events` | ✅ merged |

---

## A — Database schema + seed data (#3, #8)

**Built**
- SQLAlchemy models for all domain tables plus `outbox_events` / `processed_events`
  (`backend/meeting-service/app/models/`), with CHECK / UNIQUE / FK constraints and explicit `ON DELETE` rules.
- `UTCDateTime` column type: stores UTC, returns aware datetimes, rejects naive ones.
- Alembic initial migration, applied automatically on startup (`RUN_MIGRATIONS_ON_STARTUP`).
- Transcript parser for txt / WebVTT / JSON with line-numbered errors.
- Seed: 7 meetings, 11 recurring people, 183 segments, 34 chapters, 35 action items (`python -m app.seed [--reset]`).

**Verified**
- 82 backend tests pass (schema constraints incl. cascades, RESTRICT, SET NULL, NOCASE uniqueness, CHECKs;
  migration ≡ models; downgrade/upgrade; parser edge cases; seed completeness/idempotency).
- Real run: fresh file → migrate → seed → `PRAGMA integrity_check = ok`, `foreign_key_check` empty; second run skips; `--reset` reseeds.

**Known gaps:** none for this milestone.

## B — Meeting API (#4, #5, #14 backend)

**Built**
- Repositories (`meetings`, `action_items`, `participants`, `outbox`): escaped `LIKE` title search, any-of participant
  filter, inclusive UTC date range, keyword tag filter, both sort orders, pagination; page loads in 3 queries + 1
  grouped count query.
- Services: create from form / pasted / uploaded transcript in one transaction with the `meeting.created` outbox row;
  update with replace semantics and the 409 "speaker can't be removed" rule; delete; regenerate (`summary.requested`);
  talk-time stats; action items with assignee validation and "user edit ⇒ manual" rule.
- 14 REST endpoints with documented error responses; sample transcripts for each format.

**Verified** — 144 backend tests pass (every endpoint, filter combination, validation rule and error code; outbox side
effects; persistence via a fresh session). ruff + strict mypy clean.

**Decision:** uploads are sent as JSON text with `transcript_format` instead of multipart (documented in API.md).

## C — Kafka pipeline + AI Processing Service (#6, #7)

**Built**
- Typed payload contract (pinned in both services), outbox relay, Kafka result consumer, idempotent `SummaryService`.
- AI service: deterministic `MockSummaryProvider`, `MeetingProcessor` with retries, Kafka consume→process→produce
  loop, token-protected HTTP fallback endpoint.
- Lifespan wiring per `PROCESSING_MODE`; compose healthchecks; `SEED_ON_STARTUP` in compose.

**Verified**
- 171 meeting-service tests (97 % coverage) and 39 AI-service tests (99 %).
- **Real Kafka:** `pytest -m kafka` with the broker and the AI service container — API → outbox → Kafka → AI → Kafka →
  consumer → SQLite, `completed` in ~5 s.
- **Full compose stack:** auto-seeded 7 meetings; meeting created via `curl` completed in ~1 s with correctly assigned
  action items; data survived `docker compose restart meeting-service`.

**Bugs found by tests and fixed:** summary silently not saved (SQLAlchemy 2.x backref cascade) — SQLAlchemy warnings
are now test errors; keyword de-duplication kept the last spelling instead of the first.

**Decision:** no LLM provider ships (no key, no tests ⇒ it would be decorative); the extension point is documented in ADR-007.
