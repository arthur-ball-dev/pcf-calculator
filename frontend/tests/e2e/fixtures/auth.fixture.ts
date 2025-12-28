/**
 * E2E Authentication Fixture
 *
 * TASK-QA-P7-032: Provides authenticated page fixture for E2E tests
 *
 * This fixture:
 * 1. Authenticates via /api/v1/auth/login API
 * 2. Injects JWT token into localStorage
 * 3. Provides authenticated page for tests
 *
 * Usage:
 *   import { test, expect } from './fixtures/auth.fixture';
 *
 *   test('test name', async ({ authenticatedPage }) => {
 *     // authenticatedPage is already authenticated
 *     await expect(authenticatedPage.locator('[data-testid="product-selector"]')).toBeVisible();
 *   });
 *
 * For tests that need unauthenticated behavior:
 *   import { test as unauthTest, expect } from '@playwright/test';
 */

import { test as base, expect, Page, APIRequestContext } from '@playwright/test';

// E2E Test User Credentials
// Note: This user must exist in the database (seeded via backend/database/seeds)
const E2E_TEST_USER = {
  username: 'e2e-test',
  password: 'E2ETestPassword123!',
};

// API endpoints
const API_BASE_URL = 'http://localhost:8000';
const AUTH_LOGIN_ENDPOINT = `${API_BASE_URL}/api/v1/auth/login`;
const FRONTEND_URL = 'http://localhost:5173';

// localStorage key for auth token (must match frontend client.ts usage)
const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Get JWT access token from the auth API
 *
 * @param request - Playwright's APIRequestContext
 * @returns JWT access token string
 * @throws Error if authentication fails
 */
async function getAuthToken(request: APIRequestContext): Promise<string> {
  const response = await request.post(AUTH_LOGIN_ENDPOINT, {
    data: E2E_TEST_USER,
  });

  if (!response.ok()) {
    const errorText = await response.text();
    throw new Error(
      `E2E Auth failed: ${response.status()} - ${errorText}\n` +
        `Ensure test user '${E2E_TEST_USER.username}' exists in database.\n` +
        `Run: python -c "from backend.database.seeds.e2e_test_user import seed_test_user; seed_test_user()"`
    );
  }

  const data = await response.json();

  if (!data.access_token) {
    throw new Error('Auth response missing access_token field');
  }

  return data.access_token;
}

/**
 * Custom fixture type for authenticated page
 */
type AuthFixtures = {
  /**
   * Pre-authenticated page with JWT token in localStorage
   * Navigates to frontend app after auth setup
   */
  authenticatedPage: Page;
};

/**
 * Extended test object with authentication fixtures
 *
 * Usage:
 *   import { test, expect } from './fixtures/auth.fixture';
 *
 *   test('my test', async ({ authenticatedPage }) => {
 *     // Page is already authenticated and on the app
 *   });
 */
export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page, request }, use) => {
    // Step 1: Get JWT token from auth API
    const token = await getAuthToken(request);

    // Step 2: Inject token into localStorage BEFORE navigating
    // This ensures the frontend has the token when it initializes
    await page.addInitScript(
      ({ tokenKey, tokenValue }) => {
        window.localStorage.setItem(tokenKey, tokenValue);
        // Also mark tour as completed to prevent blocking
        window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
      },
      { tokenKey: AUTH_TOKEN_KEY, tokenValue: token }
    );

    // Step 3: Navigate to the frontend app
    await page.goto(FRONTEND_URL);

    // Step 4: Wait for the app to be ready
    // Wait for network to settle and page to be interactive
    await page.waitForLoadState('networkidle');

    // Provide the authenticated page to the test
    await use(page);
  },
});

// Re-export expect from @playwright/test for convenience
export { expect };
