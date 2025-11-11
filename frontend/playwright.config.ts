import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 * Phase 4 - API Integration Validation
 *
 * Tests validate:
 * - API calls to real backend (http://localhost:8000)
 * - Product fetching and BOM loading
 * - Calculation submission and polling
 * - Error handling with network failures
 * - State management with async operations
 * - Request/response interceptors in browser
 *
 * NOTE: Both servers must be running before tests:
 * - Backend: http://localhost:8000
 * - Frontend: http://localhost:5173
 */
export default defineConfig({
  testDir: './tests/e2e',

  // Maximum time one test can run
  timeout: 30 * 1000,

  // Expect assertions timeout
  expect: {
    timeout: 5000
  },

  // Run tests sequentially for API state stability
  fullyParallel: false,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // No retries on first run - identify real issues
  retries: 0,

  // Reporter to use
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list']
  ],

  // Single worker for deterministic execution
  workers: 1,

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:5173',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Capture screenshot on every test (for documentation)
    screenshot: 'on',

    // Video recording
    video: 'retain-on-failure',

    // Action timeout
    actionTimeout: 10000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // NOTE: Servers must be manually started before running tests
  // This ensures we test against real production-like environment
  // Backend: cd backend && source ../.venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000
  // Frontend: cd frontend && npm run dev
});
