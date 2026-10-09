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

  test("a fresh visit is light even when the OS prefers dark", async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: "dark" });
    const page = await context.newPage();
    await page.goto("/meetings");
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    expect(await page.evaluate(() => localStorage.getItem("lumen-theme"))).toBeNull(); // nothing forced
    await context.close();
  });

  test("settings offer System, Light and Dark; System follows the OS live", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await page.goto("/settings?tab=appearance");
    const option = (name: string) => page.getByRole("radio", { name: new RegExp(`^${name}`) });
    await expect(option("Light")).toHaveAttribute("aria-checked", "true"); // the default

    await option("Dark").click();
    await expect(html(page)).toHaveClass(/dark/);
    await page.reload();
    await expect(option("Dark")).toHaveAttribute("aria-checked", "true");
    await expect(html(page)).toHaveClass(/dark/);

    await option("Light").click();
    await expect(html(page)).not.toHaveClass(/dark/);
    await page.emulateMedia({ colorScheme: "dark" });
    await expect(html(page)).not.toHaveClass(/dark/); // an explicit choice ignores the OS

    await option("System").click();
    await expect(html(page)).toHaveClass(/dark/); // OS is dark now
    await page.emulateMedia({ colorScheme: "light" });
    await expect(html(page)).not.toHaveClass(/dark/); // and it follows changes live
    await page.reload();
    await expect(option("System")).toHaveAttribute("aria-checked", "true");
  });
});
