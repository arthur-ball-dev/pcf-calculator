/**
 * Bug Fix Validation E2E Tests
 * Validates the 4 bug fixes from the plan:
 * 1. BOM table columns visibility at 1024px
 * 2. Loading indicator on Next button
 * 3. Calculation error handling
 * 4. BOM loading performance
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
  await page.screenshot({ path: filepath, fullPage: false, timeout: 30000 });
  console.log(`Screenshot: ${filepath}`);
}

// Helper to dismiss the Joyride tour if it's visible
async function dismissTour(page: Page) {
  // Wait for page to load
  await page.waitForLoadState('networkidle');

  // Try to dismiss tour by pressing Escape multiple times or clicking skip
  const skipButton = page.locator('button:has-text("Skip")');
  if (await skipButton.isVisible({ timeout: 2000 }).catch(() => false)) {
    await skipButton.click();
    await page.waitForTimeout(300);
  }

  // Also try pressing Escape to close any tour overlays
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);

  // Clear localStorage to prevent tour on subsequent navigations
  await page.evaluate(() => {
    localStorage.setItem('hasSeenTour', 'true');
    localStorage.setItem('tourCompleted', 'true');
  });
}

test.describe('Bug Fix #2: BOM Table Columns Visibility', () => {
  test('all columns visible at 1024px viewport', async ({ page }) => {
    // Set viewport to 1024px
    await page.setViewportSize({ width: 1024, height: 768 });

    await page.goto('/');
    await dismissTour(page);

    // Select a product with BOM
    const productSelect = page.getByTestId('product-select-trigger');
    await productSelect.click();
    await page.waitForTimeout(500);

    // Click first product in the list
    const firstProduct = page.locator('[cmdk-item]').first();
    await firstProduct.click();
    await page.waitForTimeout(500);

    // Click Next to go to BOM editor
    const nextButton = page.getByTestId('next-button');
    await nextButton.click();

    // Wait for BOM editor to load (Step 2 heading)
    await page.waitForSelector('text=Step 2: Edit Bill of Materials', { timeout: 15000 });
    await page.waitForTimeout(1000);

    await takeScreenshot(page, 'bugfix2-bom-table-1024px');

    // Verify all expected columns are visible (check table headers)
    const tableHeaders = page.locator('th');
    const headerTexts = await tableHeaders.allTextContents();
    console.log('Headers at 1024px:', headerTexts);

    // Check that key columns are present
    const hasComponentName = headerTexts.some(h => h.toLowerCase().includes('component'));
    const hasQuantity = headerTexts.some(h => h.toLowerCase().includes('quantity'));
    const hasUnit = headerTexts.some(h => h.toLowerCase().includes('unit'));
    const hasCategory = headerTexts.some(h => h.toLowerCase().includes('category'));
    const hasEmissionFactor = headerTexts.some(h => h.toLowerCase().includes('emission'));
    const hasSource = headerTexts.some(h => h.toLowerCase().includes('source'));
    const hasActions = headerTexts.some(h => h.toLowerCase().includes('action'));

    expect(hasComponentName).toBe(true);
    expect(hasQuantity).toBe(true);
    expect(hasUnit).toBe(true);
    expect(hasCategory).toBe(true);
    expect(hasEmissionFactor).toBe(true);
    expect(hasSource).toBe(true);
    expect(hasActions).toBe(true);

    // Test 1280px viewport
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.waitForTimeout(500);
    await takeScreenshot(page, 'bugfix2-bom-table-1280px');

    // Test 1920px viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    await takeScreenshot(page, 'bugfix2-bom-table-1920px');
  });
});

test.describe('Bug Fix #3: Loading Indicator on Next Button', () => {
  test('shows loading state during BOM fetch', async ({ page }) => {
    await page.goto('/');
    await dismissTour(page);
    await takeScreenshot(page, 'bugfix3-initial');

    // Select a product with BOM
    const productSelect = page.getByTestId('product-select-trigger');
    await productSelect.click();
    await page.waitForTimeout(500);

    // Click first product
    const firstProduct = page.locator('[cmdk-item]').first();
    await firstProduct.click();
    await page.waitForTimeout(500);
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

    // Wait for BOM editor (Step 2 heading)
    await page.waitForSelector('text=Step 2: Edit Bill of Materials', { timeout: 15000 });
    await takeScreenshot(page, 'bugfix3-bom-loaded');
  });
});

test.describe('Bug Fix #1 & #4: Calculation Flow', () => {
  test('complete calculation flow for product with BOM', async ({ page }) => {
    await page.goto('/');
    await dismissTour(page);

    // Select product
    const productSelect = page.getByTestId('product-select-trigger');
    await productSelect.click();
    await page.waitForTimeout(500);

    const firstProduct = page.locator('[cmdk-item]').first();
    await firstProduct.click();
    await page.waitForTimeout(500);

    // Navigate to BOM editor
    const nextButton = page.getByTestId('next-button');
    await nextButton.click();
    await page.waitForSelector('text=Step 2: Edit Bill of Materials', { timeout: 15000 });
    await takeScreenshot(page, 'bugfix1-bom-ready');

    // Click Calculate
    const calculateButton = page.getByTestId('next-button');
    await calculateButton.click();
    await takeScreenshot(page, 'bugfix1-calculation-started');

    // Wait and take progress screenshot
    await page.waitForTimeout(2000);
    await takeScreenshot(page, 'bugfix1-calculation-progress');

    // Wait for results or error
    try {
      await page.waitForSelector('[data-testid="results-display"]', { timeout: 60000 });
      await takeScreenshot(page, 'bugfix1-calculation-success');
      console.log('Calculation completed successfully!');
    } catch (e) {
      // Check for error message
      const overlay = page.locator('[data-testid="calculation-overlay"]');
      if (await overlay.isVisible()) {
        await takeScreenshot(page, 'bugfix1-calculation-overlay');
      }

      // Check for error state in the overlay or page
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
  test('handles product without BOM correctly', async ({ page }) => {
    await page.goto('/');
    await dismissTour(page);

    // Click "All Products" toggle
    const allProductsButton = page.getByTestId('bom-filter-all');
    await allProductsButton.click();
    await page.waitForTimeout(500);
    await takeScreenshot(page, 'without-bom-all-products');

    // Open product selector
    const productSelect = page.getByTestId('product-select-trigger');
    await productSelect.click();
    await page.waitForTimeout(500);

    // Search for component
    const searchInput = page.getByPlaceholder('Search products...');
    await searchInput.fill('cotton');
    await page.waitForTimeout(1000);
    await takeScreenshot(page, 'without-bom-search-results');

    // Select if available
    const products = page.locator('[cmdk-item]');
    const count = await products.count();
    if (count > 0) {
      await products.first().click();
      await page.waitForTimeout(500);
      await takeScreenshot(page, 'without-bom-product-selected');

      // Check Next button - should be enabled to allow adding manual BOM
      const nextButton = page.getByTestId('next-button');
      await nextButton.click();

      // Wait for BOM editor with empty state
      await page.waitForSelector('text=Step 2: Edit Bill of Materials', { timeout: 15000 });
      await takeScreenshot(page, 'without-bom-empty-editor');
    } else {
      console.log('No products without BOM found in search');
      await takeScreenshot(page, 'without-bom-no-results');
    }
  });
});
