import { expect, test } from "@playwright/test";
import {
  attachLatencyReport,
  assertComponentsHealthy,
  assertNoUiErrors,
  getBridgeDiagnostics,
  maxTurnSeconds,
  runTurnsWithLatency,
  typeInTerminal,
  waitTurnDone,
  waitForTurn,
} from "./helpers";

test.beforeEach(async ({ request }) => {
  await request.post("/api/new-session");
});

test.describe("Multi-turn latency", () => {
  test("five-turn playout records per-turn bridge latency", async ({ page, request }, testInfo) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i);

    const report = await runTurnsWithLatency(page, request, "Latency playout e2e", 5);
    await attachLatencyReport(testInfo, report);

    expect(report.turn_latencies).toHaveLength(5);
    const maxS = maxTurnSeconds(report.mock);
    for (const t of report.turn_latencies) {
      expect(t.bridge_elapsed_s, `turn ${t.turn} missing bridge elapsed_s`).not.toBeNull();
      expect(t.bridge_elapsed_s!, `turn ${t.turn} too slow`).toBeLessThan(maxS);
      expect(t.ui_wall_ms!, `turn ${t.turn} ui wall`).toBeGreaterThan(0);
    }

    await assertNoUiErrors(page);
    await assertComponentsHealthy(page);

    const bridge = await getBridgeDiagnostics(request);
    expect(bridge.turn).toBe(5);
    expect(bridge.trace_errors || []).toHaveLength(0);
  });

  test("ten-turn playout latency summary", async ({ page, request }, testInfo) => {
    test.setTimeout(180_000);
    await page.goto("/");

    const report = await runTurnsWithLatency(page, request, "Ten turn latency e2e", 10);
    await attachLatencyReport(testInfo, report);

    expect(report.turn_latencies).toHaveLength(10);
    expect(report.avg_bridge_s).toBeGreaterThan(0);
    expect(report.max_bridge_s).toBeLessThan(maxTurnSeconds(report.mock));

    await assertNoUiErrors(page);
  });
});

test.describe("Bridge diagnostics latency", () => {
  test("bootstrap turn exposes elapsed_s in /api/diagnostics", async ({ request }) => {
    await request.post("/api/new-session");
    const start = await request.post("/api/start", {
      data: { pitch: "API bootstrap latency e2e" },
    });
    expect(start.ok()).toBeTruthy();

    const diag = await getBridgeDiagnostics(request);
    expect(diag.turn_latencies?.length).toBeGreaterThanOrEqual(1);
    expect(diag.turn_latencies[0].elapsed_s).toBeGreaterThan(0);
    expect(diag.turn).toBe(1);
    expect(diag.trace_errors || []).toHaveLength(0);
  });
});

test.describe("Latency regression guards", () => {
  test("turn 1 latency is recorded in UI diagnostics", async ({ page, request }) => {
    await page.goto("/");
    await typeInTerminal(page, "UI latency diag test");
    await waitForTurn(page, 1);
    await waitTurnDone(page, 1);

    const ui = await page.evaluate(() => (window as unknown as { __upliftDiag: { turnLatencies: Array<{ turn: number; elapsed_s: number; source: string }> } }).__upliftDiag);
    expect(ui.turnLatencies.length).toBeGreaterThan(0);
    const traceRow = ui.turnLatencies.find((t) => t.turn === 1 && t.source === "trace");
    expect(traceRow?.elapsed_s).toBeGreaterThan(0);

    const bridge = await getBridgeDiagnostics(request);
    const bridgeRow = bridge.turn_latencies.find((t: { turn: number }) => t.turn === 1);
    expect(bridgeRow?.elapsed_s).toBeGreaterThan(0);
  });
});
