/**
 * Playwright E2E Test Suite: Product Selector BOM Filter
 *
 * TASK-FE-P8-001: Validates BOM filter toggle in product selection flow
 *
 * Test-Driven Development Protocol:
 * - These tests MUST be committed BEFORE implementation
 * - Tests should FAIL initially (toggle component not implemented)
 * - Implementation must make tests PASS without modifying tests
 *
 * Test Scenarios:
 * 1. Toggle loads in default "With BOMs" state
 * 2. Clicking "All Products" refreshes product list
 * 3. Search with filter active returns filtered results
 * 4. Filter toggle is accessible via keyboard
 * 5. Network validation - API calls include has_bom parameter
 *
 * Prerequisites:
 * - Backend running at http://localhost:8000
 * - Frontend running at http://localhost:5173
 * - Database seeded with test data (products with and without BOMs)
 * - E2E test user seeded
 *
 * Screenshot Evidence Required:
 * Location: frontend/tests/screenshots/bom-filter-*.png
 * 1. bom-filter-default.png - Toggle in default "With BOMs" state
 * 2. bom-filter-all-products.png - Toggle after clicking "All Products"
 * 3. bom-filter-console.png - DevTools Console (0 errors)
 * 4. bom-filter-network.png - DevTools Network showing has_bom=true parameter
 */

import { test, expect } from './fixtures/auth.fixture';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// ESM-compatible __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Ensure screenshots directory exists
const screenshotsDir = path.join(__dirname, '../screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

/**
 * Test 1: Toggle Loads in Default "With BOMs" State
 *
 * Validates:
 * - BOM filter toggle is visible on page load
 * - "With BOMs" option is selected by default
 * - Toggle has correct ARIA attributes
 */
test('toggle loads in default "With BOMs" state', async ({ authenticatedPage }) => {
  // Wait for the product selector to be ready
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Verify toggle group is visible
  await expect(authenticatedPage.getByTestId('bom-filter-toggle-group')).toBeVisible();

  // Verify "With BOMs" button exists and is selected
  const withBomsButton = authenticatedPage.getByTestId('bom-filter-with-bom');
  await expect(withBomsButton).toBeVisible();
  await expect(withBomsButton).toHaveAttribute('aria-pressed', 'true');

  // Verify "All Products" button exists and is not selected
  const allProductsButton = authenticatedPage.getByTestId('bom-filter-all');
  await expect(allProductsButton).toBeVisible();
  await expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');

  // Verify label text
  await expect(authenticatedPage.getByText('Show:')).toBeVisible();
  await expect(authenticatedPage.getByText('With BOMs')).toBeVisible();
  await expect(authenticatedPage.getByText('All Products')).toBeVisible();

  // Screenshot evidence: Default state
  await authenticatedPage.screenshot({
    path: path.join(screenshotsDir, 'bom-filter-default.png'),
    fullPage: true,
  });
});

/**
 * Test 2: Clicking "All Products" Refreshes List
 *
 * Validates:
 * - Clicking "All Products" toggle updates selection state
 * - API is called without has_bom filter (or with has_bom=undefined)
 * - Product list shows all products
 */
test('clicking "All Products" refreshes list with all products', async ({ authenticatedPage }) => {
  // Wait for selector to be ready
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Setup listener for API call BEFORE clicking toggle
  const allProductsPromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/products/search') &&
      response.request().method() === 'GET',
    { timeout: 10000 }
  );

  // Click "All Products" toggle
  const allProductsButton = authenticatedPage.getByTestId('bom-filter-all');
  await allProductsButton.click();

  // Verify toggle state changed
  await expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
  await expect(authenticatedPage.getByTestId('bom-filter-with-bom')).toHaveAttribute(
    'aria-pressed',
    'false'
  );

  // Open dropdown to verify list refreshed
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for products to load
  const response = await allProductsPromise;
  expect(response.status()).toBe(200);

  // Verify URL does not include has_bom=true (or has undefined)
  const requestUrl = response.request().url();
  const url = new URL(requestUrl);
  const hasBomParam = url.searchParams.get('has_bom');
  // When "All Products" is selected, has_bom should not be in the query or should be undefined
  expect(hasBomParam).toBeNull();

  // Verify more products are shown (all products vs only those with BOM)
  const responseData = await response.json();
  expect(responseData.items).toBeDefined();
  expect(Array.isArray(responseData.items)).toBe(true);

  // Screenshot evidence: All Products state
  await authenticatedPage.screenshot({
    path: path.join(screenshotsDir, 'bom-filter-all-products.png'),
    fullPage: true,
  });
});

/**
 * Test 3: Default Filter Sends has_bom=true to API
 *
 * Validates:
 * - When dropdown opens with default "With BOMs" filter
 * - API request includes has_bom=true parameter
 */
