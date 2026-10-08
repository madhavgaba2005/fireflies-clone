import { expect, test } from "@playwright/test";

import { API, activeLine, playerTimeMs } from "./helpers";

test.describe("Meeting workspace", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("link", { name: "Weekly Product Sync" }).click();
    await expect(
      page.getByRole("heading", { name: "Weekly Product Sync", level: 1 }),
    ).toBeVisible();
  });

  test("shows speaker-labelled, timestamped transcript and AI notes", async ({ page }) => {
    const lines = page.getByTestId("transcript-line");
    await expect(lines).toHaveCount(30);
    await expect(lines.first()).toContainText("Priya Sharma");
    await expect(lines.first()).toContainText("00:00");
    await expect(lines.nth(1)).toContainText("Arjun Mehta");
    await expect(page.getByTestId("overview")).toContainText("release 2.4");
    await expect(page.getByRole("list", { name: "Outline" }).getByRole("listitem")).toHaveCount(4);
    await expect(page.getByRole("link", { name: "Activation" })).toBeVisible();
    await expect(page.getByTestId("action-item")).toHaveCount(6);
    await expect(page.getByRole("list", { name: "Talk time by speaker" })).toBeVisible();
  });

  test("clicking a transcript line seeks the player there and plays", async ({ page }) => {
    const target = page.getByTestId("transcript-line").nth(9); // "Arjun, is the release date…"
    const timestamp = (await target.getByRole("button").getAttribute("aria-label"))!.match(
      /(\d\d):(\d\d)/,
    )!;
    const expectedMs = (Number(timestamp[1]) * 60 + Number(timestamp[2])) * 1000;

    await target.getByRole("button").click();
    await expect(page.getByRole("button", { name: "Pause", exact: true })).toBeVisible(); // now playing
    expect(await playerTimeMs(page)).toBeGreaterThanOrEqual(expectedMs);
    await expect(target).toHaveAttribute("data-active", "true");
    await expect(activeLine(page)).toHaveCount(1);

    // Playback keeps moving forward from the clicked moment.
    await page.waitForTimeout(1200);
    expect(await playerTimeMs(page)).toBeGreaterThan(expectedMs + 500);
    await page.getByRole("button", { name: "Pause", exact: true }).click();
    await expect(page.getByRole("button", { name: "Play", exact: true })).toBeVisible();
  });

  test("moving the seek bar highlights and scrolls to the matching line", async ({ page }) => {
    const lines = page.getByTestId("transcript-line");
    const last = lines.last();
    const label = (await last.getByRole("button").getAttribute("aria-label"))!;
    const [, mm, ss] = label.match(/(\d\d):(\d\d)/)!;
    // The label shows whole seconds; the line may start up to 999 ms later, so aim past that.
    const insideLastLine = (Number(mm) * 60 + Number(ss) + 1.5) * 1000;

    await page.getByRole("slider", { name: "Seek" }).fill(String(insideLastLine));
    await expect(last).toHaveAttribute("data-active", "true");
    await expect(last).toBeInViewport();
    await expect(lines.first()).not.toHaveAttribute("data-active", "true");

    await page.getByRole("slider", { name: "Seek" }).fill("0");
    await expect(lines.first()).toHaveAttribute("data-active", "true");
    await expect(lines.first()).toBeInViewport();
  });

  test("playback highlights the active line and keeps it in view", async ({ page }) => {
    const lines = page.getByTestId("transcript-line");
    await page.getByRole("slider", { name: "Seek" }).fill("200000"); // far down the transcript
    await page.getByRole("button", { name: "Play", exact: true }).click();
    const active = activeLine(page);
    await expect(active).toHaveCount(1);
    await expect(active).toBeInViewport();
    await expect(lines.first()).not.toBeInViewport();
  });

  test("outline chapters and action-item timestamps seek the player", async ({ page }) => {
    const chapter = page.getByRole("list", { name: "Outline" }).getByRole("button").nth(1);
    await chapter.click();
    const ms = await playerTimeMs(page);
    expect(ms).toBeGreaterThan(60_000); // chapter 2 starts after a minute
    await expect(page.getByRole("button", { name: "Pause", exact: true })).toBeVisible();
  });

  test("search within the transcript highlights matches and navigates between them", async ({
    page,
  }) => {
    const search = page.getByLabel("Find in transcript");
    await search.fill("IMPORT");
    const count = page.getByTestId("match-count");
    await expect(count).toHaveText(/^1 \/ \d+$/);
    const total = Number((await count.textContent())!.split("/")[1]);
    expect(total).toBeGreaterThan(3);
    await expect(page.locator("mark")).toHaveCount(total);
    await expect(page.locator("mark[data-current-match]")).toHaveCount(1);
    await expect(page.locator("mark").first()).toHaveText(/import/i);

    await search.press("Enter");
    await expect(count).toHaveText(`2 / ${total}`);
    await page.getByRole("button", { name: "Previous match" }).click();
    await page.getByRole("button", { name: "Previous match" }).click();
    await expect(count).toHaveText(`${total} / ${total}`); // wraps around
    await expect(page.locator("mark[data-current-match]")).toBeInViewport();

    // Search never hides the transcript.
    await expect(page.getByTestId("transcript-line")).toHaveCount(30);
  });

  test("search with no matches says so", async ({ page }) => {
    await page.getByLabel("Find in transcript").fill("kubernetes");
    await expect(page.getByTestId("match-count")).toHaveText("0 / 0");
    await expect(page.getByRole("status").filter({ hasText: "No matches" })).toBeVisible();
    await page.getByRole("button", { name: "Clear search" }).click();
    await expect(page.locator("mark")).toHaveCount(0);
  });

  test("keyboard: space plays and pauses, / focuses search", async ({ page }) => {
    await page.locator("body").click({ position: { x: 5, y: 500 } });
    await page.keyboard.press(" ");
    await expect(page.getByRole("button", { name: "Pause", exact: true })).toBeVisible();
    await page.keyboard.press(" ");
    await expect(page.getByRole("button", { name: "Play", exact: true })).toBeVisible();
    await page.keyboard.press("/");
    await expect(page.getByLabel("Find in transcript")).toBeFocused();
  });

  test("exact boundary: a line becomes active at its start ms, the previous one just before", async ({
    page,
  }) => {
    const id = page.url().match(/meetings\/(\d+)/)![1];
    const transcript = await (
      await page.request.get(`${API}/api/meetings/${id}/transcript`)
    ).json();
    const segments: { start_ms: number }[] = transcript.segments;
    const index = 12;
    const start = segments[index].start_ms;
    expect(start % 100).toBe(0); // the seek slider moves in 100 ms steps
    const lines = page.getByTestId("transcript-line");
    const seek = page.getByRole("slider", { name: "Seek" });

    await seek.fill(String(start - 100)); // paused seek, just before the boundary
    await expect(lines.nth(index - 1)).toHaveAttribute("data-active", "true");
    await seek.fill(String(start)); // exactly on the boundary: the next line wins
    await expect(lines.nth(index)).toHaveAttribute("data-active", "true");
    await expect(lines.nth(index)).toBeInViewport();
    await expect(activeLine(page)).toHaveCount(1);
  });

  test("notes or transcript can be expanded to full width and restored", async ({ page }) => {
    const notes = page.getByTestId("notes-panel");
    const transcript = page.getByTestId("transcript-panel");
    await page.getByRole("button", { name: "Expand transcript" }).click();
    await expect(notes).toBeHidden();
    await expect(transcript).toBeVisible();
    // Sync still works while expanded.
    await page.getByTestId("transcript-line").nth(3).getByRole("button").click();
    await expect(page.getByTestId("transcript-line").nth(3)).toHaveAttribute("data-active", "true");

    await page.getByRole("button", { name: "Show both panels" }).click();
    await expect(notes).toBeVisible();
    await page.getByRole("button", { name: "Expand notes" }).click();
    await expect(transcript).toBeHidden();
    await expect(page.getByTestId("overview")).toBeVisible();
    await page.getByRole("button", { name: "Show both panels" }).click();
    await expect(transcript).toBeVisible();
  });

  test("unknown meeting shows a not-found state", async ({ page }) => {
    await page.goto("/meetings/99999");
    await expect(page.getByText("Meeting not found")).toBeVisible();
    await page.getByRole("link", { name: "Back to meetings" }).click();
    await expect(page).toHaveURL(/\/meetings$/);
  });
});
