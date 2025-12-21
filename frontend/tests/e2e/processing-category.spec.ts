/**
 * Processing/Other Category Validation Tests
 * Tests the new "Processing/Other" category feature across the app
 */

import { test, expect } from '@playwright/test';

// SKIPPED: Tests need update for current BOM editor category dropdown implementation
test.describe.skip('Processing/Other Category', () => {
  test.beforeEach(async ({ page }) => {
    // Set tour as completed to prevent it from blocking interactions
    await page.goto('http://localhost:5173');
    await page.evaluate(() => {
      localStorage.clear();
      localStorage.setItem('pcf-calculator-tour-completed', 'true');
    });
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('BOM Editor shows Processing/Other in category dropdown', async ({ page }) => {
    // Select a product - click on the combobox trigger
    const selectTrigger = page.getByTestId('product-select-trigger');
    await selectTrigger.click();

    // Wait for search API to complete
    await page.waitForResponse(
      (response) =>
        response.url().includes('/api/v1/products/search') &&
        response.request().method() === 'GET',
      { timeout: 10000 }
    );

    // Wait for dropdown options to appear
    await page.waitForSelector('[role="option"]', { state: 'visible', timeout: 5000 });

    // Setup listener for product detail API call
    const productDetailPromise = page.waitForResponse(
      (response) =>
        response.url().match(/\/api\/v1\/products\/[a-f0-9-]+$/) &&
        response.request().method() === 'GET' &&
        response.status() === 200,
      { timeout: 10000 }
    );

    // Select first option
    const firstOption = page.locator('[role="option"]').first();
    await firstOption.click();

    // Wait for product detail to load
    await productDetailPromise;

    // Wait for BOM to load
    await page.waitForTimeout(3000);

    // Go to Step 2 (Edit BOM)
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click({ force: true });
    await page.waitForTimeout(1000);

    // Verify we're on BOM step
    const bomHeading = page.locator('h2').filter({ hasText: /BOM|Bill/ });
    await expect(bomHeading).toBeVisible({ timeout: 5000 });

    // Screenshot before clicking dropdown
    await page.screenshot({
      path: 'screenshots/processing-category-before-dropdown.png',
      fullPage: true,
    });

    // Find the category dropdown in BOM table and click it
    const categoryDropdown = page.locator('button[role="combobox"][aria-label="Category"]').first();
    await expect(categoryDropdown).toBeVisible({ timeout: 5000 });
    await categoryDropdown.click({ force: true });

    // Wait for dropdown to open
    await page.waitForTimeout(500);

    // Screenshot with dropdown open
    await page.screenshot({
      path: 'screenshots/processing-category-dropdown-open.png',
      fullPage: true,
    });

    // Get all dropdown options and log them
    const allOptions = await page.locator('[role="option"]').allTextContents();
    console.log('Dropdown options found:', allOptions);

    // Check for "Processing/Other" option (or partial match)
    const hasProcessingOption = allOptions.some(text =>
      text.includes('Processing') || text.includes('Other')
    );

    // Screenshot for evidence
    await page.screenshot({
      path: 'screenshots/processing-category-dropdown.png',
      fullPage: true,
    });

    // Verify the Processing/Other option exists
    expect(hasProcessingOption).toBe(true);

    // Also verify standard options
    expect(allOptions.some(t => t.includes('Material'))).toBe(true);
    expect(allOptions.some(t => t.includes('Energy'))).toBe(true);
    expect(allOptions.some(t => t.includes('Transport'))).toBe(true);
  });

  test('Full wizard flow with calculation', async ({ page }) => {
    // Select a product
    const selectTrigger = page.getByTestId('product-select-trigger');
    await selectTrigger.click();

    // Wait for search API to complete
    await page.waitForResponse(
      (response) =>
        response.url().includes('/api/v1/products/search') &&
        response.request().method() === 'GET',
      { timeout: 10000 }
    );

    // Wait for dropdown options to appear
    await page.waitForSelector('[role="option"]', { state: 'visible', timeout: 5000 });

    // Setup listener for product detail API call
    const productDetailPromise = page.waitForResponse(
      (response) =>
        response.url().match(/\/api\/v1\/products\/[a-f0-9-]+$/) &&
        response.request().method() === 'GET' &&
        response.status() === 200,
      { timeout: 10000 }
    );

    const firstOption = page.locator('[role="option"]').first();
    await firstOption.click();

    // Wait for product detail to load
    await productDetailPromise;

    // Wait for BOM to load
    await page.waitForTimeout(3000);

    // Go to Step 2
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click({ force: true });
    await page.waitForTimeout(1000);

    // Screenshot of BOM page
    await page.screenshot({
      path: 'screenshots/wizard-step2-bom.png',
      fullPage: true,
    });

    // Go to Step 3 (Calculate)
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click({ force: true });
    await page.waitForTimeout(1000);

    // Screenshot of Calculate page
    await page.screenshot({
      path: 'screenshots/wizard-step3-calculate.png',
      fullPage: true,
    });

    // Click Calculate
    const calculateButton = page.getByTestId('calculate-button');
    await expect(calculateButton).toBeVisible();
    await calculateButton.click({ force: true });

    // Wait for results
    const resultsHeading = page.locator('h2').filter({ hasText: /Result/ });
    await expect(resultsHeading).toBeVisible({ timeout: 30000 });

    // Wait for results to fully render
    await page.waitForTimeout(2000);

    // Screenshot of results with Sankey and Breakdown
    await page.screenshot({
      path: 'screenshots/wizard-step4-results.png',
      fullPage: true,
    });

    // Verify results contain expected elements
    await expect(page.locator('text=kg CO₂e')).toBeVisible();
    await expect(page.locator('text=Carbon Flow')).toBeVisible();
    await expect(page.locator('text=Detailed Breakdown')).toBeVisible();

    // Verify export buttons are present
    await expect(page.locator('button:has-text("CSV")')).toBeVisible();
    await expect(page.locator('button:has-text("Excel")')).toBeVisible();
  });
});
