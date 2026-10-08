# Final Demo Script

A walkthrough of about 8 minutes for the evaluation. Every step uses the seeded data. Use the hosted link, or
locally run `docker compose up -d` plus `npm run dev` (README "Local Setup").

**Before you start:**
- Open the app at `/meetings` in light mode.
- Have a second tab on `/docs` (Swagger).
- Keep `backend/meeting-service/samples/standup.vtt` at hand (`retro.json` and `customer-onboarding.txt` also work).
- Optional: a terminal with `docker compose logs -f ai-service` to show Kafka traffic live.

## 1. Library: the Fireflies home view (≈1 min)
1. Point out the layout:
   - The sidebar (Meetings active, "Soon" badges on integrations, team and analytics).
   - The top bar (global search, *Add to live meeting*, *New meeting*, account menu).
   - Meetings grouped by day, each showing title, time, duration, open action items, AI keyword tags and avatars.
2. Type `sprint` in **Search by title**. The list narrows, and the URL updates (refresh to show it persists).
3. **Any time → Last 30 days**, then **Participants → Priya Sharma**. Filters combine. Click **Clear filters**.
4. Click **Newest first** to show sort by recency.
5. Click a keyword chip such as **Release 2.4** to show the tag filter (bonus).

## 2. Workspace: interactive transcript (≈2 min)
1. Open **Weekly Product Sync**. Notes are on the left and the transcript on the right, with the player docked at
   the bottom.
2. Press **Play** (or Space). The active line highlights and the transcript follows. Mention the simulated clock
   behind the `PlaybackClock` interface.
3. **Click a transcript line**. The player seeks there and plays.
4. **Drag the seek bar** to the other direction. The matching line highlights and scrolls into view.
5. Scroll the transcript manually. Auto-follow pauses and **Back to current** appears.
6. Press `/`, type `release`. Matches are highlighted with a count (1 / n); use Enter or the arrows to step through
   them.
7. Click an **Outline** chapter timestamp, then an action-item timestamp. Both seek the player.
8. Show the speaker timeline in the player bar and talk time in the notes.

## 3. AI notes and action items (≈1.5 min)
1. Walk through the notes: keywords, overview, outline/chapters, action items grouped by assignee.
2. **Tick an action item.** The update is optimistic, with a toast.
3. **Edit** one: change the title, assignee and due date, then save.
4. Click **+ Add** in Action items to add one, then delete it.
5. Refresh the page. Everything persists.

## 4. Create a meeting: the asynchronous pipeline (≈1.5 min)
1. Click **New meeting → Upload file** and choose `backend/meeting-service/samples/standup.vtt`. The title and participants come from the file;
   click **Create**.
2. The new meeting opens with **Generating notes…**. Explain the flow:
   - The API commits the meeting **and** an outbox event in one transaction.
   - The relay publishes it to Kafka.
   - The AI service generates the notes and publishes the result.
   - The Meeting Service applies the result idempotently.
3. About a second later, the **Notes ready** toast appears and the notes fill in. (Optional: show the event in the
   `ai-service` logs.)
4. Briefly show **Paste transcript** and **Manual entry** as the other create options. Paste a malformed line to show the
   line-numbered error.

## 5. Edit and delete (≈45 s)
1. **⋯ → Edit details**: rename the meeting and add a participant. A toast confirms, and the header updates.
2. **⋯ → Delete meeting**: a confirm dialog appears, then you return to the library and the meeting is gone. Refresh
   to show it stays gone.

## 6. Bonuses (≈1 min)
1. **Global search** in the top bar: type `geocoding`. Results are grouped by meeting with highlighted snippets.
   Clicking one deep-links to that moment, with the player seeked and the transcript search pre-filled.
2. **⋯ → Download**: export the transcript as TXT (with timestamps and speakers) or the notes as Markdown.
3. **Account menu → Dark mode**. Reload to show it persists.

## 7. Engineering, if there's time (≈1 min)
- Swagger at `/docs`: 15 REST operations, one error envelope.
- Mention the test suites:
  - 183 + 39 backend tests (97 % / 99 % coverage).
  - 2 tests against a real Kafka broker.
  - 74 Vitest tests.
  - 39 Playwright tests against the real services.
- Repo tour: `backend/meeting-service/app/{routers,services,repositories,events}`, `backend/ai-service`,
  `frontend/{app,components,hooks,lib}`, `docs/adr/`.

## If something goes wrong live
| Symptom | Say / do |
|---------|----------|
| Notes stay "Generating…" | The broker or AI service is down. Writes are safe in the outbox and will publish when it's back. Show the status chip, or **Retry** |
| Hosted demo is slow on first load | It's a cold start on free hosting; refresh once |
| A meeting shows "Summary generation failed" | That's the designed failure path: the reason is shown, and **Retry** re-queues the work |
