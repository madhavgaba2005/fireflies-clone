import { expect, type Page } from "@playwright/test";

export const API = "http://localhost:8100";

/** Creates a meeting through the API (fast setup for tests that aren't about creation). */
export async function createMeetingViaApi(
  page: Page,
  body: { title: string; transcript_text?: string; participants?: { name: string }[] },
): Promise<number> {
  const response = await page.request.post(`${API}/api/meetings`, {
    data: { meeting_date: new Date().toISOString(), source: "paste", ...body },
  });
  expect(response.status()).toBe(201);
  return (await response.json()).id;
}

export async function playerTimeMs(page: Page): Promise<number> {
  return Number(await page.getByRole("slider", { name: "Seek" }).inputValue());
}

export function activeLine(page: Page) {
  return page.locator('[data-testid="transcript-line"][data-active]');
}

export const SHORT_TRANSCRIPT = [
  "[00:00] Dana Fox: Let's review the onboarding launch plan for next month.",
  "[00:12] Omar Reyes: The checkout flow still fails for annual plans.",
  "[00:25] Dana Fox: Omar, can you fix the annual checkout before Friday?",
  "[00:34] Omar Reyes: Yes. I'll fix the annual plan checkout and add regression tests.",
].join("\n");
