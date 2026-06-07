import { expect, test } from "@playwright/test";
import {
  assertComponentsHealthy,
  assertNoUiErrors,
  getBridgeDiagnostics,
  getUiDiagnostics,
  typeInTerminal,
  waitForTurn,
  waitTurnDone,
} from "./helpers";

const REAL = process.env.UPLIFT_E2E_REAL === "1" || process.env.npm_lifecycle_event === "test:e2e:real";

test.describe.configure({ mode: "serial" });

test.beforeEach(async ({ request }) => {
  test.skip(!REAL, "Real-agent e2e — run via npm run test:e2e:real");
  await request.post("/api/new-session");
});

test.describe("Real agent smoke", () => {
  test("three-turn discovery with updated bootstrap", async ({ page, request }) => {
    test.setTimeout(600_000);
    await page.goto("/");
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i);

    const t0 = Date.now();
    await typeInTerminal(page, "pet sitting app real e2e");
    await waitForTurn(page, 1);
    await waitTurnDone(page, 1);
    const turn1Ms = Date.now() - t0;

    await expect(page.locator(".xterm-rows")).toContainText("## Reflection");
    await expect(page.locator(".xterm-rows")).toContainText("Questions");

    const diag1 = await getBridgeDiagnostics(request);
    expect(diag1.mock).toBeFalsy();
    expect(diag1.turn).toBe(1);
    expect(diag1.turn_latencies?.[0]?.elapsed_s).toBeGreaterThan(1);

    const t1 = Date.now();
    await typeInTerminal(page, "Q1-A");
    await waitForTurn(page, 2);
    await waitTurnDone(page, 2);
    const turn2Ms = Date.now() - t1;

    const t2 = Date.now();
    await typeInTerminal(page, "Q2-B");
    await waitForTurn(page, 3);
    await waitTurnDone(page, 3);
    const turn3Ms = Date.now() - t2;

    const diag = await getBridgeDiagnostics(request);
    expect(diag.turn).toBe(3);
    expect(diag.turn_latencies?.length).toBeGreaterThanOrEqual(3);

    await assertNoUiErrors(page);
    await assertComponentsHealthy(page);

    const ui = await getUiDiagnostics(page);
    expect(ui.errors).toHaveLength(0);

    console.log("\n--- real agent timings (ui wall) ---");
    console.log(`  turn 1: ${(turn1Ms / 1000).toFixed(2)}s`);
    console.log(`  turn 2: ${(turn2Ms / 1000).toFixed(2)}s`);
    console.log(`  turn 3: ${(turn3Ms / 1000).toFixed(2)}s`);
    for (const row of diag.turn_latencies || []) {
      console.log(`  bridge turn ${row.turn}: ${row.elapsed_s}s`);
    }
    console.log("");
  });
});
