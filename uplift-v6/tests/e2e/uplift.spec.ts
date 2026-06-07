import { expect, test } from "@playwright/test";
import {
  countReflections,
  runTurns,
  terminalText,
  typeInTerminal,
  waitForTurn,
  waitTurnDone,
} from "./helpers";

test.beforeEach(async ({ request }) => {
  await request.post("/api/new-session");
});

test.describe("Uplift v6 terminal UI", () => {
  test("health reports mock mode", async ({ request }) => {
    const res = await request.get("/api/health");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.ok).toBe(true);
    expect(body.mock).toBe(true);
  });

  test("loads terminal-only page with banner", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("brand")).toBeVisible();
    await expect(page.getByTestId("terminal")).toBeVisible();
    await expect(page.locator(".xterm-rows")).toContainText("Uplift v6", { timeout: 10_000 });
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i, { timeout: 10_000 });
  });

  test("start session via terminal streams discovery output", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i);

    await typeInTerminal(page, "Pet sitting app e2e");
    await waitForTurn(page, 1);
    await expect(page.locator(".xterm-rows")).toContainText("## Reflection");
    await expect(page.locator(".xterm-rows")).toContainText("Who is the primary user");
    await waitTurnDone(page, 1);
  });

  test("turn 1 shows reflection once (no duplicate markdown)", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "No duplicate reflection test");
    await waitTurnDone(page, 1);
    expect(await countReflections(page)).toBe(1);
  });

  test("output has no json fences", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "No json output test");
    await waitTurnDone(page, 1);
    const text = await terminalText(page);
    expect(text).not.toMatch(/```json/i);
    expect(text).not.toMatch(/"primary_gap"/);
  });

  test("follow-up message advances to turn 2", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Dog walking app e2e");
    await waitTurnDone(page, 1);
    await typeInTerminal(page, "A) Individual consumers booking directly");
    await waitForTurn(page, 2);
    await expect(page.locator(".xterm-rows")).toContainText("trust");
  });

  test("accepts multiple MCQ picks in one message", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Multi pick test app");
    await waitTurnDone(page, 1);
    await typeInTerminal(
      page,
      "- A) First pick - B) Second pick - C) Third pick"
    );
    await waitForTurn(page, 2);
    await expect(page.locator(".xterm-rows")).not.toContainText("Send one answer per turn");
  });

  test("three-turn chat conversation", async ({ page }) => {
    await page.goto("/");
    await runTurns(page, "Three turn chat e2e", 3);
    await expect(page.locator(".xterm-helper-textarea")).toBeVisible();
  });

  test("ten-turn chat conversation", async ({ page, request }) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await runTurns(page, "Ten turn chat e2e", 10);
    await expect(page.getByTestId("pill-turn")).toContainText("turn 10");
    const state = await request.get("/api/state");
    expect((await state.json()).turn).toBe(10);
    const text = await terminalText(page);
    expect(text).not.toContain("agent exited");
    expect(await countReflections(page)).toBeGreaterThanOrEqual(1);
  });

  test("new session resets terminal and state", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "New session test pitch");
    await waitForTurn(page, 1);

    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: "New session" }).first().click();

    await expect(page.getByTestId("pill-session")).toContainText("no session");
    await expect(page.getByTestId("pill-turn")).toContainText("turn —");
    await expect(page.locator(".xterm-rows")).toContainText("New session — fresh terminal");
  });

  test("/new command in terminal starts fresh session", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Slash new test");
    await waitForTurn(page, 1);

    page.once("dialog", (d) => d.accept());
    await typeInTerminal(page, "/new");

    await expect(page.getByTestId("pill-session")).toContainText("no session");
    await expect(page.locator(".xterm-rows")).toContainText("New session — fresh terminal");
  });

  test("prompt returns after turn completes", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Prompt return test");
    await waitTurnDone(page, 1);
    await expect(page.locator(".xterm-rows")).toContainText("→");
    const input = page.locator(".xterm-helper-textarea");
    await input.pressSequentially("hello", { delay: 10 });
    await expect(page.locator(".xterm-rows")).toContainText("hello");
  });

  test("interrupt button stops busy state", async ({ page }) => {
    await page.goto("/");
    await typeInTerminal(page, "Interrupt test app");
    await expect(page.getByTestId("pill-ws")).toContainText(/agent running|connected/i);
    await page.getByRole("button", { name: "Stop turn" }).click();
    await expect(page.getByTestId("pill-ws")).toContainText(/connected/i, { timeout: 10_000 });
  });
});

test.describe("Bridge persistence (chat-only agent)", () => {
  test("api/start persists response.md via bridge", async ({ request }) => {
    await request.post("/api/new-session");
    const start = await request.post("/api/start", {
      data: { pitch: "Bridge persist e2e" },
    });
    expect(start.ok()).toBeTruthy();
    const body = await start.json();
    expect(body.session_id).toBeTruthy();
    expect(body.turn).toBe(1);
    expect(body.response).toMatch(/## Reflection/);
    expect(body.response).toContain("Who is the primary user");
    expect(body.response).not.toMatch(/```json/i);
  });

  test("trace has validation persist and no edit tools", async ({ request }) => {
    await request.post("/api/new-session");
    await request.post("/api/start", { data: { pitch: "No edit e2e" } });

    const tools = await request.get("/api/trace?kind=tool");
    const toolEntries = (await tools.json()).entries || [];
    for (const e of toolEntries) {
      const tool = (e.data?.tool || "").toLowerCase();
      expect(tool).not.toBe("edit");
      expect(tool).not.toBe("write");
      expect(tool).not.toBe("shell");
    }

    const all = await request.get("/api/trace?limit=500");
    const entries = (await all.json()).entries || [];
    const validation = entries.filter((e: { kind: string }) => e.kind === "validation");
    expect(validation.some((e: { msg: string }) => e.msg.includes("turn artifacts persisted"))).toBeTruthy();
    expect(validation.some((e: { msg: string }) => e.msg.includes("tool policy ok"))).toBeTruthy();
  });

  test("turn 2 via terminal persists second turn on disk", async ({ page, request }) => {
    await page.goto("/");
    await typeInTerminal(page, "Two turn disk e2e");
    await waitForTurn(page, 1);
    await typeInTerminal(page, "A) Individual consumers booking directly");
    await waitForTurn(page, 2);

    const state = await request.get("/api/state");
    const body = await state.json();
    expect(body.turn).toBe(2);
    expect(body.response).toMatch(/trust/i);
    expect(body.response).not.toMatch(/```json/i);
  });

  test("ten turns persist on disk", async ({ page, request }) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await runTurns(page, "Ten turn disk e2e", 10);

    const state = await request.get("/api/state");
    const body = await state.json();
    expect(body.turn).toBe(10);
    expect(body.response).toMatch(/## Reflection/);
  });
});
