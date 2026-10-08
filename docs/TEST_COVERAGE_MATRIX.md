# Test Coverage Matrix

Every MUST-have requirement maps to at least one automated test that **exists and passes** (✓). File references are
relative to each project: `ms/` = `backend/meeting-service/tests`, `ai/` = `backend/ai-service/tests`,
`fe/` = `frontend` (Vitest `lib/*.test.ts`, Playwright `tests/e2e/*.spec.ts`).

E2E tests run against the real stack (both FastAPI services + production frontend build), not mocks.

## Must-have requirements

| Req | Requirement | Unit | Integration (API / DB) | E2E (browser) |
|-----|-------------|------|------------------------|---------------|
| R1.1 | List with title, date, duration, participants | — | ✓ `ms/integration/test_meetings_api.py::test_list_returns_required_fields_newest_first` | ✓ `library.spec` "lists meetings with title, date, duration and participants" |
| R1.2 | Search by title | ✓ `fe/lib/format.test.ts` (URL round-trip) | ✓ `test_search_by_title_is_case_insensitive`, `test_search_treats_like_wildcards_literally` | ✓ "search by title narrows the list and survives a reload", "top-bar search…" |
| R1.3 | Filter by date | ✓ `format.test.ts` "turns presets into inclusive day ranges" | ✓ `test_filter_by_date_range_is_inclusive`, `test_inverted_date_range_is_rejected` | ✓ "filter by date range" |
| R1.4 | Filter by participant | — | ✓ `test_filter_by_participant_any_of`, `test_filters_combine` | ✓ "filter by participant" |
| R1.5 | Sort by recency | — | ✓ `test_sort_oldest_first` (+ default order) | ✓ "sort by recency toggles newest/oldest first" |
| R1.6 | Navbar with profile/settings placeholders | — | — | ✓ "navbar: profile and settings placeholders, coming-soon features" |
| R2.1 | Transcript with speakers + timestamps | — | ✓ `test_transcript_is_ordered_with_speaker_and_times` | ✓ `workspace.spec` "shows speaker-labelled, timestamped transcript and AI notes" |
| R2.2 | Player with seek bar | ✓ `fe/lib/playback.test.ts` (13 tests: play, pause, seek, clamp, rate, end, restart) | — | ✓ "moving the seek bar…", "keyboard: space plays and pauses" |
| R2.3 | Transcript line → seeks player | — | — | ✓ "clicking a transcript line seeks the player there and plays", "outline chapters … seek the player" |
| R2.4 | Player → active line highlighted + scrolled | ✓ `fe/lib/transcript.test.ts` (boundaries, gaps, before first, after end, binary ≡ linear) | — | ✓ "exact boundary: a line becomes active at its start ms…" (paused seek), "moving the seek bar highlights and scrolls to the matching line", "playback highlights the active line and keeps it in view" |
| R2.5 | Transcript search with highlights | ✓ `fe/lib/search.test.ts` (case, regex chars, overlaps, wrap-around) | — | ✓ "search within the transcript highlights matches and navigates", "search with no matches says so" |
| R3.1 | AI summary | ✓ `ai/unit/test_mock_provider.py` | ✓ `test_summary_has_overview_topics_and_keywords`, `ms/integration/test_summary_results.py` | ✓ workspace overview; crud "create by pasting… notes are generated asynchronously" |
| R3.2 | Action items extracted | ✓ `test_action_items_detect_commitments_requests_and_deadlines`, `…skip_vague_statements` | ✓ `test_assignee_is_kept_only_if_they_attend` | ✓ crud (AI item appears), `action-items.spec` "seeded AI action items are grouped by assignee" |
| R3.3 | Topics / outline / chapters | ✓ `test_chapters_start_at_their_first_segment…` | ✓ summary topics ordered with `start_ms` | ✓ outline shown; chapter click seeks |
| R3.4 | Seeded / mocked / generated summaries | ✓ processor retries & failures (`ai/unit/test_processor.py`) | ✓ `ms/integration/test_outbox_pipeline.py`; **real Kafka** `ms/kafka/test_pipeline_kafka.py` | ✓ crud: "Notes ready" appears without reload |
| R4.1 | Create by upload | ✓ parser txt/vtt/json + sample files | ✓ `test_create_from_uploaded_vtt_and_json` | ✓ "create by uploading a WebVTT file" |
| R4.2 | Create by paste | ✓ parser | ✓ `test_create_with_pasted_transcript_queues_processing` | ✓ "create by pasting a transcript…" |
| R4.3 | Create via form | — | ✓ `test_create_via_form_without_transcript` | ✓ "create via the manual form, without a transcript" |
| R4.4 | Edit title, participants | — | ✓ `test_update_title_date_and_participants_persists`, `test_removing_a_speaker_is_a_conflict` | ✓ "edit title and participants; changes persist after reload" |
| R4.5 | Delete meeting | — | ✓ `test_delete_removes_meeting_and_children`, `test_schema.py` cascade | ✓ "delete a meeting from the library…", "delete from the workspace…" |
| R4.6–R4.8 | Add / edit / complete action items | — | ✓ `ms/integration/test_action_items_api.py` (10 tests, 14 cases) | ✓ `action-items.spec` "add, edit, complete, uncomplete and delete — all persisted" |
| R4.9 | Everything persists | — | ✓ `test_changes_persist_for_a_new_session`; Docker restart check (PROGRESS.md, Milestone C) | ✓ reloads in crud and action-items specs |
| R5.1–R5.2 | Fireflies layout, transcript + summary panels | — | — | ✓ workspace spec incl. "notes or transcript can be expanded to full width and restored"; two visual QA passes ([UI_FIDELITY_AUDIT.md](UI_FIDELITY_AUDIT.md)) |
| R5.3 | Forms, modals, search, filters | — | — | ✓ create/edit/delete dialogs, filters, transcript search |
| R5.4 | Toasts | — | — | ✓ "Meeting created", "Meeting updated", "Meeting deleted", "Action item added/deleted", error toasts |
| R5.5 | Settings placeholders | — | — | ✓ navbar spec (profile + integrations tabs); `dark-mode.spec` Appearance tab |
| M1–M5 | Coming-soon placeholders | — | — | ✓ navbar spec (Analytics, Add to live meeting) |

