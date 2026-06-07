import { expect, test } from "@playwright/test";
import {
  assertComponentsHealthy,
  assertHeaderControls,
  assertNoUiErrors,
  getUiDiagnostics,
  runTurns,
  terminalText,
  typeInTerminal,
  waitForTurn,
  waitTurnDone,
} from "./helpers";

test.beforeEach(async ({ request }) => {
  await request.post("/api/new-session");
});

test.describe("UI component health", () => {
  test("all header controls render and connect", async ({ page }) => {
    await page.goto("/");
    await assertHeaderControls(page);
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i, { timeout: 10_000 });
    await expect(page.locator("#mode-tag")).not.toBeEmpty();

    const diag = await getUiDiagnostics(page);
    expect(diag.components.ws).toBe("connected");
    expect(diag.components.trace).toBe("connected");
    expect(diag.components.terminal).toBe("ready");
    await assertNoUiErrors(page);
  });

  test("busy state toggles during turn", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Busy state test app");
    await expect(page.getByTestId("pill-ws")).toContainText(/agent running|connected/i);
    await expect(page.getByRole("button", { name: "Stop turn" })).toBeEnabled();

    await waitTurnDone(page, 1);
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i);
    await expect(page.getByRole("button", { name: "Stop turn" })).toBeDisabled();

    const diag = await getUiDiagnostics(page);
    expect(diag.components.turn).toBe("idle");
    await assertNoUiErrors(page);
  });

  test("session pill updates through three turns", async ({ page }) => {
    await page.goto("/");
    await runTurns(page, "UI health three turn", 3);

    await expect(page.getByTestId("pill-session")).not.toContainText("no session");
    await expect(page.getByTestId("pill-turn")).toContainText("turn 3");
    await assertComponentsHealthy(page);
    await assertNoUiErrors(page);
  });

  test("terminal prompt returns after each turn", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Prompt health test");
    await waitTurnDone(page, 1);
    await expect(page.locator(".xterm-rows")).toContainText("→");

    const input = page.locator(".xterm-helper-textarea");
    await input.pressSequentially("ok", { delay: 10 });
    await expect(page.locator(".xterm-rows")).toContainText("ok");
  });

  test("clear terminal preserves session", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Clear terminal test");
    await waitForTurn(page, 1);

    await page.getByRole("button", { name: "Clear" }).click();
    await expect(page.locator(".xterm-rows")).toContainText("Uplift v6");
    await expect(page.getByTestId("pill-session")).not.toContainText("no session");
    await assertNoUiErrors(page);
  });

  test("new session resets pills without UI errors", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Reset health test");
    await waitForTurn(page, 1);

    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: "New session" }).first().click();

    await expect(page.getByTestId("pill-session")).toContainText("no session");
    await expect(page.getByTestId("pill-turn")).toContainText("turn —");
    await expect(page.locator(".xterm-rows")).toContainText("New session — fresh terminal");

    const diag = await getUiDiagnostics(page);
    expect(diag.components.session).toBe("none");
    await assertNoUiErrors(page);
  });

  test("five-turn playout has no terminal error patterns", async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await runTurns(page, "Five turn UI health", 5);

    const text = await terminalText(page);
    expect(text).not.toMatch(/agent exited/i);
    expect(text).not.toMatch(/^Error:/im);
    expect(text).not.toMatch(/turn .* failed/i);
    expect(text).not.toMatch(/WebSocket disconnected/i);

    await assertNoUiErrors(page);
    await assertComponentsHealthy(page);
    await expect(page.getByTestId("pill-errors")).toBeHidden();
  });

  test("diagnostics JSON stays in sync with component state", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i);

    const diag = await getUiDiagnostics(page);
    expect(Object.keys(diag.components)).toEqual(
      expect.arrayContaining(["ws", "trace", "terminal", "session", "turn", "api"])
    );
    expect(diag.errors).toEqual([]);
    expect(await page.getByTestId("ui-diagnostics").textContent()).toBeTruthy();
  });
});

test.describe("UI error tracing", () => {
  test("multi-line answer forwards to agent without UI block", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Error trace MCQ test");
    await waitTurnDone(page, 1);

    await typeInTerminal(page, "- A) First - B) Second - C) Third");
    await waitForTurn(page, 2);
    await expect(page.locator(".xterm-rows")).not.toContainText("Send one answer per turn");
    await assertNoUiErrors(page);
  });

  test("forced mock failure surfaces in diagnostics", async ({ page, request }) => {
    // Requires UPLIFT_MOCK_FAIL_TURN — skip unless configured
    test.skip(!process.env.UPLIFT_MOCK_FAIL_TURN, "Set UPLIFT_MOCK_FAIL_TURN to test failure path");

    await page.goto("/");
    await typeInTerminal(page, "Forced fail test");
    await expect(page.locator(".xterm-rows")).toContainText(/failed|exited/i, { timeout: 15_000 });

    const diag = await getUiDiagnostics(page);
    expect(diag.errors.length).toBeGreaterThan(0);
    await expect(page.getByTestId("pill-errors")).toBeVisible();
  });
});
