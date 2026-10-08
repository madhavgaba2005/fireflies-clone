# UI Design Spec

> Status: **Accepted for implementation (Phase 1)** — derived from fireflies.ai and the official help-centre articles
> ("Learn about the Fireflies Notepad", "Fireflies AI Meeting Summaries"), reviewed 2026-10-08. The logged-in app
> could not be inspected directly. Implemented in Milestones D–F — see §11 for what was built and README for screenshots. Fireflies is a **visual/UX reference only** —
> no Fireflies code, logos, illustrations or proprietary assets are used. Our product name/logo is original.

## 1. Observed Fireflies patterns we will recreate

| Pattern (reference) | Our implementation |
|---------------------|--------------------|
| Left navigation menu with "Meetings" entry, collapsible | `Sidebar`: Home · Meetings · Uploads · Integrations · Analytics (soon) · Team (soon) · Settings; collapses to icon rail |
| Meeting page = **two-panel Notepad**: summary/notes left, transcript right; panels can expand | `MeetingWorkspace`: resizable split, "expand" toggle per panel |
| Summary header with "General Summary" template dropdown and copy button | `SummaryPanel` header: template label (only "General" active, others Coming soon) + Copy |
| "General Summary" sections, **in this order**: Keywords → Overview → Notes (bullet points) → Time-stamped notes (chapters linked to the transcript) → Action items (associated with speakers) | Same order in one scrollable notes panel: Keywords chips · Overview · Notes · Outline (click a chapter → seek) · Action items **grouped by assignee** |
| Transcript: Find bar, speaker labels, timestamps, playback synced, adjustable speed (Fireflies also has Replace/edit mode — out of scope) | `TranscriptPanel` with `TranscriptSearch` ("n of m", ↑/↓), speaker filter chips, `TranscriptLine` |
| Collapsible tool rail on the meeting page (Search, Index, Soundbites, Comments, Bookmarks) | Narrow icon rail: Index (jump to sections) active; Soundbites/Comments/Bookmarks Coming soon (or bonus B1) |
| Top bar: Share, link copy, ⋯ menu (rename, regenerate notes, meeting info, download) | Meeting header: Share (soon) · Copy link · ⋯ menu → Edit details · Regenerate notes · Download (bonus B2) · Delete |
| Download at bottom centre; options for timestamps & speaker labels | Export modal with the same two toggles (bonus B2) |
| AskFred assistant panel | "Ask AI" button → Coming soon (bonus B5 if time) |

## 2. Page regions

**Library (`/meetings`)**
```
┌ Sidebar ┐┌ TopBar: [🔍 Search meetings  /]           [+ New meeting] [avatar ▾] ┐
│ logo    ││ Meetings                                                            │
│ Home    ││ [All meetings] [Uploads]   Filters: [Date ▾] [Participants ▾] [Sort ▾]│
│ Meetings││ ─────────────────────────────────────────────────────────────────── │
│ Uploads ││ ▢ Q3 Roadmap Planning      Sep 30, 10:00 · 45 min   (PS)(AM)(+2)  ⋯ │
│ …       ││ ▢ Acme renewal call        Sep 29, 15:30 · 32 min   (JL)(PS)      ⋯ │
│ Settings││ grouped by day: "Today", "Yesterday", "Sep 28"…                    │
└─────────┘└─────────────────────────────────────────────────────────────────────┘
```
**Workspace (`/meetings/[id]`)**
```
┌ Header: ← Meetings / Title  · date · duration · participants avatars   [Share][⋯] ┐
├ Notes panel (≈42%) ─────────────────┬ Transcript panel ──────────────────────────┤
│ ✨ AI summary  [General ▾] [Copy]    │ [🔍 Find in transcript   3 of 12 ↑ ↓] [Speakers ▾]│
│ Keywords: chip chip chip            │ (PS) Priya Sharma  00:12                    │
│ Overview paragraph                  │      Morning everyone, let's start with…    │
│ Outline  00:00 Q3 priorities  ▸     │ (AM) Arjun Mehta   00:41   ← active (tinted)│
│ Action items  ☐ Send deck — Arjun   │      …                                      │
├─────────────────────────────────────┴────────────────────────────────────────────┤
│ Player bar: ⏪15 ▶ 15⏩  02:13 ━━━━━━●──────────── 45:10   1x ▾   speaker timeline │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## 3. Design tokens (original values, Fireflies-like *feel*)

| Role | Light | Dark (bonus) |
|------|-------|--------------|
| `--primary` (CTA, active nav, active line accent) | violet `#6D28D9` | `#8B5CF6` |
| `--primary-soft` (active transcript line bg, selected filter) | `#F3EEFF` | `#2A2140` |
| `--bg` / `--surface` | `#F7F7FB` / `#FFFFFF` | `#0F1117` / `#171A23` |
| `--border` | `#E6E6EF` | `#2A2E3A` |
| `--text` / `--text-muted` | `#1F2033` / `#6B6F80` | `#E7E8EE` / `#9A9EAD` |
| `--mark` (search highlight) | `#FDE68A`; current match `#F59E0B` | same |
| Speaker palette | 8 distinct hues, assigned deterministically from participant id | |

* **Typography:** Inter (Google Fonts). 13 px dense UI text, 14 px transcript body, 20/24 px page titles, tabular numerals for timestamps.
* **Spacing:** 4 px grid (4/8/12/16/24/32). Rows 56 px. Radius 8 px (cards), 6 px (inputs), full (avatars, chips).
* **Elevation:** borders over shadows; shadow only on modals/menus.
* **Icons:** lucide-react, 16 px in dense UI.

