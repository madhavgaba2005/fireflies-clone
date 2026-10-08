import { expect, test } from "@playwright/test";

const html = (page: import("@playwright/test").Page) => page.locator("html");
const background = (page: import("@playwright/test").Page) =>
  page.evaluate(() => getComputedStyle(document.body).backgroundColor);

test.describe("Dark mode (bonus)", () => {
  test("toggles from the account menu and persists across reloads", async ({ page }) => {
    await page.goto("/meetings");
    await expect(html(page)).not.toHaveClass(/dark/);
    const light = await background(page);

    await page.getByRole("button", { name: "Account menu" }).click();
    await page.getByRole("menuitem", { name: "Dark mode" }).click();
    await expect(html(page)).toHaveClass(/dark/);
    expect(await background(page)).not.toBe(light);

    await page.reload();
    await expect(html(page)).toHaveClass(/dark/);

    await page.getByRole("button", { name: "Account menu" }).click();
    await page.getByRole("menuitem", { name: "Light mode" }).click();
    await expect(html(page)).not.toHaveClass(/dark/);
    expect(await background(page)).toBe(light);
  });

  test("follows the system preference when no choice is stored", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "dark" });
    const page = await context.newPage();
    await page.goto("/meetings");
    await expect(page.locator("html")).toHaveClass(/dark/);
    await context.close();
  });
});
