/**
 * E2E Authentication Fixture
 *
 * TASK-QA-P7-032: Provides authenticated page fixture for E2E tests
 *
 * This fixture:
 * 1. Reads cached auth token from global setup (or falls back to API)
 * 2. Injects JWT token into localStorage
 * 3. Provides authenticated page for tests
 *
 * Token Caching:
 * - Auth token is obtained once in global-setup.ts
 * - Cached token is read from .auth-state.json via auth-helpers.ts
 * - Avoids hitting rate limit (5 attempts per 5 minutes)
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

import { test as base, expect, Page } from '@playwright/test';
import { getAuthToken, AUTH_TOKEN_KEY, FRONTEND_URL } from './auth-helpers';

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
    // Step 1: Get JWT token (from cache or API)
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
    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded' });

    // Step 4: Wait for the app to be ready
    await page.waitForLoadState('networkidle').catch(() => {});
    await page.waitForTimeout(2000);

    // Provide the authenticated page to the test
    await use(page);
  },
});

// Re-export expect from @playwright/test for convenience
export { expect };
