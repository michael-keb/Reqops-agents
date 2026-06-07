import { expect, type APIRequestContext, type Page, type TestInfo } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

export async function typeInTerminal(page: Page, text: string) {
  const input = page.locator(".xterm-helper-textarea");
  await input.click();
  await input.pressSequentially(text, { delay: 15 });
  await input.press("Enter");
}

export async function waitForTurn(page: Page, turn: number, timeout?: number) {
  const ms = timeout ?? turnTimeoutMs();
  await expect(page.getByTestId("pill-turn")).toContainText(`turn ${turn}`, { timeout: ms });
}

export async function waitTurnDone(page: Page, turn: number, timeout?: number) {
  const ms = timeout ?? turnTimeoutMs();
  await expect(page.locator(".xterm-rows")).toContainText(`turn ${turn} done`, { timeout: ms });
}

function turnTimeoutMs(): number {
  if (process.env.UPLIFT_E2E_REAL === "1" || process.env.npm_lifecycle_event === "test:e2e:real") {
    return 180_000;
  }
  return 20_000;
}

export async function terminalText(page: Page) {
  return page.locator(".xterm-rows").innerText();
}

export async function countReflections(page: Page) {
  const text = await terminalText(page);
  return (text.match(/## Reflection/g) || []).length;
}

/** Generic MCQ answers for multi-turn latency / smoke runs. */
export const GENERIC_ANSWERS = [
  "A) Individual consumers booking directly",
  "B) Insurance or guarantee from the platform",
  "C) Starts inside existing social trust (friends/referrals)",
  "D) Something else — spell out the trust mechanism",
  "A) Reviews and identity verification on both sides",
];

export const MCQ_ANSWERS = GENERIC_ANSWERS;

export type TurnLatency = {
  turn: number;
  bridge_elapsed_s: number | null;
  ui_wall_ms: number | null;
  reply: string | null;
};

export type LatencyReport = {
  pitch: string;
  turns: number;
  mock: boolean;
  turn_latencies: TurnLatency[];
  total_bridge_compute_s: number;
  total_ui_wall_ms: number;
  avg_bridge_s: number;
  max_bridge_s: number;
  ui_errors: UiDiagnostics["errors"];
  components: UiDiagnostics["components"];
};

export type UiDiagnostics = {
  errors: Array<{ ts: string; source: string; message: string; detail?: unknown }>;
  turnLatencies: Array<{ turn: number; elapsed_s: number; source: string }>;
  components: Record<string, string>;
};

export async function getUiDiagnostics(page: Page): Promise<UiDiagnostics> {
  const raw = await page.getByTestId("ui-diagnostics").textContent();
  if (!raw) {
    return { errors: [], turnLatencies: [], components: {} };
  }
  return JSON.parse(raw) as UiDiagnostics;
}

export async function getBridgeDiagnostics(request: APIRequestContext) {
  const res = await request.get("/api/diagnostics");
  expect(res.ok()).toBeTruthy();
  return res.json();
}

export async function assertNoUiErrors(page: Page) {
  const diag = await getUiDiagnostics(page);
  expect(diag.errors, `UI errors: ${JSON.stringify(diag.errors, null, 2)}`).toHaveLength(0);
  await expect(page.getByTestId("pill-errors")).toBeHidden();
}

export async function assertComponentsHealthy(page: Page) {
  const diag = await getUiDiagnostics(page);
  const c = diag.components;
  expect(c.ws, "WebSocket should be connected").toMatch(/connected/);
  expect(c.trace, "Trace SSE should be connected").toMatch(/connected/);
  expect(c.terminal, "Terminal should be ready").toBe("ready");
  expect(c.api, "API should be ok").toBe("ok");
  expect(c.turn, "Turn should not be stuck running").not.toBe("running");
}

export async function assertHeaderControls(page: Page) {
  await expect(page.getByTestId("brand")).toBeVisible();
  await expect(page.getByTestId("pill-ws")).toBeVisible();
  await expect(page.getByTestId("pill-session")).toBeVisible();
  await expect(page.getByTestId("pill-turn")).toBeVisible();
  await expect(page.getByTestId("terminal")).toBeVisible();
  await expect(page.getByRole("button", { name: "Stop turn" })).toBeVisible();
  await expect(page.getByRole("button", { name: "New session" }).first()).toBeVisible();
  await expect(page.locator(".xterm-helper-textarea")).toBeVisible();
}

export async function runTurns(page: Page, pitch: string, turns: number) {
  await typeInTerminal(page, pitch);
  await waitForTurn(page, 1);
  await waitTurnDone(page, 1);

  for (let t = 2; t <= turns; t++) {
    await typeInTerminal(page, GENERIC_ANSWERS[(t - 2) % GENERIC_ANSWERS.length]);
    await waitForTurn(page, t);
    await waitTurnDone(page, t);
  }
}

export async function runTurnsWithLatency(
  page: Page,
  request: APIRequestContext,
  pitch: string,
  turns: number
): Promise<LatencyReport> {
  const health = await request.get("/api/health").then((r) => r.json());
  const records: TurnLatency[] = [];

  const t0 = Date.now();
  await typeInTerminal(page, pitch);
  await waitForTurn(page, 1);
  await waitTurnDone(page, 1);
  records.push(await collectTurnLatency(page, request, 1, null, Date.now() - t0));

  for (let t = 2; t <= turns; t++) {
    const reply = GENERIC_ANSWERS[(t - 2) % GENERIC_ANSWERS.length];
    const start = Date.now();
    await typeInTerminal(page, reply);
    await waitForTurn(page, t);
    await waitTurnDone(page, t);
    records.push(await collectTurnLatency(page, request, t, reply, Date.now() - start));
  }

  const bridge = await getBridgeDiagnostics(request);
  const ui = await getUiDiagnostics(page);
  const bridgeTimes = records.map((r) => r.bridge_elapsed_s).filter((v): v is number => v != null);
  const totalBridge = bridgeTimes.reduce((a, b) => a + b, 0);

  return {
    pitch,
    turns,
    mock: Boolean(health.mock),
    turn_latencies: records,
    total_bridge_compute_s: bridge.total_compute_s ?? totalBridge,
    total_ui_wall_ms: records.reduce((a, r) => a + (r.ui_wall_ms ?? 0), 0),
    avg_bridge_s: bridgeTimes.length ? totalBridge / bridgeTimes.length : 0,
    max_bridge_s: bridgeTimes.length ? Math.max(...bridgeTimes) : 0,
    ui_errors: ui.errors,
    components: ui.components,
  };
}

async function collectTurnLatency(
  page: Page,
  request: APIRequestContext,
  turn: number,
  reply: string | null,
  uiWallMs: number
): Promise<TurnLatency> {
  const bridge = await getBridgeDiagnostics(request);
  const row = (bridge.turn_latencies || []).find((t: { turn: number }) => t.turn === turn);
  return {
    turn,
    bridge_elapsed_s: row?.elapsed_s ?? null,
    ui_wall_ms: uiWallMs,
    reply,
  };
}

export function maxTurnSeconds(mock: boolean): number {
  if (process.env.UPLIFT_E2E_REAL === "1") return 120;
  return mock ? 5 : 30;
}

export async function attachLatencyReport(testInfo: TestInfo, report: LatencyReport) {
  const dir = path.join(process.cwd(), "test-results");
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, "latency-report.json");
  fs.writeFileSync(file, JSON.stringify(report, null, 2));
  await testInfo.attach("latency-report", {
    body: JSON.stringify(report, null, 2),
    contentType: "application/json",
  });
  console.log("\n--- latency report ---");
  for (const t of report.turn_latencies) {
    console.log(
      `  turn ${t.turn}: bridge ${t.bridge_elapsed_s ?? "?"}s  ui wall ${t.ui_wall_ms ?? "?"}ms` +
        (t.reply ? `  ← ${t.reply.slice(0, 40)}…` : "  ← bootstrap")
    );
  }
  console.log(
    `  total bridge: ${report.total_bridge_compute_s.toFixed(2)}s  avg: ${report.avg_bridge_s.toFixed(2)}s  max: ${report.max_bridge_s.toFixed(2)}s`
  );
  console.log(`  total ui wall: ${report.total_ui_wall_ms}ms\n`);
}
