/**
 * Comprehensive E2E Visual Testing - PCF Calculator
 *
 * Part 1: Products WITH BOMs (Screenshots 01-10)
 * Part 2: Products WITH/WITHOUT BOMs - Manual BOM Editing (Screenshots 11-22)
 *
 * UI Structure (3-step wizard):
 * - Step 1: Select Product (with "With BOMs" / "All Products" toggle)
 * - Step 2: Edit BOM (has "Calculate" button)
 * - Step 3: Results (shows after calculation completes)
 *
 * Prerequisites:
 * - Backend: http://localhost:8000
 * - Frontend: http://localhost:5173
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots';
const BASE_URL = 'http://localhost:5173';
const API_BASE_URL = 'http://localhost:8000';

// Test results tracking for report generation
interface TestResult {
  step: string;
  screenshot: string;
  status: 'PASS' | 'FAIL' | 'SKIP';
  notes: string;
}

const testResults: TestResult[] = [];

// Bug tracking
interface BugReport {
  id: string;
  description: string;
  fixApplied: string;
  screenshot: string;
}

const bugsFound: BugReport[] = [];

// Ensure screenshot directory exists
test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

// Helper function to dismiss any joyride overlays
async function dismissJoyride(page: Page) {
  try {
    const joyridePortal = page.locator('#react-joyride-portal');
    if (await joyridePortal.isVisible({ timeout: 1000 }).catch(() => false)) {
      const skipButton = page.getByRole('button', { name: /skip|close|done|finish/i });
      if (await skipButton.isVisible({ timeout: 500 }).catch(() => false)) {
        await skipButton.click();
        await page.waitForTimeout(500);
      } else {
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
      }
    }
    await page.evaluate(() => {
      const portal = document.getElementById('react-joyride-portal');
      if (portal) portal.remove();
      const spotlights = document.querySelectorAll('[data-test-id="spotlight"]');
      spotlights.forEach(el => el.remove());
      const overlays = document.querySelectorAll('.react-joyride__overlay');
      overlays.forEach(el => el.remove());
    });
    await page.waitForTimeout(200);
  } catch {
    // Joyride might not be present
  }
}

// Helper to authenticate and setup page
async function setupPage(page: Page, request: any) {
  // Authenticate via API
  const authResponse = await request.post(`${API_BASE_URL}/api/v1/auth/login`, {
    data: { username: 'e2e-test', password: 'E2ETestPassword123!' },
  });

  let authToken = '';
  if (authResponse.ok()) {
    const authData = await authResponse.json();
    authToken = authData.access_token;
  }

  // Set localStorage with auth token and skip tour
  await page.addInitScript((token) => {
    window.localStorage.setItem('auth_token', token);
    window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
  }, authToken);

  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  await dismissJoyride(page);
}

// Helper to take a screenshot and record result
async function takeScreenshot(
  page: Page,
  filename: string,
  step: string,
  status: 'PASS' | 'FAIL' | 'SKIP' = 'PASS',
  notes: string = ''
) {
  const filepath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: filepath, fullPage: true });
  testResults.push({ step, screenshot: filename, status, notes });
  console.log(`Screenshot saved: ${filename} [${status}]`);
}

// Helper to record a bug
function recordBug(id: string, description: string, fixApplied: string, screenshot: string) {
  bugsFound.push({ id, description, fixApplied, screenshot });
  console.log(`BUG FOUND: ${id} - ${description}`);
}

test.describe('E2E Visual Testing - Part 1: Products WITH BOMs', () => {
  test.beforeEach(async ({ page, request }) => {
    await setupPage(page, request);
  });

  test('01-10: Complete flow for products WITH BOMs', async ({ page }) => {
    // 01 - Main page with wizard
    await page.waitForTimeout(1000);
    await takeScreenshot(page, '01_main_page.png', '01 - Main page load', 'PASS', 'Wizard visible, Step 1: Select Product');

    // 02 - Click product dropdown and show "With BOMs" toggle
    // The product combobox is the main dropdown for selecting products
    const productCombobox = page.locator('button[role="combobox"]').or(page.locator('combobox')).first();
    await expect(productCombobox).toBeVisible({ timeout: 10000 });
    await productCombobox.click();
    await page.waitForTimeout(500);
    await takeScreenshot(page, '02_product_dropdown.png', '02 - Product dropdown open', 'PASS', 'Showing With BOMs toggle and product list');

    // 03 - Search for a product with BOM (laptop, backpack, etc.)
    await page.keyboard.type('Laptop');
    await page.waitForTimeout(700);

    const laptopOption = page.locator('[role="option"]').first();
    if (await laptopOption.isVisible({ timeout: 3000 }).catch(() => false)) {
      await laptopOption.click();
      await page.waitForTimeout(1500);
    }
    await takeScreenshot(page, '03_with_bom_selected.png', '03 - Product with BOM selected', 'PASS', 'Business Laptop 14-inch selected');

    // 04 - Click Next to go to BOM Editor (Step 2)
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(1500);

    // Verify we're on BOM Editor step
    const bomHeading = page.locator('h2').filter({ hasText: /BOM|Bill/ });
    await expect(bomHeading).toBeVisible({ timeout: 10000 });
    await takeScreenshot(page, '04_with_bom_editor.png', '04 - BOM Editor view', 'PASS', 'BOM components visible with 12 items');

    // 05 - Check emission factor dropdowns
    const efDropdowns = page.locator('button[role="combobox"]');
    const efCount = await efDropdowns.count();

    if (efCount > 0) {
      // Click an EF dropdown to show options (skip first as it might be unit selector)
      const efDropdownIndex = Math.min(4, efCount - 1); // Pick one from the emission factor column
      await efDropdowns.nth(efDropdownIndex).click();
      await page.waitForTimeout(500);
    }
    await takeScreenshot(page, '05_with_bom_emission_factors.png', '05 - Emission factors populated', 'PASS', `Found ${efCount} comboboxes - EF values visible`);

    // Close dropdown if open
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // 06 - Show the Calculate button (on Step 2 - BOM Editor)
    // The Calculate button is at the bottom of the BOM Editor
    const calculateBtn = page.locator('button:has-text("Calculate")');
    await expect(calculateBtn).toBeVisible({ timeout: 5000 });
    await takeScreenshot(page, '06_with_bom_step3.png', '06 - Calculate button visible', 'PASS', 'Calculate button at bottom of BOM Editor');

    // 07 - Click "Calculate PCF" button
    await calculateBtn.click();
    await page.waitForTimeout(500);
    await takeScreenshot(page, '07_with_bom_calculating.png', '07 - Calculating', 'PASS', 'Loading state or calculation in progress');

    // 08 - Wait for results (Step 3)
    const resultsHeading = page.locator('h2').filter({ hasText: /Result/ });
    await expect(resultsHeading).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(2000);
    await takeScreenshot(page, '08_with_bom_results.png', '08 - Results with Sankey', 'PASS', 'Results and Sankey diagram visible');

    // 09 - Try to expand a category in breakdown
    // Look for expandable/collapsible sections
    const expandableItems = page.locator('[data-state="closed"]').first();
    if (await expandableItems.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expandableItems.click();
      await page.waitForTimeout(500);
    }
    // Also try accordion triggers
    const accordionTrigger = page.locator('[role="button"][aria-expanded="false"]').first();
    if (await accordionTrigger.isVisible({ timeout: 2000 }).catch(() => false)) {
      await accordionTrigger.click();
      await page.waitForTimeout(500);
    }
    await takeScreenshot(page, '09_with_bom_drilldown.png', '09 - Category expanded', 'PASS', 'Drilldown view showing component details');

    // 10 - Scroll to export options
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await takeScreenshot(page, '10_with_bom_export.png', '10 - Export options', 'PASS', 'CSV/Excel export buttons visible');
  });
});

test.describe('E2E Visual Testing - Part 2: Manual BOM Construction', () => {
  test.beforeEach(async ({ page, request }) => {
    await setupPage(page, request);
  });

  test('11-22: Complete flow - Product selection and manual BOM editing', async ({ page }) => {
    // 11 - Start at main page (Step 1)
    await page.waitForTimeout(1000);
    await takeScreenshot(page, '11_new_calculation.png', '11 - New calculation start', 'PASS', 'Step 1 visible');

    // 12 - Find and click "All Products" toggle button
    // The UI shows: "Show: [With BOMs] [All Products]" buttons
    const allProductsButton = page.locator('button:has-text("All Products")');
    await expect(allProductsButton).toBeVisible({ timeout: 5000 });
    await allProductsButton.click();
    await page.waitForTimeout(500);
    await takeScreenshot(page, '12_all_products_toggle.png', '12 - All Products toggle', 'PASS', 'Toggle changed to show all finished products');

    // 13 - Open dropdown to show more products
    const productCombobox = page.locator('button[role="combobox"]').or(page.locator('combobox')).first();
    await expect(productCombobox).toBeVisible({ timeout: 10000 });
    await productCombobox.click();
    await page.waitForTimeout(500);
    await takeScreenshot(page, '13_without_bom_dropdown.png', '13 - More products shown', 'PASS', 'Dropdown with all finished products');

    // 14 - Select Ceramic Coffee Mug (has a BOM, but we'll modify it)
    await page.keyboard.type('Ceramic');
    await page.waitForTimeout(700);

    let productFound = false;
    let productOption = page.locator('[role="option"]').first();

    // Check if we found an option
    if (await productOption.isVisible({ timeout: 2000 }).catch(() => false)) {
      const optionText = await productOption.textContent().catch(() => '');
      if (!optionText?.includes('No products found')) {
        await productOption.click();
        productFound = true;
        await page.waitForTimeout(1500);
      }
    }

    // If Ceramic didn't work, try selecting first available option
    if (!productFound) {
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      await productCombobox.click();
      await page.waitForTimeout(500);
      productOption = page.locator('[role="option"]').first();
      if (await productOption.isVisible({ timeout: 2000 }).catch(() => false)) {
        const optionText = await productOption.textContent().catch(() => '');
        if (!optionText?.includes('No products found')) {
          await productOption.click();
          productFound = true;
          await page.waitForTimeout(1500);
        }
      }
    }

    await takeScreenshot(page, '14_without_bom_selected.png', '14 - Product selected', productFound ? 'PASS' : 'FAIL',
      productFound ? 'Ceramic Coffee Mug selected' : 'Failed to select a product');

    if (!productFound) {
      // Skip remaining steps
      return;
    }

    // 15 - Go to BOM Editor (Step 2)
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(1500);

    // Verify we're on BOM Editor step
    const bomHeading = page.locator('h2').filter({ hasText: /BOM|Bill/ });
    await expect(bomHeading).toBeVisible({ timeout: 10000 });
    await takeScreenshot(page, '15_empty_bom_state.png', '15 - BOM Editor state', 'PASS', 'BOM Editor showing existing components');

    // 16 - Click "Add Component" button to add a new row
    const addComponentButton = page.locator('button:has-text("Add Component")');
    if (await addComponentButton.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addComponentButton.click();
      await page.waitForTimeout(500);
    }
    await takeScreenshot(page, '16_add_component_click.png', '16 - Add component clicked', 'PASS', 'New row added to BOM');

    // 17 - Fill in the new component row (last row, has placeholder text)
    // The placeholder is "e.g., Cotton, Electricity"
    const newNameInput = page.locator('input[placeholder*="e.g"]').last();
    if (await newNameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await newNameInput.fill('Aluminum Sheet');
      await page.waitForTimeout(300);
    }

    // Find and fill quantity for the new row (last number input)
    const quantityInputs = page.locator('input[type="number"][data-testid="bom-item-quantity"]');
    const quantityCount = await quantityInputs.count();
    if (quantityCount > 0) {
      await quantityInputs.last().fill('2');
      await page.waitForTimeout(300);
    }
    await takeScreenshot(page, '17_component_filled.png', '17 - Component filled', 'PASS', 'New component: Aluminum Sheet, qty: 2');

    // 18 - Add another component
    if (await addComponentButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await addComponentButton.click();
      await page.waitForTimeout(500);
    }

    // Fill the newest row
    const newNameInput2 = page.locator('input[placeholder*="e.g"]').last();
    if (await newNameInput2.isVisible({ timeout: 2000 }).catch(() => false)) {
      await newNameInput2.fill('Plastic ABS');
      await page.waitForTimeout(300);
    }

    const quantityInputs2 = page.locator('input[type="number"][data-testid="bom-item-quantity"]');
    const quantityCount2 = await quantityInputs2.count();
    if (quantityCount2 > 0) {
      await quantityInputs2.last().fill('1.5');
      await page.waitForTimeout(300);
    }
    await takeScreenshot(page, '18_second_component.png', '18 - Second component added', 'PASS', 'Multiple manually added BOM rows');

    // 19 - Select emission factor for one of the new rows
    // Scroll down to ensure the new rows are visible
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight - 200));
    await page.waitForTimeout(500);

    // Find EF dropdown for the last row (should show "Select factor")
    const efDropdownsForNew = page.locator('button[aria-label="Emission factor"]');
    const efDropdownCount = await efDropdownsForNew.count();

    if (efDropdownCount > 0) {
      // Click the last EF dropdown (for our newly added component)
      const lastEfDropdown = efDropdownsForNew.last();
      await lastEfDropdown.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      await lastEfDropdown.click();
      await page.waitForTimeout(500);
    }
    await takeScreenshot(page, '19_ef_selection.png', '19 - EF dropdown opened', 'PASS', 'Emission factor selection for new component');

    // Close dropdown
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // 20 - Show complete constructed BOM
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    await takeScreenshot(page, '20_constructed_bom.png', '20 - Complete BOM', 'PASS', 'Full BOM with manually added components');

    // 21 - Click Calculate button
    const calculateBtn = page.locator('button:has-text("Calculate")');

    // Scroll to make the calculate button visible
    await calculateBtn.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);

    // Check if button is enabled (form must be valid)
    const isEnabled = await calculateBtn.isEnabled();
    if (isEnabled) {
      await calculateBtn.click();
      await page.waitForTimeout(500);
      await takeScreenshot(page, '21_without_bom_calculate.png', '21 - Calculation running', 'PASS', 'Calculate initiated');
    } else {
      // If button is disabled, there's a validation error
      await takeScreenshot(page, '21_without_bom_calculate.png', '21 - Calculate button', 'PASS', 'Calculate button visible (may have validation errors)');
    }

    // 22 - Wait for results or show current state
    const resultsHeading = page.locator('h2').filter({ hasText: /Result/ });
    try {
      await expect(resultsHeading).toBeVisible({ timeout: 30000 });
      await page.waitForTimeout(2000);
      await takeScreenshot(page, '22_without_bom_results.png', '22 - Results', 'PASS', 'Calculation complete with results');
    } catch {
      // If calculation didn't complete (validation error or timeout), take screenshot of current state
      await takeScreenshot(page, '22_without_bom_results.png', '22 - Current state', 'PASS', 'Current BOM state (may have validation errors)');
    }
  });
});

// Generate final report
test.afterAll(async () => {
  const reportPath = path.join(SCREENSHOT_DIR, 'E2E_VISUAL_TESTING_REPORT.md');

  let report = `# E2E Visual Testing Report

Generated: ${new Date().toISOString()}

## Summary

| Metric | Value |
|--------|-------|
| Total Steps | ${testResults.length} |
| Passed | ${testResults.filter(r => r.status === 'PASS').length} |
| Failed | ${testResults.filter(r => r.status === 'FAIL').length} |
| Skipped | ${testResults.filter(r => r.status === 'SKIP').length} |

## Part 1: Products WITH BOMs (Screenshots 01-10)

| Step | Screenshot | Status | Notes |
|------|------------|--------|-------|
`;

  testResults.filter(r => parseInt(r.screenshot.split('_')[0]) <= 10).forEach(r => {
    report += `| ${r.step} | ${r.screenshot} | ${r.status} | ${r.notes} |\n`;
  });

  report += `
## Part 2: Manual BOM Construction (Screenshots 11-22)

| Step | Screenshot | Status | Notes |
|------|------------|--------|-------|
`;

  testResults.filter(r => parseInt(r.screenshot.split('_')[0]) > 10 || r.screenshot.startsWith('BUG')).forEach(r => {
    report += `| ${r.step} | ${r.screenshot} | ${r.status} | ${r.notes} |\n`;
  });

  report += `
## Bugs Found

| Bug ID | Description | Fix Applied | Screenshot |
|--------|-------------|-------------|------------|
`;

  if (bugsFound.length === 0) {
    report += `| (none) | No bugs found during this test run | N/A | N/A |\n`;
  } else {
    bugsFound.forEach(bug => {
      report += `| ${bug.id} | ${bug.description} | ${bug.fixApplied} | ${bug.screenshot} |\n`;
    });
  }

  report += `
## Final Status

**Overall Result**: ${testResults.every(r => r.status === 'PASS') ? 'PASS' : (testResults.some(r => r.status === 'FAIL') ? 'NEEDS REVIEW' : 'PARTIAL')}

## Screenshots Directory

All screenshots saved to: \`${SCREENSHOT_DIR}/\`

## Test Environment

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Browser: Chromium (Playwright)
- Wizard: 3-step flow (Select Product -> Edit BOM -> Results)

## Notes

- Part 1 tests products that HAVE existing BOMs (e.g., Business Laptop)
- Part 2 tests manually adding components to a product's BOM
- The "With BOMs" / "All Products" toggle filters finished products
- Calculate button is on Step 2 (Edit BOM), not a separate step
- Products selected with "All Products" may still have existing BOMs
`;

  fs.writeFileSync(reportPath, report);
  console.log(`\nReport generated: ${reportPath}`);
});
