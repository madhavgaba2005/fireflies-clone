import { expect, test } from "@playwright/test";

import { activeLine, playerTimeMs } from "./helpers";

test.describe("Global search (bonus)", () => {
  test("finds transcript moments across meetings and deep-links to them", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByLabel("Search meetings").fill("webhook");
    const results = page.getByRole("region", { name: "Search results" });
    await expect(results).toContainText("Engineering Sprint 14 Review");
    await expect(results).toContainText("Discovery Call — Brightline Logistics");
    await expect(results.locator("mark").first()).toHaveText(/webhook/i);

    const hit = results
      .getByTestId("search-hit")
      .filter({ hasText: "Arjun Mehta" })
      .filter({ hasText: "incident" })
      .first();
    const href = (await hit.getAttribute("href"))!;
    const startMs = Number(new URL(href, "http://x").searchParams.get("t"));
    await hit.click();

    await expect(page).toHaveURL(/\/meetings\/\d+\?t=\d+&find=webhook/);
    await expect(page.getByLabel("Find in transcript")).toHaveValue("webhook");
    // The seek slider snaps to 100 ms steps.
    await expect.poll(async () => Math.abs((await playerTimeMs(page)) - startMs)).toBeLessThan(100);
    await expect(activeLine(page)).toContainText("incident");
    await expect(page.locator("mark[data-current-match]")).toBeInViewport();
  });

  test("says when nothing matches, and Enter falls back to the library", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByLabel("Search meetings").fill("kubernetes");
    await expect(page.getByRole("region", { name: "Search results" })).toContainText(
      "Nothing matches",
    );
    await page.getByLabel("Search meetings").press("Enter");
    await expect(page).toHaveURL(/\/meetings\?q=kubernetes/);
    await expect(page.getByText("No meetings match your filters")).toBeVisible();
  });
});
