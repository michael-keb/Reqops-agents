import { expect, test } from "@playwright/test";

test.beforeEach(async ({ request }) => {
  await request.post("/api/reset");
});

test.describe("Uplift v5 UI", () => {
  test("health endpoint reports mock agent", async ({ request }) => {
    const res = await request.get("/api/health");
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    expect(body.agent).toBe(true);
    expect(body.mock).toBe(true);
    expect(body.root).toContain("uplift-v5");
  });

  test("loads home page with live terminal", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Uplift/ })).toBeVisible();
    await expect(page.getByPlaceholder("One-line pitch")).toBeVisible();
    await expect(page.locator("#terminal")).toBeVisible();
    await expect(page.locator("#termStatus")).toContainText(/live|connecting/i);
  });

  test("start session streams to terminal", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("One-line pitch").fill("Pet sitting app");
    await page.getByRole("button", { name: "Start session" }).click();

    await expect(page.locator("#terminal")).toContainText("turn 01", { timeout: 15_000 });
    await expect(page.locator("#sessionPanel")).toBeVisible();
    await expect(page.locator("#response")).toContainText("primary user");
  });

  test("submit answer advances to turn 02 in same session", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("One-line pitch").fill("Pet sitting app e2e");
    await page.getByRole("button", { name: "Start session" }).click();
    await expect(page.locator("#meta")).toContainText("turn 01", { timeout: 15_000 });

    await page.getByRole("button", { name: /Individual consumers/ }).click();
    await page.getByRole("button", { name: "Submit" }).click();

    await expect(page.locator("#meta")).toContainText("turn 02", { timeout: 15_000 });
    await expect(page.locator("#response")).toContainText("trust");
    await expect(page.locator("#lastInput")).toContainText("Individual consumers");
  });

  test("empty submit shows error", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("One-line pitch").fill("Empty submit test");
    await page.getByRole("button", { name: "Start session" }).click();
    await expect(page.locator("#sessionPanel")).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "Submit" }).click();
    await expect(page.locator("#error")).toContainText("Enter an answer");
  });

  test("new session returns to pitch panel", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("One-line pitch").fill("New session test");
    await page.getByRole("button", { name: "Start session" }).click();
    await expect(page.locator("#sessionPanel")).toBeVisible({ timeout: 15_000 });

    page.once("dialog", (d) => d.accept());
    await page.getByRole("button", { name: "New session" }).click();
    await expect(page.locator("#startPanel")).toBeVisible();
    await expect(page.locator("#sessionPanel")).toBeHidden();
  });
});
