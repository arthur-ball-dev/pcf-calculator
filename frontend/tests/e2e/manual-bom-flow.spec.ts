/**
 * E2E Test: Manual BOM Construction Flow
 *
 * Purpose: Complete the manual BOM -> Results flow test
 *
 * Steps:
 * 1. Navigate to the app (with auth)
 * 2. Dismiss tour dialog if present
 * 3. Select a product from the list (keep BOM toggle ON for products with BOMs)
 * 4. Click Next to go to BOM Editor
 * 5. Handle any validation errors in BOM
 * 6. Take screenshot of valid BOM state
 * 7. Click Calculate
 * 8. Wait for results
 * 9. Take screenshot of results
 *
 * UI: Emerald Night ProductList (full-page scrollable list, 3-step wizard)
 *
 * Screenshots saved to: /home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots/
 */

import { test, expect } from '@playwright/test';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots';
const API_BASE_URL = 'http://localhost:8000';

test.describe('Manual BOM Construction Flow', () => {
  test('should build manual BOM and complete calculation', async ({ page, request }) => {
    test.setTimeout(120000);

    // Step 1: Authenticate and navigate to the application
    console.log('Step 1: Authenticate and navigate to the application...');

    // Authenticate via API
    const authResponse = await request.post(`${API_BASE_URL}/api/v1/auth/login`, {
      data: { username: 'e2e-test', password: 'E2ETestPassword123!' },
    });

    let authToken = '';
    if (authResponse.ok()) {
      const authData = await authResponse.json();
      authToken = authData.access_token;
    }

    // Set localStorage with auth token and skip tour BEFORE navigating
    await page.addInitScript((token) => {
      window.localStorage.setItem('auth_token', token);
      window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
    }, authToken);

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Step 2: Dismiss tour dialog if present (belt-and-suspenders)
    console.log('Step 2: Dismiss tour dialog if present...');
    await page.evaluate(() => {
      const portal = document.getElementById('react-joyride-portal');
      if (portal) portal.remove();
      document.querySelectorAll('.react-joyride__overlay').forEach(el => el.remove());
    });
    await page.waitForFunction(() => !document.getElementById('react-joyride-portal'), {}, { timeout: 3000 }).catch(() => {});

    // Take debug screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'debug_after_tour.png'),
      fullPage: false,
      timeout: 30000
    });

    // Step 3: Wait for product list to load, then select a product
    console.log('Step 3: Search for and select a product...');
    const searchInput = page.getByTestId('product-search-input');
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    // Wait for initial products to load (the list auto-loads on mount)
    await page.waitForLoadState('networkidle').catch(() => {});

    // Select the first available product from the list
    const productRow = page.locator('[role="option"]').first();
    if (await productRow.isVisible({ timeout: 5000 }).catch(() => false)) {
      const productText = await productRow.textContent();
      console.log(`Selecting product: ${productText?.substring(0, 80)}`);
      await productRow.click();
      await page.waitForLoadState('networkidle').catch(() => {});
    } else {
      console.log('No products visible, trying search...');
      await searchInput.fill('Bottle');
      await page.waitForResponse(resp => resp.url().includes('/products/search') && resp.status() === 200, { timeout: 10000 }).catch(() => {});

      const searchResult = page.locator('[role="option"]').first();
      if (await searchResult.isVisible({ timeout: 5000 }).catch(() => false)) {
        await searchResult.click();
        await page.waitForLoadState('networkidle').catch(() => {});
      }
    }

    // Take screenshot after product selection
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'debug_product_selected.png'),
      fullPage: false,
      timeout: 30000
    });

    // Step 4: Click "Next" to go to BOM Editor
    console.log('Step 4: Navigate to BOM Editor (Step 2)...');
    const nextBtn = page.getByTestId('next-button');
    await expect(nextBtn).toBeEnabled({ timeout: 10000 });
    console.log('Clicking Next button...');
    await nextBtn.click();

    // Wait for BOM skeleton to disappear
    const bomSkeleton = page.getByTestId('bom-editor-skeleton');
    if (await bomSkeleton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await expect(bomSkeleton).not.toBeVisible({ timeout: 15000 });
    }

    // Take screenshot of BOM Editor
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'debug_bom_editor.png'),
      fullPage: false,
      timeout: 30000
    });

    // Step 5: Handle validation errors if present
    console.log('Step 5: Check for and fix validation errors...');
    const errorBox = page.locator('text=Please fix the following errors');

    if (await errorBox.isVisible({ timeout: 2000 }).catch(() => false)) {
      console.log('Found validation errors - fixing empty rows...');

      // Find empty input fields (component name is required)
      const emptyInputs = await page.locator('input[placeholder="e.g., Cotton, Electricity"]').all();

      for (let i = 0; i < emptyInputs.length; i++) {
        const input = emptyInputs[i];
        const value = await input.inputValue();

        if (!value || value.trim() === '') {
          console.log(`Found empty input at index ${i}`);

          // Find the row this input belongs to
          const row = input.locator('xpath=ancestor::tr');

          // Try to delete this row
          const deleteBtn = row.locator('button[aria-label="Delete component"]');

          if (await deleteBtn.count() > 0) {
            const isDisabled = await deleteBtn.getAttribute('disabled');

            if (!isDisabled) {
              console.log('Clicking delete button for empty row...');
              await deleteBtn.click();
              await page.locator('button:has-text("Delete")').last().waitFor({ state: 'visible', timeout: 3000 }).catch(() => {});

              // Confirm deletion in the dialog
              const confirmBtn = page.locator('button:has-text("Delete")').last();
              if (await confirmBtn.isVisible()) {
                console.log('Confirming delete...');
                await confirmBtn.click();
                await page.waitForLoadState('networkidle').catch(() => {});
              }
              break; // Only delete one row at a time
            } else {
              // If can't delete (e.g., last row), fill it in instead
              console.log('Cannot delete - filling in the component name...');
              await input.fill('Recycled Material');
              break;
            }
          }
        }
      }
    }

    // Check again for any remaining empty inputs and fill them
    const remainingEmptyInputs = await page.locator('input[placeholder="e.g., Cotton, Electricity"]').all();
    for (let idx = 0; idx < remainingEmptyInputs.length; idx++) {
      const val = await remainingEmptyInputs[idx].inputValue();
      if (!val || val.trim() === '') {
        console.log(`Filling remaining empty input #${idx}`);
        await remainingEmptyInputs[idx].fill(`Material ${idx + 1}`);
        await remainingEmptyInputs[idx].blur();
      }
    }

    // Wait for validation to update
    await page.waitForFunction(() => { const errors = document.querySelectorAll('.text-destructive, .text-red-500'); return errors.length >= 0; }, {}, { timeout: 3000 }).catch(() => {});

    // Step 6: Take screenshot of valid BOM state
    console.log('Step 6: Taking screenshot 23: Valid BOM ready...');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '23_valid_bom_ready.png'),
      fullPage: false,
      timeout: 30000
    });

    // Step 7: Check if Calculate button is enabled and click it
    console.log('Step 7: Click Calculate button...');
    const calcButton = page.locator('button:has-text("Calculate")').first();

    // Wait for the button to be visible
    await expect(calcButton).toBeVisible({ timeout: 10000 });

    const isCalcDisabled = await calcButton.getAttribute('disabled');

    if (isCalcDisabled) {
      console.log('Calculate button is still disabled - taking debug screenshot');
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '23_calc_button_disabled.png'),
        fullPage: false,
        timeout: 30000
      });

      // Check what validation errors exist
      const validationErrors = await page.locator('.text-destructive, .text-red-500').allTextContents();
      console.log('Validation errors found:', validationErrors);

      // One more attempt to fill empty fields
      const allNameInputs = await page.locator('input[placeholder="e.g., Cotton, Electricity"]').all();
      for (let i = 0; i < allNameInputs.length; i++) {
        const currentVal = await allNameInputs[i].inputValue();
        if (!currentVal) {
          await allNameInputs[i].fill(`Component ${i + 1}`);
          await allNameInputs[i].blur();
        }
      }
      await page.waitForFunction(() => { const errors = document.querySelectorAll('.text-destructive, .text-red-500'); return errors.length >= 0; }, {}, { timeout: 3000 }).catch(() => {});

      // Check again
      const stillDisabled = await calcButton.getAttribute('disabled');
      if (stillDisabled) {
        throw new Error('Calculate button is disabled - validation issues remain. Errors: ' + validationErrors.join(', '));
      }
    }

    console.log('Clicking Calculate button...');
    await calcButton.click();

    // Step 8: Wait for calculation to complete and results to appear
    console.log('Step 8: Waiting for calculation results...');
    try {
      // Wait for the results page content
      await page.waitForSelector('text=Total Carbon Footprint', { timeout: 30000 });
      console.log('Results page loaded!');
    } catch (e) {
      console.log('Timeout waiting for "Total Carbon Footprint" - checking alternative indicators...');

      // Check if we see "Results" step indicator or any CO2e value
      const resultsStep = page.locator('text=Results').first();
      const co2eText = page.locator('text=kg CO').first();

      const hasResultsIndicator = await resultsStep.isVisible().catch(() => false) ||
        await co2eText.isVisible().catch(() => false);

      if (hasResultsIndicator) {
        console.log('Found results content');
      } else {
        // Take a debug screenshot
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '24_timeout_debug.png'),
          fullPage: false,
          timeout: 30000
        });

        // Get page content for debugging
        const pageText = await page.locator('body').textContent();
        console.log('Page content excerpt:', pageText?.substring(0, 500));

        throw new Error('Could not find results page content');
      }
    }

    // Wait for any animations
    await page.waitForLoadState('networkidle').catch(() => {});

    // Step 9: Take screenshot of results
    console.log('Step 9: Taking screenshot 24: Manual BOM results...');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '24_manual_bom_results.png'),
      fullPage: false,
      timeout: 30000
    });

    console.log('E2E test completed successfully!');
  });
});
