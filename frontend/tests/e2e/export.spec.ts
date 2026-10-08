import { readFile } from "node:fs/promises";

import { expect, test } from "@playwright/test";

test.describe("Export (bonus)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("link", { name: "Weekly Product Sync" }).click();
    await expect(
      page.getByRole("heading", { name: "Weekly Product Sync", level: 1 }),
    ).toBeVisible();
    await page.getByRole("button", { name: "Meeting actions" }).click();
    await page.getByRole("menuitem", { name: "Download" }).click();
  });

  test("downloads the transcript as text with timestamps and speakers", async ({ page }) => {
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      page.getByRole("dialog").getByRole("button", { name: "Download" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("weekly-product-sync-transcript.txt");
    const text = await readFile((await download.path())!, "utf-8");
    expect(text.startsWith("Weekly Product Sync\n")).toBe(true);
    expect(text).toContain("[00:00] Priya Sharma:");
    await expect(page.getByText("Download started")).toBeVisible();
  });

  test("downloads the AI notes as Markdown", async ({ page }) => {
    const dialog = page.getByRole("dialog");
    await dialog.getByText("AI notes").click();
    await dialog.getByText("Markdown (.md)").click();
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      dialog.getByRole("button", { name: "Download" }).click(),
    ]);
    expect(download.suggestedFilename()).toBe("weekly-product-sync-notes.md");
    const md = await readFile((await download.path())!, "utf-8");
    expect(md).toContain("# Weekly Product Sync");
    expect(md).toContain("## Overview");
    expect(md).toMatch(/- \[[ x]\] /);
  });
});
