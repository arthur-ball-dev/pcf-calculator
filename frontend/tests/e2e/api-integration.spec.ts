/**
 * Playwright E2E Test Suite: API Integration
 *
 * TASK-FE-013: Validates API integration in real browser environment
 * TASK-QA-P7-032: Updated to use authenticated fixture for JWT-protected endpoints
 *
 * Test Scenarios:
 * 1. Product fetching from API on page load
 * 2. Product selection triggers BOM loading
 * 3. Calculation submission (async flow with 202 response)
 * 4. Polling for calculation results
 * 5. Error handling when backend is unavailable
 *
 * Prerequisites:
 * - Backend running at http://localhost:8000
 * - Frontend running at http://localhost:5173
 * - Database seeded with test data (6 products)
 * - E2E test user seeded (see backend/database/seeds/e2e_test_user.py)
 *
 * NOTE: This is a VALIDATION task. Tests written to verify existing functionality.
 * If tests fail, bugs are documented for separate fix tasks.
 */

import { test, expect } from './fixtures/auth.fixture';

/**
 * Helper function to select a product from dropdown
 * Handles the Command combobox interaction
 */
async function selectFirstProduct(page: any) {
  // Wait for product selector to be ready
  await page.waitForSelector('[data-testid="product-select-trigger"]', {
    state: 'visible',
    timeout: 10000
  });

  // Setup listener for product search API call BEFORE opening dropdown
  const searchPromise = page.waitForResponse(
    (response: any) =>
      response.url().includes('/api/v1/products/search') &&
      response.request().method() === 'GET',
    { timeout: 10000 }
  );

  const trigger = page.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for product search to complete
  await searchPromise;

  // Wait for products to appear
  await page.waitForSelector('[role="option"]', { state: 'visible', timeout: 5000 });

  // Setup listener for product detail API call BEFORE selecting
  const productDetailPromise = page.waitForResponse(
    (response: any) =>
      response.url().match(/\/api\/v1\/products\/[a-f0-9-]+$/) &&
      response.request().method() === 'GET' &&
      response.status() === 200,
    { timeout: 10000 }
  );

  // Select first option
  const firstOption = page.locator('[role="option"]').first();
  await firstOption.click();

  // Wait for product detail API to complete (includes BOM data)
  await productDetailPromise;
  // Give BOM transform time to process and update UI
  await page.waitForTimeout(1000);
}

/**
 * Test Suite Setup
 * The authenticatedPage fixture handles:
 * - Clearing localStorage and setting auth token
 * - Marking tour as completed to prevent blocking
 * - Navigating to the app
 */

/**
 * Test 1: Product Fetching from API
 *
 * Validates:
 * - GET /api/v1/products/search called when dropdown opens
 * - Response status 200
 * - Products populate dropdown
 * - No CORS errors
 */
test('fetches products from API when dropdown opens', async ({ authenticatedPage }) => {
  // Verify product selector is ready
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible();
  await expect(authenticatedPage.getByTestId('product-select-trigger')).toBeVisible();

  // Setup response listener BEFORE opening dropdown
  const responsePromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/products/search') &&
      response.request().method() === 'GET'
  );

  // Click to open dropdown - this triggers the API call
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for API call to complete
  const response = await responsePromise;

  // Verify API response
  expect(response.status()).toBe(200);

  const responseData = await response.json();
  expect(responseData.items).toBeDefined();
  expect(Array.isArray(responseData.items)).toBe(true);
  expect(responseData.items.length).toBeGreaterThan(0);

  // Verify products appear in dropdown
  await authenticatedPage.waitForSelector('[role="option"]', { timeout: 5000 });

  // Screenshot proof
  await authenticatedPage.screenshot({
    path: 'screenshots/01-products-loaded.png',
    fullPage: true,
  });

  // Verify no console errors (CORS or otherwise)
  const consoleErrors: string[] = [];
  authenticatedPage.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // Small wait to catch any async errors
  await authenticatedPage.waitForTimeout(1000);

  // Should have no CORS or network errors
  expect(
    consoleErrors.filter((err) => err.includes('CORS') || err.includes('Failed to fetch'))
  ).toHaveLength(0);
});

/**
 * Test 2: Product Selection Loads BOM
 *
 * Validates:
 * - Clicking product dropdown shows options
 * - Selecting product triggers GET /api/v1/products/{id}
 * - BOM data loads successfully
 * - Next button becomes enabled
 */
test('selecting product loads BOM from API', async ({ authenticatedPage }) => {
  // Wait for products to load
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible();

  // Select first product using keyboard navigation
  await selectFirstProduct(authenticatedPage);

  // Verify product selected confirmation appears
  await expect(authenticatedPage.getByTestId('product-selected-confirmation')).toBeVisible();

  // Verify Next button becomes enabled
  const nextButton = authenticatedPage.getByTestId('next-button');
  await expect(nextButton).toBeEnabled();

  // Screenshot proof
  await authenticatedPage.screenshot({
    path: 'screenshots/03-product-selected.png',
    fullPage: true,
  });
});