## Edge cases

| Edge case | Covered by |
|-----------|-----------|
| Empty library / no filter matches | ✓ `test_empty_library`; E2E "no matches shows an empty state" |
| Meeting not found | ✓ `test_missing_meeting_is_404_everywhere`; E2E "unknown meeting shows a not-found state" |
| Empty transcript (form-created meeting) | ✓ `test_create_via_form_without_transcript`; E2E manual-form test ("No transcript") |
| Transcript search: no matches / many matches / regex characters / case | ✓ `search.test.ts`; E2E search specs |
| Timestamp exactly on a boundary, in a gap, before first, after end | ✓ `transcript.test.ts` (9 parametrized cases) |
| Duplicate action-item submission | ✓ submit button disabled while saving (`ActionItemEditor`); create guarded by `saving` |
| Delete failure → error toast, item kept | ✓ E2E "failed delete shows an error toast and keeps the meeting" |
| API unavailable → error state + retry | ✓ E2E "API unavailable: the library shows an error with a working retry" |
| Failed optimistic toggle rolls back | ✓ E2E "failed action-item toggle rolls back the optimistic checkbox" |
| Summary processing failure → reason + retry | ✓ `test_failure_marks_meeting_failed_with_reason`, `test_retry_after_failure_succeeds`; E2E failure state |
| Duplicate Kafka event | ✓ `test_duplicate_delivery_is_applied_once`, consumer test with a duplicated message; **real broker** `ms/kafka/test_duplicates_kafka.py` |
| Stale result (older transcript revision) | ✓ `test_stale_result_for_an_older_revision_is_ignored` |
| Malformed transcript | ✓ parser tests (txt/vtt/json); `test_malformed_transcript_is_400_with_line_number`; E2E inline error |
| Malformed event on Kafka | ✓ `test_handle_message_outcomes`, AI `test_requests_are_processed…` (garbage skipped) |
| Missing participant data | ✓ `test_unknown_participant_id_is_422`, JSON parser "missing speaker uses placeholder" |
| Invalid payloads | ✓ `test_invalid_create_payloads_are_422` (9 cases), action-item `test_invalid_payloads` (5 cases) |
| Stale UI after mutation | ✓ cache invalidation per mutation (`hooks/queries.ts`); every E2E CRUD test reloads |
| Phone-width layout | ✓ E2E `responsive.spec` (no horizontal scroll, drawer, tabs) |
| Expanded panel keeps sync working | ✓ E2E "notes or transcript can be expanded…" (click-to-seek while expanded) |

## Bonus features

| Bonus | Unit | Integration | E2E |
|-------|------|-------------|-----|
| B3 Global search | — | ✓ `ms/integration/test_search_api.py` (12) | ✓ `global-search.spec` (2) |
| B4 Tags (AI keywords) | — | ✓ `test_filter_by_keyword_tag` | ✓ `library.spec` "keyword chips filter by tag" |
| B2 Export TXT / Markdown | ✓ `fe/lib/export.test.ts` (6) | — | ✓ `export.spec` (2, real downloaded files) |
| B6 Dark mode (System / Light / Dark) | ✓ `fe/lib/theme.test.ts` (4) | — | ✓ `dark-mode.spec` (3: menu toggle + reload, OS default, settings incl. live OS change) |
