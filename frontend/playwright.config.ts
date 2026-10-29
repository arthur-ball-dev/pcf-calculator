import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 * Phase 4 - API Integration Validation
 *
 * TASK-QA-P7-032: Added global setup for JWT authentication
 * TASK-BE-P9-xxx: Added isolated test database configuration
 *
 * Tests validate:
 * - API calls to real backend (http://localhost:8000)
 * - Product fetching and BOM loading
 * - Calculation submission and polling
 * - Error handling with network failures
 * - State management with async operations
 * - Request/response interceptors in browser
 *
 * Authentication:
 * - Global setup authenticates once at start of test run
 * - Auth token is cached and reused across all tests
 * - Avoids hitting rate limit (5 attempts per 5 minutes)
 *
 * Test Database (Isolated):
 * - E2E tests use `pcf_calculator_test` PostgreSQL database
 * - Isolated from development database to prevent data pollution
 * - Setup: `npm run test:e2e:setup` creates and seeds the test database
 * - Run isolated: `npm run test:e2e:isolated` runs setup + tests
 * - Connection: postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
 *
 * Available npm scripts:
 * - test:e2e          - Run E2E tests (uses whatever DB backend is configured)
 * - test:e2e:ui       - Run E2E tests with interactive UI
 * - test:e2e:setup    - Setup/reset test database only
 * - test:e2e:isolated - Setup test DB and run tests against it
 *
 * NOTE: Both servers must be running before tests:
 * - Backend: DATABASE_URL=<test-db-url> uvicorn backend.main:app --reload --port 8000
 * - Frontend: npm run dev (http://localhost:5173)
 */
export default defineConfig({
  testDir: './tests/e2e',

  // Global setup runs before all tests (authentication)
  globalSetup: './tests/e2e/global-setup.ts',

  // Maximum time one test can run (120s for production data + dev server overhead)
  timeout: 120 * 1000,

  // Expect assertions timeout
  expect: {
    timeout: 10000
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

    // Capture screenshot only on failure
    screenshot: 'only-on-failure',

    // Video recording only on failure
    video: 'retain-on-failure',

    // Action timeout
    actionTimeout: 15000,

    // Navigation timeout
    navigationTimeout: 60000,
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
  //
  // For isolated E2E testing with test database:
  // 1. Setup test database: npm run test:e2e:setup
  // 2. Start backend with test DB:
  //    export DATABASE_URL=postgresql+psycopg://pcf_user:DB_PASSWORD@localhost:5432/pcf_calculator_test
  //    cd backend && source ../.venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000
  // 3. Start frontend: cd frontend && npm run dev
  // 4. Run tests: npm run test:e2e
  //
  // Or use the combined script: npm run test:e2e:isolated
  // (requires backend to be started with DATABASE_URL already set to test DB)
});
