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
| Library | Meetings grouped by day; rows with title, time, duration and participant avatars; overflow menu | Day groups, a time · duration · open-tasks line, AI keyword chips, an avatar stack and a ⋯ menu (edit, delete) |
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
- README screenshots were re-captured after pass 2.
