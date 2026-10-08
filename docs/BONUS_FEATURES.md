# Bonus Features

Rule: no bonus work starts until every MUST row in [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md) is ✅.

| Priority | ID | Bonus | Implementation plan | Test | Status |
|----------|----|-------|---------------------|------|--------|
| 1 | B3 | Global search across all meetings | SQLite FTS5 virtual table over segment text (kept in sync on transcript write) + title; `GET /api/search`; top-bar results dropdown with snippet → deep link `/meetings/{id}?t=ms` | Integration (ranking, snippet); E2E deep link seeks | ⬜ |
| 2 | B2 | Export transcript / summary (TXT, Markdown) | `GET /api/meetings/{id}/export`; Fireflies-like Download modal with *timestamps* / *speaker labels* toggles | Unit (formatters); E2E download | ⬜ |
| 3 | B6 | Dark mode | CSS variable tokens already planned; toggle in user menu; persisted in localStorage; respects `prefers-color-scheme` | E2E toggle | ⬜ |
| 4 | B4 | Tags / topics + filtering | AI keywords → tags (`tags`, `meeting_tags`); tag filter on dashboard | Integration; E2E | ⬜ |
| 5 | B1 | Comments / highlights on segments | `segment_comments` table; hover action on transcript line | Integration; E2E | ⏸ |
| 6 | B5 | Ask-a-question chat | Keyword retrieval over segments → answer with cited timestamps; LLM if key configured | Unit | ⏸ |
