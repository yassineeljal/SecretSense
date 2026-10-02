import { test, expect } from "@playwright/test";
test("portfolio offers local setup and never accepts scan input or contacts an API", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).origin !== "http://127.0.0.1:3000")
      requests.push(request.url());
  });
  const response = await page.goto("/");
  expect(response?.headers()["content-security-policy"]).not.toContain(":8000");
  await page.getByRole("link", { name: "Run locally" }).click();
  await expect(page).toHaveURL(/\/docs$/);
  await page.getByRole("link", { name: "Scanner", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Scanning stays local." }),
  ).toBeVisible();
  await expect(page.locator("textarea, input[type=file], form")).toHaveCount(0);
  await page.getByRole("link", { name: "Set up SecretSense" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "checkout",
  );
  expect(requests).toEqual([]);
});
