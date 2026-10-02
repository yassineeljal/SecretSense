import { test, expect } from "@playwright/test";
import baseline from "../../ml/results/baseline.json";
import fresh from "../../ml/results/xgboost.json";

test("all informational routes are navigable, titled, and fit the viewport", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  for (const [label, route, title] of [
    ["How it works", "how-it-works", "A signal you can inspect."],
    ["Benchmarks", "benchmarks", "The tradeoffs, in the open."],
    ["Documentation", "docs", "From checkout to first scan."],
    ["Model card", "model", "A score is another signal."],
    ["Security & privacy", "security", "Keep the input close."],
    ["About", "about", "Make the evidence visible."],
  ]) {
    await page
      .getByRole("navigation", { name: "Project information" })
      .getByRole("link", { name: label, exact: true })
      .click();
    await expect(page).toHaveURL(new RegExp(`/${route}$`));
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    await expect(page).toHaveTitle(/SecretSense/);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  expect(errors).toEqual([]);
});

test("benchmark interaction preserves aggregate evidence and matrix orientation", async ({
  page,
}) => {
  await page.goto("/benchmarks");
  for (const [experiment, metrics, names] of [
    [
      "historical",
      baseline.evaluation.test.metrics,
      ["regex_only", "rules_and_entropy", "candidate_pipeline_model"],
    ],
    [
      "fresh",
      fresh.evaluation.test.metrics,
      [
        "regex_only",
        "rules_and_entropy",
        "random_forest_filter",
        "xgboost_filter",
      ],
    ],
  ] as const) {
    await page.getByLabel("Recorded experiment").selectOption(experiment);
    for (const [index, name] of names.entries()) {
      const metric = (
        metrics as Record<
          string,
          {
            precision: number;
            recall: number;
            f1: number;
            confusion_matrix: number[][];
          }
        >
      )[name];
      await page.getByLabel("Inspect a method").selectOption(String(index));
      await expect(page.locator(".matrix td strong")).toHaveText(
        metric.confusion_matrix.flat().map(String),
      );
      await expect(page.locator(".metric-label strong")).toHaveText(
        [metric.precision, metric.recall, metric.f1].map(
          (value) => `${(value * 100).toFixed(2)}%`,
        ),
      );
    }
  }
  await expect(
    page.getByText(/do not establish real-world detection quality/),
  ).toBeVisible();
});

test("copy command has success and manual fallback feedback", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/docs");
  await page.getByRole("button", { name: "Copy commands" }).first().click();
  await expect(page.getByRole("status").first()).toHaveText("Copied commands.");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain(
    "python -m pip install -e ./core",
  );
  await page.evaluate(() => {
    Object.defineProperty(navigator.clipboard, "writeText", {
      value: () => Promise.reject(new Error("denied")),
    });
  });
  await page.getByRole("button", { name: "Copy commands" }).first().click();
  await expect(page.getByRole("status").first()).toContainText("copy manually");
});
