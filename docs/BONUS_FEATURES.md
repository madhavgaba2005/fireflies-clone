# Bonus Features

Rule: no bonus work starts until every MUST row in [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md) is ✅.

| Priority | ID | Bonus | Implementation plan | Test | Status |
|----------|----|-------|---------------------|------|--------|
| 1 | B3 | Global search across all meetings | `GET /api/search` (escaped LIKE over titles + transcript lines, grouped per meeting, snippets); top-bar combobox dropdown with highlighted snippets → deep link `/meetings/{id}?t=ms&find=q` that seeks the player and pre-fills transcript search. FTS5 deferred: LIKE is instant at this scale and simpler to explain | `test_search_api.py` (12); E2E `global-search.spec.ts` (2) | ✅ |
| 2 | B2 | Export transcript / summary (TXT, Markdown) | Generated client-side from data already loaded (pure formatters in `lib/export.ts`, no extra endpoint); Fireflies-like Download dialog in the ⋯ menu with content, format, *timestamps* and *speaker names* options | `lib/export.test.ts` (6); E2E `export.spec.ts` (2, real file downloads) | ✅ |
| 3 | B6 | Dark mode | CSS variable tokens already planned; toggle in user menu; persisted in localStorage; respects `prefers-color-scheme` | E2E toggle | ⬜ |
| 4 | B4 | Tags / topics + filtering | AI keywords (`summary_keywords`) are the tags — no duplicate tag tables; `GET /api/meetings?keyword=`; keyword chips on rows and in notes filter the library | `test_filter_by_keyword_tag`; E2E "keyword chips filter by tag" | ✅ |
| 5 | B1 | Comments / highlights on segments | `segment_comments` table; hover action on transcript line | Integration; E2E | ⏸ |
| 6 | B5 | Ask-a-question chat | Keyword retrieval over segments → answer with cited timestamps; LLM if key configured | Unit | ⏸ |

## Evaluation value (why this order)

| ID | Value | Reasoning |
|----|-------|-----------|
| B3 | High | The PDF description itself says "search across transcripts"; strong Fireflies signature feature |
| B2 | Medium | Fireflies has a prominent Download flow; cheap once formatters exist |
| B6 | Medium | Visible polish; design tokens already planned as CSS variables |
| B4 | Medium | Reuses AI keywords; extends an existing filter UI |
| B1 | Low–Medium | New table + UI; nice but not core |
| B5 | Low without a real LLM | A heuristic "Ask" risks looking fake; only with an LLM key |