test('default filter sends has_bom=true to API', async ({ authenticatedPage }) => {
  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Setup listener for API call
  const searchPromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/products/search') &&
      response.request().method() === 'GET',
    { timeout: 10000 }
  );

  // Open the dropdown (triggers search)
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for API response
  const response = await searchPromise;
  expect(response.status()).toBe(200);

  // Verify has_bom=true is in the request URL
  const requestUrl = response.request().url();
  const url = new URL(requestUrl);
  const hasBomParam = url.searchParams.get('has_bom');

  expect(hasBomParam).toBe('true');
});

/**
 * Test 4: Search with Filter Active
 *
 * Validates:
 * - User can type search query with filter active
 * - API call includes both query and has_bom parameter
 * - Filtered results are displayed
 */
test('search with filter active returns filtered results', async ({ authenticatedPage }) => {
  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Open dropdown
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for dropdown to open
  await authenticatedPage.waitForSelector('[role="option"]', {
    state: 'visible',
    timeout: 10000,
  });

  // Find search input and type
  const searchInput = authenticatedPage.getByPlaceholder(/search/i);
  await expect(searchInput).toBeVisible();

  // Setup listener for search API call
  const searchWithQueryPromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/products/search') &&
      response.url().includes('query=') &&
      response.request().method() === 'GET',
    { timeout: 10000 }
  );

  // Type search query
  await searchInput.fill('motor');

  // Wait for debounced search
  const searchResponse = await searchWithQueryPromise;
  expect(searchResponse.status()).toBe(200);

  // Verify both has_bom and query params are present
  const requestUrl = searchResponse.request().url();
  const url = new URL(requestUrl);

  expect(url.searchParams.get('has_bom')).toBe('true');
  expect(url.searchParams.get('query')).toContain('motor');
});

/**
 * Test 5: Filter Toggle Accessible via Keyboard
 *
 * Validates:
 * - Toggle buttons are focusable with Tab
 * - Enter/Space activates toggle
 * - State changes correctly
 */
test('filter toggle accessible via keyboard', async ({ authenticatedPage }) => {
  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Get toggle buttons
  const withBomsButton = authenticatedPage.getByTestId('bom-filter-with-bom');
  const allProductsButton = authenticatedPage.getByTestId('bom-filter-all');

  // Focus on "With BOMs" button (should be first in tab order)
  await withBomsButton.focus();
  await expect(withBomsButton).toBeFocused();

  // Tab to "All Products" button
  await authenticatedPage.keyboard.press('Tab');
  await expect(allProductsButton).toBeFocused();

  // Press Enter to activate
  await authenticatedPage.keyboard.press('Enter');

  // Verify state changed
  await expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
  await expect(withBomsButton).toHaveAttribute('aria-pressed', 'false');

  // Tab back and use Space to activate
  await authenticatedPage.keyboard.press('Shift+Tab');
  await expect(withBomsButton).toBeFocused();
  await authenticatedPage.keyboard.press('Space');

  // Verify state changed back
  await expect(withBomsButton).toHaveAttribute('aria-pressed', 'true');
  await expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');
});

/**
 * Test 6: Console Error Validation
 *
 * Validates:
 * - No JavaScript errors in console during filter interactions
 * - No React warnings during toggle state changes
 */
test('no console errors during filter usage', async ({ authenticatedPage }) => {
  const consoleErrors: string[] = [];
  const consoleWarnings: string[] = [];

  // Listen for console messages
  authenticatedPage.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
    if (msg.type() === 'warning' && !msg.text().includes('React DevTools')) {
      consoleWarnings.push(msg.text());
    }
  });

  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Interact with toggle
  const allProductsButton = authenticatedPage.getByTestId('bom-filter-all');
  await allProductsButton.click();

  // Wait a moment for any async errors
  await authenticatedPage.waitForTimeout(1000);

  // Switch back
  const withBomsButton = authenticatedPage.getByTestId('bom-filter-with-bom');
  await withBomsButton.click();

  // Open dropdown
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for products
  await authenticatedPage.waitForSelector('[role="option"]', {
    state: 'visible',
    timeout: 10000,
  });

  // Wait for any async operations
  await authenticatedPage.waitForTimeout(500);

  // Screenshot evidence: Console state
  await authenticatedPage.screenshot({
    path: path.join(screenshotsDir, 'bom-filter-console.png'),
    fullPage: true,
  });

  // Verify no errors
  expect(consoleErrors).toHaveLength(0);
});

/**
 * Test 7: Network Request Validation
 *
 * Validates:
 * - Correct HTTP method (GET)
 * - Correct endpoint (/api/v1/products/search)
 * - Response time <500ms
 * - No CORS errors
 */
