import { defineConfig } from "@playwright/test";

const PORT = process.env.UPLIFT_PORT || "8797";
const BASE = `http://127.0.0.1:${PORT}`;

/** Real Cursor CLI agent — longer timeouts, no mock. */
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: ["real-smoke.spec.ts"],
  timeout: 600_000,
  expect: { timeout: 180_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report-real" }]],
  use: {
    baseURL: BASE,
    viewport: { width: 1280, height: 800 },
    trace: "retain-on-failure",
  },
  webServer: {
    command: [
      `UPLIFT_PORT=${PORT}`,
      "UPLIFT_AGENT_MODE=headless",
      "UPLIFT_SESSIONS_DIR=./tests/.e2e-real-sessions",
      "./.venv/bin/python -m bridge.server --kill-port",
    ].join(" "),
    cwd: __dirname,
    url: `${BASE}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
