import { defineConfig } from "vitest/config";

// Unit tests for pure logic in lib/ and hooks/ (sync, search, API client).
// User-facing workflows are covered by Playwright in tests/e2e.
export default defineConfig({
  test: {
    include: ["lib/**/*.test.ts", "hooks/**/*.test.ts"],
    environment: "node",
  },
});
