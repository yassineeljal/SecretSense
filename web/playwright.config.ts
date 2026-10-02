import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  testIgnore: "portfolio.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["iPhone 13"], defaultBrowserType: "chromium" },
    },
  ],
  webServer: [
    {
      command: "npm run start",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: false,
      env: { NEXT_TELEMETRY_DISABLED: "1" },
    },
    {
      command: `${process.env.SECRETSENSE_PYTHON || "../.venv/bin/python"} -m uvicorn api.main:app --app-dir .. --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers`,
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: false,
    },
  ],
});
