import { expect, test } from "@playwright/test";

import { createMeetingViaApi } from "./helpers";

// Seed: 7 meetings dated 1, 3, 5, 8, 11, 16 and 23 days ago (see app/seed/data.py).
const rows = (page: import("@playwright/test").Page) => page.getByTestId("meeting-row");

// Other specs add meetings dated "now", so these tests look for seeded meetings by name
// instead of assuming the database holds only the seed.
const row = (page: import("@playwright/test").Page, title: string) =>
  rows(page).filter({ has: page.getByRole("link", { name: title, exact: true }) });

test.describe("Meetings library", () => {
  test("lists meetings with title, date, duration and participants", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveURL(/\/meetings$/);
    await expect(page.getByRole("heading", { name: "Meetings", level: 1 })).toBeVisible();
    await expect(page.getByText(/^\d+ meetings$/)).toBeVisible();
    const sync = row(page, "Weekly Product Sync");
    await expect(sync).toBeVisible();
    await expect(sync).toContainText(/\d+ min/);
    await expect(sync).toContainText(/\d{1,2}:\d{2}/); // time of day
    await expect(sync.getByLabel(/Priya Sharma/)).toBeVisible(); // participant avatars
    expect(await rows(page).count()).toBeGreaterThanOrEqual(7);
  });

  test("search by title narrows the list and survives a reload", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByLabel("Search by title").fill("q1 planning");
    await expect(page).toHaveURL(/q=q1/);
    await expect(rows(page)).toHaveCount(1);
    await expect(rows(page).first()).toContainText("Q1 Planning Kickoff");
    await page.reload();
    await expect(page.getByLabel("Search by title")).toHaveValue("q1 planning");
    await expect(rows(page)).toHaveCount(1);
  });

  test("top-bar search opens the filtered library", async ({ page }) => {
    await page.goto("/settings");
    await page.getByLabel("Search meetings").fill("design review");
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/meetings\?q=design/);
    await expect(rows(page).first()).toContainText("Design Review");
  });

  test("filter by participant", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Participant filter" }).click();
    await page.getByLabel("Find a person").fill("Tom");
    await page.getByText("Tom Becker").click();
    await page.keyboard.press("Escape");
    await expect(rows(page)).toHaveCount(1);
    await expect(rows(page).first()).toContainText("Brightline");
    await expect(page.getByRole("button", { name: "Participant filter" })).toContainText(
      "Tom Becker",
    );
  });

  test("filter by date range", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Date filter" }).click();
    await page.getByRole("option", { name: "Last 7 days" }).click();
    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(/date=7d/);
    // Seeded 1, 3 and 5 days ago are in; 8+ days ago are out.
    for (const title of [
      "Weekly Product Sync",
      "Engineering Sprint 14 Review",
      "Discovery Call — Brightline Logistics",
    ]) {
      await expect(row(page, title)).toBeVisible();
    }
    for (const title of [
      "Q1 Planning Kickoff",
      "Q4 Marketing Strategy",
      "Senior Backend Engineer — Hiring Debrief",
    ]) {
      await expect(row(page, title)).toHaveCount(0);
    }
  });

  test("sort by recency toggles newest/oldest first", async ({ page }) => {
    await page.goto("/meetings");
    await expect(page.getByRole("button", { name: /Sort: newest first/ })).toBeVisible();
    await expect(rows(page).first()).not.toContainText("Q1 Planning Kickoff");
    await page.getByRole("button", { name: /Sort:/ }).click();
    await expect(page).toHaveURL(/sort=oldest/);
    await expect(rows(page).first()).toContainText("Q1 Planning Kickoff"); // oldest seeded meeting
  });

  test("no matches shows an empty state with a way back", async ({ page }) => {
    await page.goto("/meetings?q=zzzz-nothing");
    await expect(page.getByText("No meetings match your filters")).toBeVisible();
    await page.getByRole("button", { name: "Clear filters" }).last().click();
    await expect(rows(page).first()).toBeVisible();
  });

  test("keyword chips filter by tag", async ({ page }) => {
    await page.goto("/meetings");
    await row(page, "Weekly Product Sync").getByRole("button", { name: "Release 2.4" }).click();
    await expect(page).toHaveURL(/keyword=Release/);
    await expect(rows(page)).toHaveCount(1);
    await page.getByRole("button", { name: "Remove tag filter" }).click();
    await expect(page).not.toHaveURL(/keyword=/);
  });
  test("meetings are grouped by week with the meeting count beside the range", async ({ page }) => {
    await page.goto("/meetings");
    const firstGroup = page.locator("section").first();
    await expect(firstGroup.getByRole("heading", { level: 2 })).toContainText(
      /Today · \d+ meetings?/,
    );
    // Columns: the date, time and duration of a row sit under their headings.
    const sync = row(page, "Weekly Product Sync");
    for (const name of ["Date", "Time", "Duration"]) {
      const heading = await page.getByText(name, { exact: true }).first().boundingBox();
      const cell = await sync
        .locator("> div")
        .nth(["Date", "Time", "Duration"].indexOf(name) + 1)
        .boundingBox();
      expect(Math.abs(heading!.x - cell!.x)).toBeLessThanOrEqual(2);
    }
  });

  test("row details show participants and tags; a tag filters the library", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Details for Weekly Product Sync" }).click();
    const details = page.getByRole("dialog");
    await expect(details).toContainText("Priya Sharma");
    await details.getByRole("button", { name: "Release 2.4" }).click();
    await expect(page).toHaveURL(/keyword=Release/);
    await expect(rows(page)).toHaveCount(1);
  });

  test("select meetings and delete them together", async ({ page }) => {
    const tag = `bulk-${Date.now()}`;
    await createMeetingViaApi(page, { title: `${tag} one` });
    await createMeetingViaApi(page, { title: `${tag} two` });
    await page.goto(`/meetings?q=${tag}`);
    await expect(rows(page)).toHaveCount(2);
    await page.getByLabel("Select all meetings").check();
    await expect(page.getByRole("region", { name: "Selection" })).toContainText("2 selected");
    await page
      .getByRole("region", { name: "Selection" })
      .getByRole("button", { name: "Delete" })
      .click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("2 meetings deleted")).toBeVisible();
    await expect(rows(page)).toHaveCount(0);
    await page.reload();
    await expect(page.getByText("No meetings match your filters")).toBeVisible();
  });

  test("navbar: profile and settings placeholders, coming-soon features", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Account menu" }).click();
    await page.getByRole("menuitem", { name: "Profile" }).click();
    await expect(page).toHaveURL(/\/settings\?tab=profile/);
    await expect(page.getByText("alex.morgan@northwind.io").first()).toBeVisible();
    await page.getByRole("tab", { name: "Integrations" }).click();
    await expect(page.getByText("Zoom", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: /^Analytics/ }).click();
    await expect(page.getByRole("dialog")).toContainText("Coming soon");
    await page.getByRole("button", { name: "Got it" }).click();
    await page.getByRole("button", { name: "Add to live meeting" }).click();
    await expect(page.getByRole("dialog")).toContainText("Coming soon");
  });
});
