import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  testMatch: "*.spec.ts",
  timeout: 60000,
  workers: 1,
  use: {
    baseURL: process.env.ARM_URL ?? "http://localhost:8780",
    headless: true,
    viewport: { width: 1440, height: 1080 },
    launchOptions: {
      ...(process.env.CHROMIUM_PATH
        ? { executablePath: process.env.CHROMIUM_PATH }
        : {}),
    },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
});
