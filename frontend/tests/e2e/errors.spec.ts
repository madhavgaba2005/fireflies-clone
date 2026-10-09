import { expect, test } from "@playwright/test";

import { API } from "./helpers";

test.describe("Error and loading states", () => {
  test("API unavailable: the library shows an error with a working retry", async ({ page }) => {
    let fail = true;
    await page.route(`${API}/api/meetings?**`, (route) =>
      fail ? route.abort() : route.continue(),
    );
    await page.goto("/meetings");
    await expect(page.getByText("Couldn't load meetings")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Can't reach the server/)).toBeVisible();
    fail = false;
    await page.getByRole("button", { name: "Try again" }).click();
    await expect(page.getByTestId("meeting-row").first()).toBeVisible();
  });

  test("failed delete shows an error toast and keeps the meeting", async ({ page }) => {
    await page.route(`${API}/api/meetings/*`, (route) =>
      route.request().method() === "DELETE"
        ? route.fulfill({
            status: 500,
            contentType: "application/json",
            body: JSON.stringify({
              error: { code: "internal_error", message: "An unexpected error occurred." },
            }),
          })
        : route.continue(),
    );
    await page.goto("/meetings");
    await page.getByRole("button", { name: "Actions for Q1 Planning Kickoff" }).click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect(page.getByText("Couldn't delete the meeting")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("link", { name: "Q1 Planning Kickoff" })).toBeVisible();
  });

  test("failed action-item toggle rolls back the optimistic checkbox", async ({ page }) => {
    await page.route(`${API}/api/action-items/*`, (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: { code: "x", message: "Server error" } }),
      }),
    );
    await page.goto("/meetings");
    await page.getByRole("link", { name: "Weekly Product Sync" }).click();
    await expect(
      page.getByRole("heading", { name: "Weekly Product Sync", level: 1 }),
    ).toBeVisible();
    // Target an action item's checkbox: the library also has checkboxes (row selection).
    const checkbox = page.getByTestId("action-item").first().getByRole("checkbox");
    const before = await checkbox.isChecked();
    await checkbox.click();
    await expect(page.getByText("Couldn't update the action item")).toBeVisible();
    await expect(checkbox).toBeChecked({ checked: before });
  });

  test("summary generation failure shows the reason and a retry", async ({ page }) => {
    await page.route(`${API}/api/meetings/1`, async (route) => {
      const response = await route.fetch();
      const meeting = await response.json();
      await route.fulfill({
        response,
        json: {
          ...meeting,
          processing_status: "failed",
          processing_error: "Model timed out after 3 attempts",
        },
      });
    });
    await page.goto("/meetings/1");
    await expect(page.getByText("Notes couldn’t be generated")).toBeVisible();
    await expect(page.getByText("Model timed out after 3 attempts")).toBeVisible();
    await expect(page.getByRole("button", { name: "Retry" })).toBeVisible();
  });
});
