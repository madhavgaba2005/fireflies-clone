import path from "node:path";

import { expect, test } from "@playwright/test";

import { createMeetingViaApi, SHORT_TRANSCRIPT } from "./helpers";

const SAMPLES = path.resolve(__dirname, "../../../backend/meeting-service/samples");

test.describe("Meeting management", () => {
  test("create by pasting a transcript: notes are generated asynchronously and persist", async ({
    page,
  }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "New meeting" }).click();
    const dialog = page.getByRole("dialog", { name: "New meeting" });
    await dialog.getByRole("tab", { name: "Paste transcript" }).click();
    await dialog.getByLabel("Title").fill("E2E launch review");
    await dialog.getByLabel("Transcript").fill(SHORT_TRANSCRIPT);
    await dialog.getByRole("button", { name: "Create meeting" }).click();

    await expect(page.getByText("Meeting created")).toBeVisible();
    await expect(page.getByRole("heading", { name: "E2E launch review", level: 1 })).toBeVisible();
    await expect(page.getByTestId("transcript-line")).toHaveCount(4);
    // Outbox → AI service → result: the UI polls and flips to "Notes ready" by itself.
    await expect(page.getByText("Notes ready")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("overview")).toContainText("Dana Fox and Omar Reyes met");
    await expect(
      page.getByTestId("action-item").filter({ hasText: "Fix the annual checkout before Friday" }),
    ).toBeVisible();

    await page.reload();
    await expect(page.getByTestId("overview")).toBeVisible();
    await page.goto("/meetings");
    await expect(page.getByRole("link", { name: "E2E launch review" })).toBeVisible();
  });

  test("create by uploading a WebVTT file", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Uploads" }).click();
    const dialog = page.getByRole("dialog", { name: "New meeting" });
    await dialog.getByLabel("Transcript file").setInputFiles(path.join(SAMPLES, "standup.vtt"));
    await expect(dialog.getByLabel("Title")).toHaveValue("Standup");
    await dialog.getByRole("button", { name: "Create meeting" }).click();
    await expect(page.getByRole("heading", { name: "Standup", level: 1 })).toBeVisible();
    await expect(page.getByTestId("transcript-line").first()).toContainText("Noah Williams");
  });

  test("create via the manual form, without a transcript", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "New meeting" }).click();
    const dialog = page.getByRole("dialog", { name: "New meeting" });
    await dialog.getByRole("tab", { name: "Manual entry" }).click();
    await dialog.getByLabel("Title").fill("E2E planning call");
    await dialog.getByLabel("Participants").fill("Grace Hopper");
    await dialog.getByLabel("Participants").press("Enter");
    await dialog.getByLabel("Duration (minutes)").fill("45");
    await dialog.getByRole("button", { name: "Create meeting" }).click();
    await expect(page.getByRole("heading", { name: "E2E planning call", level: 1 })).toBeVisible();
    await expect(page.getByText("No transcript", { exact: true })).toBeVisible();
    await expect(page.getByText("45 min")).toBeVisible();
  });

  test("a malformed transcript shows the server's error and creates nothing", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("button", { name: "New meeting" }).click();
    const dialog = page.getByRole("dialog", { name: "New meeting" });
    await dialog.getByRole("tab", { name: "Paste transcript" }).click();
    await dialog.getByLabel("Title").fill("Broken");
    await dialog.getByLabel("Transcript").fill("[00:10] A: later\n[00:05] B: earlier");
    await dialog.getByRole("button", { name: "Create meeting" }).click();
    await expect(dialog.getByRole("alert")).toContainText(
      "Line 2: Timestamps must not go backwards",
    );
    await expect(dialog).toBeVisible();
  });

  test("edit title and participants; changes persist after reload", async ({ page }) => {
    const id = await createMeetingViaApi(page, {
      title: "E2E edit me",
      participants: [{ name: "Ada Park" }],
    });
    await page.goto(`/meetings/${id}`);
    await page.getByRole("button", { name: "Meeting actions" }).click();
    await page.getByRole("menuitem", { name: "Edit details" }).click();
    const dialog = page.getByRole("dialog", { name: "Edit meeting" });
    await dialog.getByLabel("Title").fill("E2E edited title");
    await dialog.getByLabel("Participants").fill("Ben Cole");
    await dialog.getByLabel("Participants").press("Enter");
    await dialog.getByRole("button", { name: "Remove Ada Park" }).click();
    await dialog.getByRole("button", { name: "Save changes" }).click();

    await expect(page.getByText("Meeting updated")).toBeVisible();
    await page.reload();
    await expect(page.getByRole("heading", { name: "E2E edited title", level: 1 })).toBeVisible();
    await expect(page.getByLabel("Ben Cole")).toBeVisible();
    await expect(page.getByLabel("Ada Park")).toHaveCount(0);
  });

  test("delete a meeting from the library; it stays gone after reload", async ({ page }) => {
    await createMeetingViaApi(page, { title: "E2E delete me" });
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Actions for E2E delete me" }).click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page
      .getByRole("dialog", { name: "Delete meeting?" })
      .getByRole("button", { name: "Delete" })
      .click();
    await expect(page.getByText("Meeting deleted")).toBeVisible();
    await expect(page.getByRole("link", { name: "E2E delete me" })).toHaveCount(0);
    await page.reload();
    await expect(page.getByRole("link", { name: "Weekly Product Sync" })).toBeVisible();
    await expect(page.getByRole("link", { name: "E2E delete me" })).toHaveCount(0);
  });

  test("delete from the workspace returns to the library", async ({ page }) => {
    const id = await createMeetingViaApi(page, { title: "E2E delete from workspace" });
    await page.goto(`/meetings/${id}`);
    const failed: string[] = [];
    page.on("response", (r) => r.status() >= 400 && failed.push(`${r.status()} ${r.url()}`));
    await page.getByRole("button", { name: "Meeting actions" }).click();
    await page.getByRole("menuitem", { name: "Delete meeting" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(page).toHaveURL(/\/meetings$/);
    await expect(page.getByTestId("meeting-row").first()).toBeVisible();
    // Leaving the deleted meeting's page must not refetch it (no 404s in the console).
    expect(failed).toEqual([]);
    await page.goto(`/meetings/${id}`);
    await expect(page.getByText("Meeting not found")).toBeVisible();
  });
});
