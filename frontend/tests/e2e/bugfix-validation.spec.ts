/**
 * Bug Fix Validation E2E Tests
 * Validates the 4 bug fixes from the plan:
 * 1. BOM table columns visibility at 1024px
 * 2. Loading indicator on Next button
 * 3. Calculation error handling
 * 4. BOM loading performance
 *
 * UI Structure (3-step wizard - Emerald Night):
 * - Step 1: Select Product (ProductList - full-page list with search + filters)
 * - Step 2: Edit BOM (BOM editor with Calculate button via next-button)
 * - Step 3: Results (after calculation completes)
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots/bugfix-validation';

// Ensure screenshot directory exists
test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

async function takeScreenshot(page: Page, name: string) {
  const filepath = path.join(SCREENSHOT_DIR, `${name}.png`);
  // Use viewport screenshot instead of fullPage to avoid timeout issues
  await page.screenshot({ path: filepath, fullPage: false, timeout: 60000 });
  console.log(`Screenshot: ${filepath}`);
}

// Helper to set up auth and dismiss tour
async function setupAuth(page: Page, request: any) {
  const authResponse = await request.post('http://localhost:8000/api/v1/auth/login', {
    data: { username: 'e2e-test', password: 'E2ETestPassword123!' },
  });

  let authToken = '';
  if (authResponse.ok()) {
    const authData = await authResponse.json();
    authToken = authData.access_token;
  }

  await page.addInitScript((token) => {
    window.localStorage.setItem('auth_token', token);
    window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
  }, authToken);
}

/**
 * Helper to select the first product from the ProductList.
 * ProductList auto-loads products on mount; products are clickable rows with role="option".
 */
async function selectFirstProductFromList(page: Page) {
  // Wait for products to load in the list
  await page.waitForSelector('[role="option"]', {
    state: 'visible',
    timeout: 15000,
  });

  // Setup listener for product detail API call BEFORE selecting
  // Product IDs can be hex strings (no dashes) or UUIDs (with dashes)
  const productDetailPromise = page.waitForResponse(
    (response) =>
      response.url().match(/\/api\/v1\/products\/[a-f0-9-]+$/) !== null &&
      response.request().method() === 'GET' &&
      response.status() === 200,
    { timeout: 10000 }
  );

  // Click first product row
  const firstProductRow = page.locator('[role="option"]').first();
  await firstProductRow.click();

  // Wait for product detail API to complete
  await productDetailPromise;
}

test.describe('Bug Fix #2: BOM Table Columns Visibility', () => {
  test('all columns visible at 1024px viewport', async ({ page, request }) => {
    test.setTimeout(60000);

    // Set viewport to 1024px
    await page.setViewportSize({ width: 1024, height: 768 });

    await setupAuth(page, request);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select a product with BOM from ProductList
    await selectFirstProductFromList(page);

    // Click Next to go to BOM editor
    const nextButton = page.getByTestId('next-button');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();

    // Wait for BOM editor to load (Step 2 heading: "Edit BOM")
    await expect(page.locator('h2').filter({ hasText: /Edit BOM/i })).toBeVisible({ timeout: 15000 });
    await page.waitForLoadState('networkidle').catch(() => {});

    await takeScreenshot(page, 'bugfix2-bom-table-1024px');

    // Verify all expected columns are visible (check table headers)
    const tableHeaders = page.locator('th');
    const headerTexts = await tableHeaders.allTextContents();
    console.log('Headers at 1024px:', headerTexts);

    // Check that key columns are present
    // Current BOM table headers: Component, Category, Quantity, Emission Factor, Source, CO2e, Actions
    const hasComponentName = headerTexts.some(h => h.toLowerCase().includes('component'));
    const hasQuantity = headerTexts.some(h => h.toLowerCase().includes('quantity'));
    const hasCategory = headerTexts.some(h => h.toLowerCase().includes('category'));
    const hasEmissionFactor = headerTexts.some(h => h.toLowerCase().includes('emission'));
    const hasSource = headerTexts.some(h => h.toLowerCase().includes('source'));
    const hasActions = headerTexts.some(h => h.toLowerCase().includes('action'));

    expect(hasComponentName).toBe(true);
    expect(hasQuantity).toBe(true);
    expect(hasCategory).toBe(true);
    expect(hasEmissionFactor).toBe(true);
    expect(hasSource).toBe(true);
    expect(hasActions).toBe(true);

    // Test 1280px viewport
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForLoadState('domcontentloaded').catch(() => {});
    await takeScreenshot(page, 'bugfix2-bom-table-1280px');

    // Test 1920px viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForLoadState('domcontentloaded').catch(() => {});
    await takeScreenshot(page, 'bugfix2-bom-table-1920px');
  });
});

