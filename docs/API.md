# API Contract — Meeting Service

> Status: **Implemented (Milestone B)** — `backend/meeting-service/app/routers/`. Live docs: `GET /docs` (Swagger UI),
> `GET /openapi.json`. Every endpoint below is exercised by `tests/integration/test_*_api.py`.
> Base path `/api`. JSON only. Datetimes are ISO-8601 **with a timezone** (stored and returned as UTC);
> transcript offsets are integer milliseconds.

## Conventions

**Error envelope** — every non-2xx response:
```json
{ "error": { "code": "meeting_not_found", "message": "Meeting 42 not found", "details": null } }
```

| Status | When | Example `code` |
|--------|------|----------------|
| 400 | Transcript can't be parsed (`details.line` points at the problem) | `transcript_invalid` |
| 404 | Resource doesn't exist (also unknown routes) | `meeting_not_found`, `action_item_not_found`, `summary_not_found`, `not_found` |
| 405 | Wrong method | `method_not_allowed` |
| 409 | Business-rule conflict | `participant_has_transcript_lines`, `no_transcript` |
| 422 | Invalid input — schema (`validation_error`, `details` = field errors) or rule | `validation_error`, `invalid_date_range`, `invalid_assignee`, `participant_not_found` |
| 500 | Unexpected — generic message; details only in server logs | `internal_error` |

No authentication (the PDF says to assume a default logged-in user). CORS allows only `CORS_ORIGINS`.

**Why transcripts are sent as JSON text, not multipart:** the browser reads the uploaded file and sends its text with
`transcript_format` (`txt` | `vtt` | `json`). One content type, one validation path, the same 300 000-character
limit for pasted and uploaded transcripts, and the parser is identical for both — the user experience is unchanged.

## Endpoints

| Method | Path | Purpose | Success |
|--------|------|---------|---------|
| GET | `/api/meetings` | List with search, filters, sort, pagination | 200 |
| POST | `/api/meetings` | Create (form, pasted or uploaded transcript) | 201 |
| GET | `/api/meetings/{id}` | Detail: metadata, participants, status, talk time | 200 |
| PATCH | `/api/meetings/{id}` | Edit title, date, participants | 200 |
| DELETE | `/api/meetings/{id}` | Delete meeting and everything it owns | 204 |
| GET | `/api/meetings/{id}/transcript` | Ordered segments with speaker | 200 |
| GET | `/api/meetings/{id}/summary` | Overview, chapters, keywords | 200 · 404 until generated |
| POST | `/api/meetings/{id}/summary/regenerate` | Queue a new AI summary | 202 |
| GET | `/api/meetings/{id}/action-items` | List items | 200 |
| POST | `/api/meetings/{id}/action-items` | Add item | 201 |
| PATCH | `/api/action-items/{id}` | Edit / complete / uncomplete | 200 |
| DELETE | `/api/action-items/{id}` | Delete item | 204 |
| GET | `/api/participants` | Everyone, with meeting counts (filters, pickers) | 200 |
| GET | `/health` · `/health/ready` | Liveness · readiness (database) | 200 · 503 |

**Resource design:** action items are nested only for list/create (they need the parent); an item's id is globally
unique, so edit/delete use `/api/action-items/{id}`. Transcript and summary are separate GETs because the library
and edit modal need only metadata, while a transcript can be hundreds of KB; the workspace fetches them in parallel.

AI service (internal, never called by the browser): `GET /health`; `POST /internal/process` only in
`PROCESSING_MODE=http`, protected by the shared `X-Internal-Token` header (see EVENT_DRIVEN_ARCHITECTURE.md).

---

### GET /api/meetings
| Param | Type | Validation | Meaning |
|-------|------|-----------|---------|
| `q` | string | ≤ 100 chars | Title contains, case-insensitive; `%` and `_` are matched literally |
| `participant_id` | int, repeatable | — | Meetings with **any** of these participants |
| `date_from`, `date_to` | `YYYY-MM-DD` | `date_from ≤ date_to` else 422 `invalid_date_range` | Inclusive whole days (UTC) |
| `keyword` | string | ≤ 64 chars | Meetings whose summary has this keyword (tag filter) |
| `sort` | `-meeting_date` (default) \| `meeting_date` | — | Newest / oldest first |
| `limit` | int | 1–100, default 50 | Page size |
| `offset` | int | ≥ 0 | Page start |

```json
200 {
  "items": [{
    "id": 1, "title": "Weekly Product Sync", "meeting_date": "2026-10-08T10:00:00Z",
    "duration_seconds": 278, "source": "seed", "processing_status": "completed",
    "participants": [{ "id": 2, "name": "Arjun Mehta", "email": "arjun.mehta@northwind.io" }],
    "keywords": ["Release 2.4", "Bulk import"],
    "action_item_count": 6, "open_action_item_count": 4
  }],
  "total": 7, "limit": 50, "offset": 0
}
```
The page is loaded with 3 queries regardless of size (page + participants + keywords via `selectinload`) plus one
grouped query for action-item counts — no N+1.

