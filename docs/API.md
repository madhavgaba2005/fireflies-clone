# API Contract — Meeting Service

> Status: **Proposed (Phase 0)**. Live, always-current docs: `GET /docs` (Swagger UI) and `/openapi.json`.
> Base path: `/api`. JSON everywhere except multipart upload. Times: ISO-8601 UTC; transcript offsets: integer ms.

## Conventions

**Error envelope** (every non-2xx):
```json
{ "error": { "code": "meeting_not_found", "message": "Meeting 42 not found", "details": null } }
```
| Status | When |
|--------|------|
| 400 | Malformed transcript file (unparseable VTT/JSON) — `details` includes line number |
| 404 | Resource does not exist |
| 409 | Business-rule conflict (e.g. removing a participant who has transcript lines) |
| 413 | Upload over `MAX_UPLOAD_BYTES` (default 2 MB) |
| 415 | Unsupported transcript file type |
| 422 | Validation error (Pydantic) — `details` lists fields |
| 500 | Unexpected — generic message, details logged server-side only |

No authentication (assignment: assume default logged-in user). CORS restricted to `FRONTEND_ORIGIN`.

## Endpoints

| Method | Path | Purpose | Success |
|--------|------|---------|---------|
| GET | `/api/meetings` | List + search + filter + sort + paginate | 200 |
| POST | `/api/meetings` | Create (form / paste: JSON; upload: multipart) | 201 |
| GET | `/api/meetings/{id}` | Meeting detail (metadata, participants, status) | 200 |
| PATCH | `/api/meetings/{id}` | Edit title, date, participants | 200 |
| DELETE | `/api/meetings/{id}` | Delete meeting + all children | 204 |
| GET | `/api/meetings/{id}/transcript` | Ordered segments with speaker | 200 |
| PUT | `/api/meetings/{id}/transcript` | Replace transcript (re-triggers AI) — *optional, if time allows* | 200 |
| GET | `/api/meetings/{id}/summary` | Overview, topics, keywords | 200 / 404 if none yet |
| POST | `/api/meetings/{id}/summary/regenerate` | Request new AI summary | 202 |
| GET | `/api/meetings/{id}/action-items` | List items | 200 |
| POST | `/api/meetings/{id}/action-items` | Create item | 201 |
| PATCH | `/api/action-items/{id}` | Edit / complete / uncomplete | 200 |
| DELETE | `/api/action-items/{id}` | Delete | 204 |
| GET | `/api/participants` | Options for participant filter + pickers | 200 |
| GET | `/health`, `/health/ready` | Liveness / readiness | 200 / 503 |

Why action items are **not** nested for PATCH/DELETE: an item's id is globally unique, so
`/api/action-items/{id}` is the canonical address; nesting is used only where the parent is needed (list/create).

Why transcript and summary are **separate GETs** from the meeting: the dashboard and edit modal need only
metadata; the transcript can be hundreds of KB. The detail page fetches the three in parallel.

---

### GET /api/meetings
Query params (all optional, combinable):

| Param | Type | Validation | Meaning |
|-------|------|-----------|---------|
| `q` | string | ≤ 100 chars | Case-insensitive title contains |
| `participant_id` | int (repeatable) | ≥ 1 | Meetings including **any** of these participants |
| `date_from`, `date_to` | date | `date_from ≤ date_to` else 422 | Inclusive on `meeting_date` |
| `sort` | enum | `-meeting_date` (default) \| `meeting_date` | Recency |
| `limit` | int | 1–100, default 50 | Page size |
| `offset` | int | ≥ 0 | Page start |

```json
200 {
  "items": [{
    "id": 7, "title": "Q3 Roadmap Planning", "meeting_date": "2026-09-30T10:00:00Z",
    "duration_seconds": 2710, "source": "seed", "processing_status": "completed",
    "participants": [{ "id": 1, "name": "Priya Sharma", "email": "priya@acme.io" }],
    "action_item_count": 5, "open_action_item_count": 3
  }],
  "total": 7, "limit": 50, "offset": 0
}
```