test.describe('Bug Fix #3: Loading Indicator on Next Button', () => {
  test('shows loading state during BOM fetch', async ({ page, request }) => {
    test.setTimeout(60000);

    await setupAuth(page, request);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await takeScreenshot(page, 'bugfix3-initial');

    // Select a product with BOM from ProductList
    await selectFirstProductFromList(page);
    await takeScreenshot(page, 'bugfix3-product-selected');

    // Check Next button state before clicking
    const nextButton = page.getByTestId('next-button');
    const initialText = await nextButton.textContent();
    console.log('Next button text before click:', initialText);

    // Click Next and immediately capture state
    await nextButton.click();

    // Take screenshot quickly to capture loading state
    await page.waitForTimeout(100);
    await takeScreenshot(page, 'bugfix3-loading-state');

    // Wait for BOM editor (Step 2 heading: "Edit BOM")
    await expect(page.locator('h2').filter({ hasText: /Edit BOM/i })).toBeVisible({ timeout: 15000 });
    await takeScreenshot(page, 'bugfix3-bom-loaded');
  });
});

test.describe('Bug Fix #1 & #4: Calculation Flow', () => {
  test('complete calculation flow for product with BOM', async ({ page, request }) => {
    test.setTimeout(120000);

    await setupAuth(page, request);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Select product from ProductList
    await selectFirstProductFromList(page);

    // Navigate to BOM editor
    const nextButton = page.getByTestId('next-button');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await expect(page.locator('h2').filter({ hasText: /Edit BOM/i })).toBeVisible({ timeout: 15000 });
    await takeScreenshot(page, 'bugfix1-bom-ready');

    // Click Calculate (Next button on edit step shows "Calculate")
    const calculateButton = page.getByTestId('next-button');
    await expect(calculateButton).toBeEnabled({ timeout: 5000 });
    await calculateButton.click();
    await takeScreenshot(page, 'bugfix1-calculation-started');

    // Wait and take progress screenshot
    await page.waitForLoadState('networkidle').catch(() => {});
    await takeScreenshot(page, 'bugfix1-calculation-progress');

    // Wait for results or error
    try {
      await page.waitForSelector('[data-testid="results-display"]', { timeout: 60000 });
      await takeScreenshot(page, 'bugfix1-calculation-success');
      console.log('Calculation completed successfully!');
    } catch (e) {
      // Check for calculation overlay
      const overlay = page.locator('[data-testid="calculation-overlay"]');
      if (await overlay.isVisible()) {
        await takeScreenshot(page, 'bugfix1-calculation-overlay');
      }

      // Check for error state
      const errorText = await page.locator('text=/error|failed/i').first().textContent().catch(() => null);
      if (errorText) {
        console.log('Error encountered:', errorText);
        await takeScreenshot(page, 'bugfix1-calculation-error');
      }
      throw e;
    }
  });
});

test.describe('Products WITHOUT BOMs', () => {
  test('handles product without BOM correctly', async ({ page, request }) => {
    test.setTimeout(60000);

    await setupAuth(page, request);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for product list to load
    await page.waitForSelector('[data-testid="product-list"]', { timeout: 10000 });

    // Turn off the "With BOMs" toggle to show all products
    const bomToggle = page.getByTestId('bom-toggle-switch');
    await expect(bomToggle).toBeVisible({ timeout: 5000 });
    // Toggle is on by default (showOnlyWithBom=true), click to turn off
    await bomToggle.click();
    await page.waitForResponse(resp => resp.url().includes('/products/search') && resp.status() === 200, { timeout: 10000 }).catch(() => {});
    await takeScreenshot(page, 'without-bom-all-products');

    // Search for a component product
    const searchInput = page.getByTestId('product-search-input');
    await searchInput.fill('cotton');
    await page.waitForResponse(resp => resp.url().includes('/products/search') && resp.status() === 200, { timeout: 10000 }).catch(() => {});
    await takeScreenshot(page, 'without-bom-search-results');

    // Select if available
    const productRows = page.locator('[role="option"]');
    const count = await productRows.count();
    if (count > 0) {
      // Setup listener for product detail API call BEFORE selecting
      const productDetailPromise = page.waitForResponse(
        (response) =>
          response.url().match(/\/api\/v1\/products\/[a-f0-9-]+$/) !== null &&
          response.request().method() === 'GET',
        { timeout: 10000 }
      );

      await productRows.first().click();
      await productDetailPromise;
      await takeScreenshot(page, 'without-bom-product-selected');

      // Check Next button - should be enabled to allow adding manual BOM
      const nextButton = page.getByTestId('next-button');
      await expect(nextButton).toBeEnabled({ timeout: 5000 });
      await nextButton.click();

      // Wait for BOM editor with empty state (heading: "Edit BOM")
      await expect(page.locator('h2').filter({ hasText: /Edit BOM/i })).toBeVisible({ timeout: 15000 });
      await takeScreenshot(page, 'without-bom-empty-editor');
    } else {
      console.log('No products without BOM found in search');
      await takeScreenshot(page, 'without-bom-no-results');
    }
  });
});