### POST /api/meetings
```json
{
  "title": "Design review",                         // required, 1–200 chars (trimmed)
  "meeting_date": "2026-10-07T14:00:00Z",           // required, must include a timezone
  "participants": [{ "name": "Arjun Mehta", "email": "arjun@acme.io" }, { "id": 3 }],  // ≤ 50; id OR name
  "duration_seconds": 1800,                          // optional; at least the transcript length
  "transcript_text": "[00:00] Arjun: Hi all…",       // optional, ≤ 300 000 chars
  "transcript_format": "txt",                        // txt | vtt | json (default txt)
  "source": "paste"                                  // form | paste | upload (default form)
}
```
Behaviour, in **one transaction**: parse the transcript → find-or-create participants by name (case-insensitive) →
every speaker becomes a participant → insert meeting + segments → if there is a transcript, set
`processing_status = "pending"` and write a `meeting.created` event to the outbox. The response never waits for AI.
→ `201` meeting detail · `400 transcript_invalid` · `422`.

**Transcript formats** (examples in `backend/meeting-service/samples/`):
* **txt / paste:** `[mm:ss] Speaker: text` (or `[h:mm:ss]`, brackets optional); a line without a timestamp continues
  the previous utterance; timestamps must not go backwards. A segment ends where the next begins.
* **vtt:** WebVTT cues; speaker from `<v Name>` or a `Name:` prefix; tags stripped.
* **json:** `[{ "speaker": "…", "start": 12.5, "end": 18.0, "text": "…" }]` (seconds; `end` optional) or `{ "segments": [...] }`.

### GET /api/meetings/{id}
`200` = list item fields + `processing_error`, `transcript_revision`, `media_url`, `created_at`, `updated_at`, and
`speaker_stats: [{ participant_id, name, talk_time_ms, percentage }]` (largest first). `404 meeting_not_found`.

`processing_status`: `not_requested | pending | processing | completed | failed`
(see [EVENT_DRIVEN_ARCHITECTURE.md §5](EVENT_DRIVEN_ARCHITECTURE.md#5-processing-status-state-machine-meeting-service)).

### PATCH /api/meetings/{id}
```json
{ "title": "New title", "meeting_date": "2026-10-07T14:00:00Z", "participants": [{ "id": 3 }, { "name": "New Person" }] }
```
All fields optional; `participants` is the complete desired list. Removing a participant who **speaks** in the
transcript → `409 participant_has_transcript_lines` (`details.participants` lists them). Removing a silent participant
unassigns their action items (an assignee must attend the meeting). → `200` detail · `404` · `409` · `422`.

### DELETE /api/meetings/{id}
`204` · `404`. Segments, summary (topics, keywords), action items and participant links are removed by
`ON DELETE CASCADE`; people stay in the workspace address book.

### GET /api/meetings/{id}/transcript
```json
200 { "meeting_id": 1, "revision": 1, "segments": [
  { "id": 1, "sequence": 0, "start_ms": 0, "end_ms": 13680,
    "speaker": { "id": 1, "name": "Priya Sharma" }, "text": "Morning everyone…" } ] }
```

### GET /api/meetings/{id}/summary
```json
200 { "meeting_id": 1, "overview": "…", "provider": "seed", "transcript_revision": 1, "generated_at": "…",
      "topics": [{ "sequence": 0, "title": "Release 2.4 status", "summary": "…", "start_ms": 14280 }],
      "keywords": ["Release 2.4", "Activation"] }
```
`404 summary_not_found` until the AI result arrives — the UI shows "Generating notes…" based on `processing_status`.

### POST /api/meetings/{id}/summary/regenerate
`202 { "meeting_id": 1, "processing_status": "pending" }` · `404` · `409 no_transcript`.
Writes a `summary.requested` event to the outbox.

### Action items
```json
POST /api/meetings/1/action-items
{ "title": "Send revised pricing deck", "description": null, "assignee_id": 2, "due_date": "2026-10-10" }
→ 201 { "id": 36, "meeting_id": 1, "title": "…", "description": null,
        "assignee": { "id": 2, "name": "Arjun Mehta", "email": "…" }, "due_date": "2026-10-10",
        "completed": false, "completed_at": null, "source": "manual", "start_ms": null,
        "created_at": "…", "updated_at": "…" }

PATCH /api/action-items/36   { "completed": true }                       → 200 (completed_at set by the server)
PATCH /api/action-items/36   { "title": "…", "assignee_id": null }       → 200 (null unassigns; omitted = unchanged)
DELETE /api/action-items/36                                              → 204
```
Validation: `title` 1–500, `description` ≤ 2000, `due_date` ISO date, `assignee_id` must attend the meeting
(`422 invalid_assignee`). **Rule:** any edit turns an AI-extracted item into `source: "manual"`; regenerating notes
replaces only AI items, so user work is never lost.

### GET /api/participants
`200 [{ "id": 1, "name": "Priya Sharma", "email": "priya.sharma@northwind.io", "meeting_count": 6 }]` (by name)

## Bonus endpoints
| Method | Path | Bonus |
|--------|------|-------|
| GET | `/api/search?q=` — titles + transcript text, with snippets and `start_ms` to deep-link | B3 (Milestone G) |