/**
 * Test 3: Navigate to BOM Step
 *
 * Validates:
 * - Clicking Next navigates to BOM editor
 * - BOM data is displayed
 */
test('navigates to BOM editor after product selection', async ({ authenticatedPage }) => {
  // Select product
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible();
  await selectFirstProduct(authenticatedPage);

  // Wait for product selected confirmation
  await expect(authenticatedPage.getByTestId('product-selected-confirmation')).toBeVisible();

  // Wait for Next button to be enabled
  const nextButton = authenticatedPage.getByTestId('next-button');
  await expect(nextButton).toBeEnabled();

  // Click Next button and wait for step heading change
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Edit');
    }, {}, { timeout: 10000 }),
    nextButton.click()
  ]);

  // Verify we're on step 2 (BOM editing)
  await expect(authenticatedPage.getByRole('heading', { name: /Edit Bill of Materials/i })).toBeVisible({
    timeout: 5000,
  });

  // Screenshot proof
  await authenticatedPage.screenshot({
    path: 'screenshots/04-bom-editor.png',
    fullPage: true,
  });
});

/**
 * Test 4: Calculation Submission (Async Flow)
 *
 * Validates:
 * - Navigate through wizard to Calculate step
 * - POST /api/v1/calculate returns 202 Accepted
 * - Response contains calculation_id
 * - Loading spinner appears
 */
test('submits calculation and receives calculation_id', async ({ authenticatedPage }) => {
  // Step 1: Select product
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible();
  await selectFirstProduct(authenticatedPage);
  await expect(authenticatedPage.getByTestId('product-selected-confirmation')).toBeVisible();

  // Navigate to Step 2 (BOM Editor)
  await expect(authenticatedPage.getByTestId('next-button')).toBeEnabled();
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Edit');
    }),
    authenticatedPage.getByTestId('next-button').click()
  ]);
  await expect(authenticatedPage.getByRole('heading', { name: /Edit Bill of Materials/i })).toBeVisible();
  // Wait for BOM data to load and form validation to complete
  await authenticatedPage.waitForTimeout(2000);

  // Navigate to Step 3 (Calculate)
  await expect(authenticatedPage.getByTestId('next-button')).toBeEnabled({ timeout: 5000 });
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Calculate');
    }),
    authenticatedPage.getByTestId('next-button').click()
  ]);
  await expect(authenticatedPage.locator('h2').filter({ hasText: /Calculate/ })).toBeVisible();

  // Screenshot before calculation
  await authenticatedPage.screenshot({
    path: 'screenshots/05-before-calculation.png',
    fullPage: true,
  });

  // Setup listener for calculation API call
  const calculatePromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/calculate') &&
      response.request().method() === 'POST'
  );

  // Click Calculate button
  const calculateButton = authenticatedPage.getByTestId('calculate-button');
  await expect(calculateButton).toBeVisible();
  await calculateButton.click();

  // Wait for API response
  const calculateResponse = await calculatePromise;

  // Verify response status 202 Accepted
  expect(calculateResponse.status()).toBe(202);

  // Verify response body contains calculation_id
  const responseBody = await calculateResponse.json();
  expect(responseBody).toHaveProperty('calculation_id');
  expect(typeof responseBody.calculation_id).toBe('string');
  expect(responseBody.calculation_id.length).toBeGreaterThan(0);

  // Verify loading state appears
  await expect(authenticatedPage.getByTestId('calculating-button')).toBeVisible({ timeout: 2000 });
  await expect(authenticatedPage.getByTestId('loading-spinner')).toBeVisible();

  // Screenshot proof of loading state
  await authenticatedPage.screenshot({
    path: 'screenshots/06-calculation-loading.png',
    fullPage: true,
  });
});

/**
 * Test 5: Polling for Results
 *
 * Validates:
 * - GET /api/v1/calculations/{id} called repeatedly
 * - Eventually returns status: "completed"
 * - Results display appears
 * - Total CO2e value shown
 */
