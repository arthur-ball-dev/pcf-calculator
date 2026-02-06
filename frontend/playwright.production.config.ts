import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for production site visual testing.
 * Targets https://pcf.glideslopeintelligence.ai/
 * No global setup (auth is handled in test).
 */
export default defineConfig({
  testDir: './tests/e2e',
  timeout: 180000,
  expect: { timeout: 10000 },
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  workers: 1,
  use: {
    baseURL: 'https://pcf.glideslopeintelligence.ai',
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    actionTimeout: 15000,
    headless: true,
    ignoreHTTPSErrors: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
