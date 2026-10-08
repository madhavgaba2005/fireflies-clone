import { expect, test } from "@playwright/test";

test("home redirects to the meetings library", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/meetings$/);
  await expect(page.getByRole("heading", { name: "Meetings" })).toBeVisible();
});

test("settings route is reachable", async ({ page }) => {
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible();
});
