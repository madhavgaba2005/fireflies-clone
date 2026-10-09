# UI Fidelity Audit

How closely the UI follows the Fireflies meeting workspace, checked against screenshots of the running app.

**Reference:**
- The public Fireflies site and its help-centre articles on the Notepad and meeting summaries (links in
  [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) §10).
- Fireflies was used only as a visual and UX reference: no source code, assets or logos were copied, and the product
  has its own name, "Lumen".

**Method:**
- A Playwright script captured the same ten screens each pass at 1440×900 and 390×844: library, row hover,
  workspace while playing, transcript search, meeting menu, new-meeting dialog, settings, empty library, not-found
  and phone workspace.
- Pass 2 added dark-mode captures and the expanded-panel views.

## What matches the Fireflies experience

| Area | Fireflies pattern | Here |
|------|-------------------|------|
| Navigation | Left sidebar with an active item in the brand colour; a top bar with global search, a live-meeting call-to-action, "New" and an avatar | Same structure. Out-of-scope items are marked "Soon" and open Coming-soon dialogs |
| Library | Icon rail + contextual Meetings sidebar; compact toolbar; a table with MEETING / DATE / TIME / DURATION columns, week groups with a count, divider-only rows, ⋯ and ⓘ at the far right | Day groups, a time · duration · open-tasks line, AI keyword chips, an avatar stack and a ⋯ menu (edit, delete) |
| Workspace | Notepad: AI notes on one side, transcript on the other, docked player | Notes on the left (keywords → overview → outline → action items by assignee → talk time), transcript on the right, docked player with a speaker timeline and speed control |
| Transcript | Coloured speaker avatars, name with timestamp, click to play from a line, find-in-transcript | Same, plus an active-line highlight, auto-follow with a "Back to current" button, and a match counter with ↑/↓ |
| Feedback | Toasts for actions; clear processing state | Toasts for every mutation and failure; "Generating notes…", "Notes ready" and "Failed + Retry" chips |
| Panels | Notes and transcript can each be focused | Expand / restore button in each panel header (desktop); tabs on phones |
| Theme | Light and dark | Appearance settings: System / Light / Dark |

## Pass 1: layout and information hierarchy

| # | Finding | Fix |
|---|---------|-----|
| 1 | Transcript lines put the timestamp inline before the text, so wrapped lines hung under the speaker name and the time was hard to scan | Speaker name and time now share one row and the text sits below, as in Fireflies. Continuation lines by the same speaker show their time in the left gutter |
| 2 | Panels could not be expanded (the one open item on the UI checklist) | Desktop focus mode: **Expand notes** / **Expand transcript** / **Show both panels**. Sync, search and seeking keep working while a panel is expanded (E2E) |
| 3 | Avatar stacks overlapped so far that initials were clipped | Less overlap; the 2 px surface ring is kept |
| 4 | On phones the meeting header wrapped its date, duration and participant count over several lines | The meta items no longer wrap internally, the participant count shows only from `sm` up (the avatars remain), the Share button is icon-only on phones, and long titles clamp to two lines |
| 5 | The theme could only be toggled from the account menu, and there was no "System" option | Settings → **Appearance** with System / Light / Dark. System follows OS changes live. The menu toggle stays as a shortcut |

## Pass 2: spacing, typography, controls and states

| # | Finding | Fix |
|---|---------|-----|
| 6 | The notes and transcript header bars had slightly different heights, so their bottom borders did not line up | Both are now a fixed `h-14` |
| 7 | On phones the transcript panel repeated "Transcript" directly under the "Transcript" tab | The panel title is hidden below `lg`; the search box takes the row |
| 8 | The "System" theme card's hint wrapped onto a third line | Shorter hint ("Follow device") |
| 9 | Dark mode: checked keyword chips, outline timestamps, status chips, highlights and the expanded notes for contrast | No changes needed. Text tokens meet WCAG AA against their surfaces |
| 10 | States: empty library ("No meetings match your filters" + Clear filters), not-found meeting, loading skeletons, failed notes with Retry | Reviewed. Each already had a clear next action; no changes |

## Library redesign (against a Fireflies Meetings screenshot)

The baseline looked like a different product: one wide sidebar, a large page header, a rounded card, grey
uppercase day bands and fields positioned with flex spacing. The redesign was compared side by side at 1440, 1024
and 390 px.

**Pass A: shell, navigation, toolbar, grid and proportions**

