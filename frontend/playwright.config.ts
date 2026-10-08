import { defineConfig, devices } from "@playwright/test";

// End-to-end tests run against the REAL stack on dedicated ports (so they never touch dev data):
//   AI service      :8101  PROCESSING_MODE=http (the fallback transport — no broker needed)
//   Meeting Service :8100  fresh SQLite file, reset + seeded on every run
//   Frontend        :3100  production build pointing at :8100
// The Kafka transport is covered separately by `pytest -m kafka` (see docs/TESTING.md).
const isWindows = process.platform === "win32";
const python =
  process.env.E2E_PYTHON ?? (isWindows ? ".venv\\Scripts\\python.exe" : ".venv/bin/python");
const TOKEN = "e2e-internal-token";
const API = "http://localhost:8100";
const WEB = "http://localhost:3100";

export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: false,
  workers: 1, // specs share one seeded database; serial runs keep them deterministic
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: { baseURL: WEB, trace: "retain-on-failure", screenshot: "only-on-failure" },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } },
    },
  ],
  webServer: [
    {
      name: "ai-service",
      cwd: "../backend/ai-service",
      command: `${python} -m uvicorn app.main:create_app --factory --port 8101`,
      url: "http://localhost:8101/health",
      env: { PROCESSING_MODE: "http", INTERNAL_API_TOKEN: TOKEN, RETRY_BACKOFF_SECONDS: "0" },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      name: "meeting-service",
      cwd: "../backend/meeting-service",
      command: `${python} -m app.seed --reset && ${python} -m uvicorn app.main:create_app --factory --port 8100`,
      url: `${API}/health/ready`,
      env: {
        DATABASE_URL: "sqlite:///./data/e2e.db",
        PROCESSING_MODE: "http",
        AI_SERVICE_URL: "http://localhost:8101",
        INTERNAL_API_TOKEN: TOKEN,
        CORS_ORIGINS: WEB,
        OUTBOX_POLL_INTERVAL: "0.3",
      },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      name: "frontend",
      command: "npm run build && npm run start -- --port 3100",
      url: WEB,
      env: { NEXT_PUBLIC_API_URL: API },
      reuseExistingServer: false,
      timeout: 240_000,
    },
  ],
});