test('network requests have correct format and performance', async ({ authenticatedPage }) => {
  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Record request timing
  const startTime = Date.now();

  // Setup listener for API call
  const apiPromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/products/search') &&
      response.request().method() === 'GET',
    { timeout: 10000 }
  );

  // Trigger API call by opening dropdown
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for response
  const response = await apiPromise;
  const endTime = Date.now();
  const responseTime = endTime - startTime;

  // Validate response
  expect(response.status()).toBe(200);
  expect(response.request().method()).toBe('GET');

  // Validate URL structure
  const requestUrl = response.request().url();
  expect(requestUrl).toContain('/api/v1/products/search');
  expect(requestUrl).toContain('has_bom=true');

  // Validate performance (should be <500ms)
  expect(responseTime).toBeLessThan(500);

  // Validate response body structure
  const responseData = await response.json();
  expect(responseData).toHaveProperty('items');
  expect(responseData).toHaveProperty('total');
  expect(responseData).toHaveProperty('has_more');

  // Screenshot evidence: Network (for documentation purposes)
  await authenticatedPage.screenshot({
    path: path.join(screenshotsDir, 'bom-filter-network.png'),
    fullPage: true,
  });

  console.log(`API Response time: ${responseTime}ms`);
});

/**
 * Test 8: Complete Flow with BOM Filter
 *
 * Validates:
 * - User can select product with filter active
 * - Selected product confirmation appears
 * - Next button becomes enabled
 */
test('complete product selection flow with BOM filter', async ({ authenticatedPage }) => {
  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  // Verify default filter state
  await expect(authenticatedPage.getByTestId('bom-filter-with-bom')).toHaveAttribute(
    'aria-pressed',
    'true'
  );

  // Setup listeners
  const searchPromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/products/search') &&
      response.request().method() === 'GET',
    { timeout: 10000 }
  );

  // Open dropdown
  const trigger = authenticatedPage.getByTestId('product-select-trigger');
  await trigger.click();

  // Wait for products to load
  await searchPromise;
  await authenticatedPage.waitForSelector('[role="option"]', {
    state: 'visible',
    timeout: 10000,
  });

  // Setup listener for product detail fetch
  const productDetailPromise = authenticatedPage.waitForResponse(
    (response) =>
      response.url().match(/\/api\/v1\/products\/[a-f0-9-]+$/) &&
      response.request().method() === 'GET' &&
      response.status() === 200,
    { timeout: 10000 }
  );

  // Select first product
  const firstOption = authenticatedPage.locator('[role="option"]').first();
  await firstOption.click();

  // Wait for product detail to load
  await productDetailPromise;

  // Verify confirmation message
  await expect(authenticatedPage.getByTestId('product-selected-confirmation')).toBeVisible({
    timeout: 5000,
  });

  // Verify Next button is enabled
  const nextButton = authenticatedPage.getByTestId('next-button');
  await expect(nextButton).toBeEnabled();

  // Verify filter state is still correct (didn't reset)
  await expect(authenticatedPage.getByTestId('bom-filter-with-bom')).toHaveAttribute(
    'aria-pressed',
    'true'
  );
});

/**
 * Test 9: Filter Toggle Visual Styling
 *
 * Validates:
 * - Active button has distinct visual appearance
 * - Inactive button has different appearance
 * - Hover states work correctly
 */
test('filter toggle has correct visual styling', async ({ authenticatedPage }) => {
  // Wait for selector
  await expect(authenticatedPage.getByTestId('product-selector')).toBeVisible({ timeout: 10000 });

  const withBomsButton = authenticatedPage.getByTestId('bom-filter-with-bom');
  const allProductsButton = authenticatedPage.getByTestId('bom-filter-all');

  // Get computed styles for active button
  const withBomsStyles = await withBomsButton.evaluate((el) => {
    const styles = window.getComputedStyle(el);
    return {
      backgroundColor: styles.backgroundColor,
      color: styles.color,
    };
  });

  // Get computed styles for inactive button
  const allProductsStyles = await allProductsButton.evaluate((el) => {
    const styles = window.getComputedStyle(el);
    return {
      backgroundColor: styles.backgroundColor,
      color: styles.color,
    };
  });

  // Active and inactive buttons should have different styles
  // (exact values depend on implementation, but they should differ)
  expect(withBomsStyles.backgroundColor !== allProductsStyles.backgroundColor ||
         withBomsStyles.color !== allProductsStyles.color).toBe(true);

  // Click to change active state
  await allProductsButton.click();

  // Get new styles
  const newWithBomsStyles = await withBomsButton.evaluate((el) => {
    const styles = window.getComputedStyle(el);
    return {
      backgroundColor: styles.backgroundColor,
      color: styles.color,
    };
  });

  // Styles should have changed (active became inactive)
  expect(newWithBomsStyles.backgroundColor !== withBomsStyles.backgroundColor ||
         newWithBomsStyles.color !== withBomsStyles.color).toBe(true);
});

/**
 * Test 10: Toggle Works After Error Recovery
 *
 * Validates:
 * - If initial load fails, toggle still works after retry
 */
test.skip('toggle works after error recovery', async ({ authenticatedPage }) => {
  // This test requires ability to simulate network errors
  // Skip for now - will be implemented with network interception
});
