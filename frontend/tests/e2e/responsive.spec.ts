import { expect, test } from "@playwright/test";

test.describe("Responsive layout (phone width)", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  async function expectNoHorizontalScroll(page: import("@playwright/test").Page) {
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  }

  test("library fits the screen and navigation moves into a drawer", async ({ page }) => {
    await page.goto("/meetings");
    await expect(page.getByTestId("meeting-row").first()).toBeVisible();
    await expectNoHorizontalScroll(page);
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page.getByRole("link", { name: "Settings" }).click();
    await expect(page).toHaveURL(/\/settings/);
  });

  test("workspace switches between notes and transcript tabs", async ({ page }) => {
    await page.goto("/meetings/1");
    await expect(page.getByTestId("transcript-line").first()).toBeVisible();
    await expectNoHorizontalScroll(page);
    await page.getByRole("tab", { name: "notes" }).click();
    await expect(page.getByTestId("overview")).toBeVisible();
    await expect(page.getByTestId("player")).toBeVisible();
  });
});
