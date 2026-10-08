import { expect, test } from "@playwright/test";

import { createMeetingViaApi } from "./helpers";

test.describe("Action items", () => {
  test("add, edit, complete, uncomplete and delete — all persisted", async ({ page }) => {
    const id = await createMeetingViaApi(page, {
      title: "E2E action items",
      participants: [{ name: "Ivy Chen" }, { name: "Leo Grant" }],
    });
    await page.goto(`/meetings/${id}`);
    const items = page.getByTestId("action-item");
    await expect(page.getByText("No action items yet")).toBeVisible();

    // Add
    await page.getByRole("button", { name: "Add", exact: true }).click();
    const form = page.getByRole("form", { name: "New action item" });
    await form.getByLabel("Action item").fill("Draft the Q1 hiring plan");
    await form.getByLabel("Assignee").selectOption({ label: "Ivy Chen" });
    await form.getByLabel("Due date").fill("2030-01-15");
    await form.getByRole("button", { name: "Add" }).click();
    await expect(page.getByText("Action item added")).toBeVisible();
    await expect(items).toHaveCount(1);
    await expect(items.first()).toContainText("Draft the Q1 hiring plan");
    await expect(page.getByRole("region", { name: "Action items" })).toContainText("Ivy Chen");

    // Edit
    await items.first().hover();
    await page.getByRole("button", { name: "Edit “Draft the Q1 hiring plan”" }).click();
    const editForm = page.getByRole("form", { name: "Edit action item" });
    await editForm.getByLabel("Action item").fill("Draft and share the Q1 hiring plan");
    await editForm.getByLabel("Assignee").selectOption({ label: "Leo Grant" });
    await editForm.getByRole("button", { name: "Save" }).click();
    await expect(items.first()).toContainText("Draft and share the Q1 hiring plan");

    // Complete → persists across reload
    await page
      .getByRole("checkbox", { name: /Mark “Draft and share the Q1 hiring plan” as done/ })
      .check();
    await expect(page.getByText("0 open · 1 done")).toBeVisible();
    await page.reload();
    const checkbox = page.getByRole("checkbox", { name: /Draft and share the Q1 hiring plan/ });
    await expect(checkbox).toBeChecked();
    await expect(page.getByRole("region", { name: "Action items" })).toContainText("Leo Grant");

    // Uncomplete
    await checkbox.uncheck();
    await expect(page.getByText("1 open · 0 done")).toBeVisible();

    // Delete → persists across reload
    await items.first().hover();
    await page.getByRole("button", { name: "Delete “Draft and share the Q1 hiring plan”" }).click();
    await expect(page.getByText("Action item deleted")).toBeVisible();
    await page.reload();
    await expect(page.getByText("No action items yet")).toBeVisible();
  });

  test("seeded AI action items are grouped by assignee", async ({ page }) => {
    await page.goto("/meetings");
    await page.getByRole("link", { name: "Discovery Call — Brightline Logistics" }).click();
    const section = page.getByRole("region", { name: "Action items" });
    await expect(section).toContainText("Marcus Johnson");
    await expect(section).toContainText("Priya Sharma");
    await expect(section.getByTitle("Extracted by AI").first()).toBeVisible();
  });
});