## 4. Component hierarchy
```
AppShell
 ├─ Sidebar (NavItem)
 ├─ TopBar (GlobalSearch, NewMeetingButton, UserMenu)
 └─ page
     ├─ MeetingsPage → MeetingFilters (SearchInput, DateRangeFilter, ParticipantFilter, SortToggle)
     │                 MeetingList → MeetingDayGroup → MeetingRow (AvatarStack, DurationBadge, RowMenu)
     │                 CreateMeetingModal (tabs: Upload | Paste | Form), EditMeetingModal, ConfirmDialog
     └─ MeetingPage → MeetingHeader
                      MeetingWorkspace
                       ├─ SummaryPanel → Keywords, Overview, Topics, ActionItems (ActionItemRow, ActionItemComposer)
                       └─ TranscriptPanel → TranscriptSearch, SpeakerFilter, TranscriptLine*
                      AudioPlayer (SeekBar, SpeedMenu)  ← state from usePlaybackClock(PlaybackClock)
ui/: Button, IconButton, Input, Modal, DropdownMenu, Tabs, Avatar, AvatarStack, Badge, Skeleton, EmptyState, ErrorState, ComingSoon
```

## 5. Interaction patterns
* Transcript line hover → subtle bg + "▶ play from here" affordance; click → seek + play.
* Active line: `--primary-soft` bg + left accent bar; auto-scroll centres it, **paused for 4 s after the user scrolls manually** (prevents fighting the user).
* Search: `/` focuses library search; `Ctrl/⌘+F` inside workspace focuses transcript find; Enter / Shift+Enter cycle matches.
* Optimistic action-item toggles with rollback + error toast.
* Destructive actions always confirm (dialog names the meeting).
* All modals: focus-trapped, Esc closes, return focus to trigger.

## 6. Media player design
```
PlaybackClock (interface)            usePlaybackClock(clock) → { currentMs, playing, rate, play, pause, seek, setRate }
 ├─ SimulatedClock   rAF-driven, no media (now)
 └─ HtmlMediaClock   wraps <audio>/<video> (later, if a sample file is added)
```
`AudioPlayer`, `TranscriptPanel` and `Outline` only see the hook — swapping the clock changes no UI or sync code.
Player bar also shows a **speaker timeline** (coloured blocks per speaker turn) — a recognizable Fireflies cue.

## 7. States
| Screen | Loading | Empty | Error |
|--------|---------|-------|-------|
| Library | 6 skeleton rows | "No meetings yet" + Upload CTA; "No meetings match your filters" + Clear filters | Error card + Retry |
| Workspace | Panel skeletons | No transcript: "This meeting has no transcript" + upload CTA | 404 page "Meeting not found" + back link; panel-level error + Retry |
| Summary | "✨ Generating notes…" shimmer (status `pending`) | — | `failed`: reason + Retry |
| Action items | — | "No action items" + Add | Toast on failed mutation |
| Transcript search | — | "No matches for ‘x’" | — |

## 8. Responsive
* ≥ 1280: sidebar expanded, two panels side by side.
* 1024–1279: sidebar icon rail.
* < 1024: panels become tabs (Notes | Transcript), player stays docked at bottom; sidebar becomes a drawer.
* No horizontal page scroll at 360 px.

## 9. Fidelity checklist (used in Phase 16 polish)
- [ ] Left sidebar with active item highlighted in the accent colour
- [ ] Library rows (not a bare table): title, date · duration, participant avatar stack, status chip, row menu
- [ ] Two-panel notepad, independently scrolling, each expandable
- [ ] Notes sections in Fireflies order; sparkle "AI" labels
- [ ] Transcript lines: coloured avatar, speaker name, timestamp, hover "play from here"
- [ ] Docked player bar with speed menu and speaker timeline
- [ ] Toasts for every mutation; Coming-soon modals for out-of-scope features
- [ ] Loading skeletons, empty and error states on every screen

## 10. References (visual/UX only — no code or assets copied)
- https://fireflies.ai/
- https://guide.fireflies.ai/articles/6653885315-learn-about-the-fireflies-notepad
- https://guide.fireflies.ai/articles/9547055509-learn-about-the-fireflies-ai-meeting-summaries

## 11. Implementation notes (Milestones D–F)
- **Product name and logo:** "Lumen" with an original sparkle mark — Fireflies is a UX reference, not a brand to copy.
- **Library:** day groups ("Today", "Yesterday", "Mon, Oct 5") with sticky headers; rows show time, duration, open
  action items, processing chip (hidden when ready), two keyword chips (click → tag filter), avatar stack, ⋯ menu.
- **Notes panel order:** Keywords → Overview → Outline (timestamped, clickable, current chapter highlighted) →
  Action items (grouped by assignee, AI badge, due date / overdue, jump-to-moment) → Talk time. A separate bullet
  "Notes" section was folded into the outline chapters (each chapter carries its own summary).
- **Transcript:** consecutive lines by one speaker are grouped under one avatar/name; each line has a timestamp with a
  hover "play" affordance; the active line gets a violet tint and left bar.
- **Auto-follow rule:** the active line scrolls into view on playback *and* on seeks, except for 4 s after the user
  scrolls or navigates search results — then a "Back to current" pill appears.
- **Player:** speaker timeline painted under the seek bar; speaker legend; speed menu; an info icon states that playback
  is simulated.
- **Responsive (tested):** < 1024 px the sidebar becomes a drawer and the workspace panels become Notes / Transcript
  tabs; no horizontal scroll at 390 px.
- **Not implemented (by design):** the Fireflies "tool rail" (Soundbites / Comments / Bookmarks) — those are bonus or
  out-of-scope features; the AskFred panel (bonus B5).