| # | Change |
|---|--------|
| A1 | The single sidebar is replaced by a 48 px **icon rail** (logo, Meetings, Uploads, Analytics, Integrations, Team; Settings at the bottom, with tooltips) and a 220 px **contextual Meetings sidebar** on the library. It has All meetings, Shared with me (Soon), and Channels with an empty state and "+ Channel" (Soon). There is no "My meetings": the demo user attends no seeded meeting, so that view would always be empty, which would be false functionality |
| A2 | A 56 px toolbar on one line: the page label (the library's `h1`), global search (≤ 320 px), Invite (Soon), **New meeting**, Add to live meeting, Notifications (Soon) and the avatar menu. The large in-content page header is gone |
| A3 | A full-width table on one CSS grid template (`tableGrid.ts`) shared by the header and every row. MEETING / DATE / TIME / DURATION headings line up with their cells to within 2 px (E2E-checked) |
| A4 | Rows are 72 px tall with divider lines instead of a rounded card. The details cell has the checkbox, one participant avatar, the title, and a second line with participants, open action items, status and up to two tag chips |
| A5 | Date groups are by **week** (Sunday start, as in the reference): "Oct 4 – Today · 3 meetings" |

**Pass B: date contrast, type, spacing, controls and responsive states**

| # | Change |
|---|--------|
| B1 | Group headings use dark 15 px / 500 text (`.type-group-heading`), with the count on the same line in muted blue-gray (`.type-group-count`). The grey uppercase band is gone |
| B2 | New tokens in both themes: `--meta` (blue-gray metadata, AA contrast), `--row-hover` and `--rail`. Type classes: `.type-col-heading`, `.type-row-title`, `.type-meta` |
| B3 | The "+N" avatar badge was removed: it duplicated the "+N" in the names line and cluttered the avatar |
| B4 | The duplicate "Uploads" entry was removed from the contextual sidebar (the rail has it, as in the reference). An E2E test caught the ambiguity |
| B5 | 1024 px: the contextual sidebar stays, the date/time/duration columns narrow (116 / 92 / 76 px), filters fit on one line, and the toolbar label is narrower |
| B6 | 390 px: the rails become a drawer (primary items plus the Meetings section). Rows collapse to avatar, title, participants and "date · time · duration". Filter controls scroll sideways instead of stacking. No horizontal page overflow (E2E) |
| B7 | Row actions: ⋯ (Open, Edit details, Delete) and ⓘ details (participants, clickable tags, action items). Checkboxes appear on hover or focus and stay visible once something is selected; selecting rows enables a real bulk delete |

Kept unchanged: search, date and participant filters, sorting, tags, detail navigation, edit and delete, the API and
database, dark mode.

## Meeting page and de-boxing (against a Fireflies meeting screenshot)

The meeting page was still a full-width header over two equal-feeling panels, with bordered section blocks and
card-like transcript messages. Every meeting uses the same workspace component; it was verified on three seeded
meetings (own title, participants, transcript, notes and action items each).

| # | Change |
|---|--------|
| C1 | On meeting routes the global toolbar gives way to a one-line **meeting toolbar**: ← and the breadcrumb `All meetings › Title` on the left; a purple **Share**, copy link, ⋯ (edit, regenerate, download, delete), notifications and the avatar on the right. Global search and New meeting stay on the library and settings toolbars |
| C2 | **Notes are the primary column (~73 %)** with the title and metadata at the top. The transcript gets `clamp(320px, 27%, 460px)`. Both panels scroll independently, the player stays docked, and the expand buttons still focus either panel |
| C3 | **De-boxed notes:** no section borders or blocks. Keywords, Overview, Outline and Action items are marked by small purple icons, 14 px headings and spacing on one white canvas, in a centred reading column (≤ 860 px). "Notes ready" is quiet muted text; only the in-progress and failed states use a coloured pill |
| C4 | **Transcript as a continuous conversation:** a compact header with the search on its own row, 20 px avatars, 12.5 px names, 13.5 px text, tighter spacing. Only the active line gets a soft tint with a 2 px accent |
| C5 | **Settings de-boxed:** the content card is gone (a thin divider separates it from the tabs), and integrations are a divided list instead of tiles. Controls such as the theme radio cards keep their borders for usability |
| C6 | Tablet keeps both columns (transcript at 320 px). Phones use the Notes / Transcript tabs and a compact toolbar (☰, ←, title, Share, copy link, ⋯); notifications and the avatar are in the drawer. No horizontal overflow |

**Favicon:** `frontend/app/icon.svg` is the Lumen spark on a purple tile (original, simplified for 16 px). The App
Router emits `<link rel="icon" href="/icon.svg…" type="image/svg+xml">`, served as `image/svg+xml`. Previously the
app had no favicon at all.

## Known differences (accepted)

- **No real audio or video.** The player is a simulated clock behind the `PlaybackClock` interface, which the PDF
  allows. An info tooltip in the player says so.
- **No Fireflies-only features:** AskFred, soundbites, comments and integrations are out of scope. Bonus B1 and B5
  were deliberately deferred.
- **Brand colour and logo are original.** The layout follows Fireflies; the visual identity does not copy it.

## Verification

- E2E tests cover the expanded panels, the theme options (including System following the OS live and the choice
  surviving a reload), speaker names and timestamps on transcript lines, and phone-width layout
  with no horizontal scroll.
- README screenshots were re-captured from the production build on 2026-10-09, after the meeting-page and
  spacing changes: library (light, dark, 1024 px, phone), filters, new-meeting dialog, workspace (light, dark,
  phone), transcript search, and Settings → Appearance.