### POST /api/meetings
**JSON (form or paste):**
```json
{
  "title": "Design review",                 // required, 1–200
  "meeting_date": "2026-10-07T14:00:00Z",   // required
  "participants": [{ "name": "Arjun Mehta", "email": "arjun@acme.io" }],  // 0–50, name 1–100
  "duration_seconds": 1800,                  // optional; derived from transcript if present
  "transcript_text": "[00:00] Arjun: Hi all…" // optional, ≤ MAX_TRANSCRIPT_CHARS
}
```
**Multipart (upload):** fields `title`, `meeting_date`, optional `participants` (JSON string), `file` (.txt / .vtt / .json).

Behaviour: transcript is parsed → speakers resolved/created as participants → if transcript present,
`processing_status = pending` and a `meeting.created` event is queued (outbox).
Responses: `201` meeting detail · `400` unparseable transcript · `413` · `415` · `422`.

Supported transcript formats (documented with examples in `backend/meeting-service/samples/`):
* **.txt / paste:** `[mm:ss] Speaker: text` or `Speaker (mm:ss): text` per line; lines without a timestamp continue the previous utterance.
* **.vtt:** WebVTT cues; speaker from `<v Speaker>` voice tag or `Speaker:` prefix.
* **.json:** `[{ "speaker": "…", "start": 12.5, "end": 18.0, "text": "…" }]` (seconds).

### GET /api/meetings/{id}
`200` same shape as a list item plus `transcript_revision`, `processing_error`, `media_url`, `created_at`, `updated_at`, `speaker_stats` (talk time per participant). `404 meeting_not_found`.

### PATCH /api/meetings/{id}
```json
{ "title": "New title", "meeting_date": "…", "participants": [{ "id": 3 }, { "name": "New Person" }] }
```
All fields optional; `participants` is the full desired list (replace semantics). `200` updated meeting · `404` · `409 participant_has_transcript_lines` · `422`.

### DELETE /api/meetings/{id}
`204` · `404`. Cascades to participants links, transcript, summary, action items.

### GET /api/meetings/{id}/transcript
```json
200 { "meeting_id": 7, "revision": 1, "segments": [
  { "id": 1, "sequence": 0, "start_ms": 0, "end_ms": 6400,
    "speaker": { "id": 1, "name": "Priya Sharma" }, "text": "Morning everyone…" } ] }
```

### GET /api/meetings/{id}/summary
```json
200 { "meeting_id": 7, "overview": "…", "provider": "mock", "generated_at": "…",
      "topics": [{ "sequence": 0, "title": "Q3 priorities", "summary": "…", "start_ms": 0 }],
      "keywords": ["roadmap", "hiring", "SOC 2"] }
```
`404 summary_not_found` when not generated yet (frontend shows "Processing…" / "Not available" based on meeting status).

### POST /api/meetings/{id}/summary/regenerate
`202 { "processing_status": "pending" }` · `404` · `409 no_transcript`.

### Action items
```json
POST /api/meetings/7/action-items
{ "title": "Send revised pricing deck", "description": null, "assignee_id": 2, "due_date": "2026-10-10" }
→ 201 { "id": 31, "meeting_id": 7, "title": "…", "assignee": { "id": 2, "name": "…" },
        "due_date": "2026-10-10", "completed": false, "completed_at": null, "source": "manual",
        "start_ms": null, "created_at": "…", "updated_at": "…" }

PATCH /api/action-items/31   { "completed": true }        → 200 (completed_at set server-side)
PATCH /api/action-items/31   { "title": "…", "assignee_id": null } → 200
DELETE /api/action-items/31  → 204
```
Validation: `title` 1–500; `assignee_id` must be a participant of the meeting (`422` otherwise); `due_date` ISO date.

### GET /api/participants
`200 [{ "id": 1, "name": "Priya Sharma", "email": "priya@acme.io", "meeting_count": 4 }]`

## Bonus endpoints (only after must-haves)
| Method | Path | Bonus |
|--------|------|-------|
| GET | `/api/meetings/{id}/export?content=transcript\|summary&format=txt\|md&timestamps=true&speakers=true` | B2 |
| GET | `/api/search?q=` (titles + transcript text, snippets with `start_ms`) | B3 |
