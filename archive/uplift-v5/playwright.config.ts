import { defineConfig } from "@playwright/test";

const PORT = process.env.UPLIFT_UI_PORT || "8796";
const BASE = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: BASE,
    trace: "on-first-retry",
  },
  webServer: {
    command: `UPLIFT_MOCK_AGENT=1 UPLIFT_UI_PORT=${PORT} UPLIFT_MOCK_DELAY_MS=150 UPLIFT_SESSIONS_DIR=./tests/.e2e-sessions python3 bridge/server.py`,
    cwd: __dirname,
    url: `${BASE}/api/health`,
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