test('polls for calculation results until complete', async ({ page, context }) => {
  // Track all API requests
  const pollingRequests: string[] = [];

  authenticatedPage.on('request', (request) => {
    const url = request.url();
    if (url.includes('/api/v1/calculations/') && request.method() === 'GET') {
      pollingRequests.push(url);
    }
  });

  // Navigate through wizard and submit calculation
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible();
  await selectFirstProduct(authenticatedPage);

  // Wait for confirmation and navigate
  await expect(authenticatedPage.getByTestId('product-selected-confirmation')).toBeVisible();
  await expect(authenticatedPage.getByTestId('next-button')).toBeEnabled();
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Edit');
    }),
    authenticatedPage.getByTestId('next-button').click()
  ]);
  await expect(authenticatedPage.getByRole('heading', { name: /Edit Bill of Materials/i })).toBeVisible();

  await expect(authenticatedPage.getByTestId('next-button')).toBeEnabled({ timeout: 5000 });
  // Wait for BOM data to load and form validation to complete
  await authenticatedPage.waitForTimeout(2000);
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Calculate');
    }),
    authenticatedPage.getByTestId('next-button').click()
  ]);
  await expect(authenticatedPage.locator('h2').filter({ hasText: /Calculate/ })).toBeVisible();

  // Submit calculation
  await authenticatedPage.getByTestId('calculate-button').click();

  // Wait for loading state
  await expect(authenticatedPage.getByTestId('calculating-button')).toBeVisible();

  // Wait for results to appear (up to 30 seconds)
  await expect(authenticatedPage.getByTestId('results-display')).toBeVisible({ timeout: 30000 });

  // Verify total CO2e is displayed
  await expect(authenticatedPage.getByTestId('total-co2e')).toBeVisible();

  // Verify the value is a number
  const totalCO2eText = await authenticatedPage.getByTestId('total-co2e').textContent();
  expect(totalCO2eText).toBeTruthy();
  const numericValue = parseFloat(totalCO2eText || '0');
  expect(numericValue).toBeGreaterThan(0);

  // Screenshot proof of results
  await authenticatedPage.screenshot({
    path: 'screenshots/07-results-displayed.png',
    fullPage: true,
  });

  // Verify polling occurred multiple times
  expect(pollingRequests.length).toBeGreaterThan(0);
  console.log(`Polling occurred ${pollingRequests.length} times`);
});

/**
 * Test 6: Complete End-to-End Flow
 *
 * Validates:
 * - Full wizard flow from start to finish
 * - All API calls succeed
 * - Results display correctly
 */
test('completes full calculation flow end-to-end', async ({ authenticatedPage }) => {
  // Step 1: Select Product
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible();
  await selectFirstProduct(authenticatedPage);
  await expect(authenticatedPage.getByTestId('next-button')).toBeEnabled();

  // Step 2: BOM Editor
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Edit');
    }),
    authenticatedPage.getByTestId('next-button').click()
  ]);
  await expect(authenticatedPage.getByRole('heading', { name: /Edit Bill of Materials/i })).toBeVisible();
  await expect(authenticatedPage.getByTestId('next-button')).toBeEnabled({ timeout: 5000 });

  // Wait for BOM data to load and form validation to complete
  await authenticatedPage.waitForTimeout(2000);
  // Step 3: Calculate
  await Promise.all([
    authenticatedPage.waitForFunction(() => {
      const heading = document.querySelector('h2');
      return heading && heading.textContent && heading.textContent.includes('Calculate');
    }),
    authenticatedPage.getByTestId('next-button').click()
  ]);
  await expect(authenticatedPage.locator('h2').filter({ hasText: /Calculate/ })).toBeVisible();
  await authenticatedPage.getByTestId('calculate-button').click();

  // Step 4: Results
  await expect(authenticatedPage.getByTestId('results-display')).toBeVisible({ timeout: 30000 });
  await expect(authenticatedPage.getByTestId('results-summary')).toBeVisible();
  await expect(authenticatedPage.getByTestId('total-co2e')).toBeVisible();

  // Verify results contain Unicode CO₂e (Issue D fix)
  const resultsText = await authenticatedPage.textContent('body');
  expect(resultsText).toContain('kg CO₂e');


  // Verify New Calculation button exists
  await expect(authenticatedPage.getByTestId('new-calculation-action-button')).toBeVisible();

  // Final screenshot
  await authenticatedPage.screenshot({
    path: 'screenshots/08-complete-flow.png',
    fullPage: true,
  });
});

/**
 * Test 7: Error Handling (Backend Down)
 *
 * NOTE: This test requires manually stopping the backend server
 * Run separately with: npx playwright test --grep "backend.*down"
 *
 * To run this test:
 * 1. Stop backend server
 * 2. Run: npx playwright test api-integration.spec.ts --grep "backend.*down"
 * 3. Restart backend server
 */
test.skip('handles API errors gracefully when backend is down', async ({ authenticatedPage }) => {
  // NOTE: Backend must be manually stopped before running this test

  // Wait for error message to appear
  await expect(authenticatedPage.getByTestId('error-message')).toBeVisible({ timeout: 10000 });

  // Verify error message contains expected text
  const errorText = await authenticatedPage.getByTestId('error-message').textContent();
  expect(errorText).toContain('Unable to load products');

  // Verify retry button is present
  await expect(authenticatedPage.getByTestId('retry-button')).toBeVisible();

  // Screenshot proof
  await authenticatedPage.screenshot({
    path: 'screenshots/09-api-error-handled.png',
    fullPage: true,
  });
});
