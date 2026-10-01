import { test, expect } from "@playwright/test";

const synthetic = () => "gh" + "p_" + "aB3cD4eF5".repeat(4);
test("home, live scan, masking, filters, remediation and clearing", async ({
  page,
}) => {
  const logs: string[] = [];
  page.on("console", (message) => logs.push(message.text()));
  const externalRequests: string[] = [];
  page.on("request", (request) => {
    if (!new URL(request.url()).hostname.match(/^(127\.0\.0\.1|localhost)$/))
      externalRequests.push(request.url());
  });
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Catch the secret",
  );
  await page.getByRole("link", { name: "Try the scanner" }).click();
  const value = synthetic();
  await page
    .getByLabel("Source text")
    .fill(
      `// context-marker\nconst token = "${value}";\n-----BEGIN ${"RSA PRIVATE"} KEY-----`,
    );
  await page.getByRole("button", { name: "Analyze text" }).click();
  await expect(page).toHaveURL(/\/results$/);
  await expect(
    page.getByRole("heading", { name: "GitHub", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("[REDACTED]", { exact: true })).toHaveCount(2);
  expect((await page.content()).includes(value)).toBe(false);
  expect((await page.content()).includes("context-marker")).toBe(false);
  await page.getByLabel("Severity").selectOption("critical");
  await expect(page.locator(".finding")).toHaveCount(1);
  await page.getByLabel("Severity").selectOption("all");
  await page.getByText("Response guidance", { exact: true }).first().click();
  await expect(
    page.getByText(/Revoke the token or application authorization/),
  ).toBeVisible();
  expect(
    await page.evaluate(() => localStorage.length + sessionStorage.length),
  ).toBe(0);
  expect(logs.join(" ").includes(value)).toBe(false);
  expect(externalRequests).toEqual([]);
  await page.getByRole("link", { name: "Scanner", exact: true }).click();
  await expect(page.getByLabel("Source text")).toHaveValue("");
  await page.getByRole("link", { name: "Results", exact: true }).click();
  await expect(page).toHaveURL(/\/results$/);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "A fresh start." }),
  ).toBeVisible();
});

test("text upload and clean result", async ({ page }) => {
  await page.goto("/scan");
  await page.getByLabel("Choose a text file").setInputFiles({
    name: "example.py",
    mimeType: "text/plain",
    buffer: Buffer.from("print(42)"),
  });
  await expect(page.getByLabel("Source text")).toHaveValue("print(42)");
  await page.getByRole("button", { name: "Analyze text" }).click();
  await expect(
    page.getByRole("heading", { name: "No candidates found." }),
  ).toBeVisible();
  await expect(page.getByText(/not a security guarantee/)).toBeVisible();
  await page.getByRole("button", { name: "Clear results" }).click();
  await expect(
    page.getByRole("heading", { name: "A fresh start." }),
  ).toBeVisible();
});

test("rejects oversized and binary files before a request", async ({
  page,
}) => {
  let scans = 0;
  page.on("request", (request) => {
    if (request.url().endsWith("/api/scan")) scans++;
  });
  await page.goto("/scan");
  await expect(
    page.getByRole("button", { name: "Analyze text" }),
  ).toBeDisabled();
  const upload = page.getByLabel("Choose a text file");
  await upload.setInputFiles({
    name: "large.txt",
    mimeType: "text/plain",
    buffer: Buffer.alloc(1_048_577, 65),
  });
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "exceeds 1 MiB",
  );
  await upload.setInputFiles({
    name: "binary.txt",
    mimeType: "text/plain",
    buffer: Buffer.from([0xff, 0x00]),
  });
  await expect(page.locator("main").getByRole("alert")).toContainText("UTF-8");
  expect(scans).toBe(0);
});

test("busy state, safe errors and recovery", async ({ page }) => {
  await page.goto("/scan");
  await page.route("http://127.0.0.1:8000/api/scan", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200));
    await route.fulfill({
      status: 429,
      contentType: "application/json",
      body: JSON.stringify({ detail: synthetic() }),
    });
  });
  await page.getByLabel("Source text").fill("print(42)");
  await page.getByRole("button", { name: "Analyze text" }).click();
  await expect(page.getByRole("button", { name: "Scanning" })).toBeDisabled();
  await expect(page.getByLabel("Source text")).toHaveValue("");
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Wait a minute",
  );
  expect((await page.content()).includes(synthetic())).toBe(false);
  await page.unroute("http://127.0.0.1:8000/api/scan");
  await page.getByLabel("Source text").fill("print(42)");
  await page.getByRole("button", { name: "Analyze text" }).click();
  await expect(
    page.getByRole("heading", { name: "No candidates found." }),
  ).toBeVisible();
});

test("unavailable API, timeout and incomplete responses never look clean", async ({
  page,
}) => {
  await page.goto("/scan");
  for (const status of [504, 422, 500]) {
    await page.route("http://127.0.0.1:8000/api/scan", (route) =>
      route.fulfill({ status, body: "{}" }),
    );
    await page.getByLabel("Source text").fill("print(42)");
    await page.getByRole("button", { name: "Analyze text" }).click();
    await expect(page.locator("main").getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/scan$/);
    await page.unroute("http://127.0.0.1:8000/api/scan");
  }
  await page.route("http://127.0.0.1:8000/api/scan", (route) => route.abort());
  await page.getByLabel("Source text").fill("print(42)");
  await page.getByRole("button", { name: "Analyze text" }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "local API",
  );
});

test("responsive page has no horizontal overflow and supports reduced motion", async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.locator(".scan-line")).toHaveCSS("animation-name", "none");
  await page.goto("/scan");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
