import { defineConfig } from "@playwright/test";

const PORT = process.env.UPLIFT_PORT || "8796";
const BASE = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 90_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: BASE,
    viewport: { width: 1280, height: 800 },
    trace: "on-first-retry",
  },
  webServer: {
    command: [
      "UPLIFT_MOCK_AGENT=1",
      `UPLIFT_PORT=${PORT}`,
      "UPLIFT_MOCK_DELAY_MS=80",
      "UPLIFT_SESSIONS_DIR=./tests/.e2e-sessions",
      "./.venv/bin/python -m bridge.server --kill-port",
    ].join(" "),
    cwd: __dirname,
    url: `${BASE}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
