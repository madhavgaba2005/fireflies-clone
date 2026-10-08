# Progress Log

One entry per milestone: what was built, how it was verified, what's left. Newest last.

| Milestone | Branch | Status |
|-----------|--------|--------|
| Phase 0–1 Requirements & architecture | `docs/1-requirements-analysis` | ✅ merged |
| Phase 2 Scaffolding | `chore/2-project-scaffolding` | ✅ merged |
| A Database + seed | `feature/3-database-schema` | ✅ merged |

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
