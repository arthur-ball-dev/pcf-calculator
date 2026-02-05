/**
 * E2E Test: Manual BOM Construction Flow
 *
 * Purpose: Complete the manual BOM -> Results flow test
 *
 * Steps:
 * 1. Navigate to the app
 * 2. Dismiss tour dialog if present
 * 3. Click "All Products" to see products without BOM
 * 4. Select a product without existing BOM (or any product)
 * 5. Add manual BOM components
 * 6. Handle any validation errors
 * 7. Take screenshot of valid BOM state
 * 8. Click Calculate
 * 9. Wait for results
 * 10. Take screenshot of results
 *
 * Screenshots saved to: /home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots/
 */

import { test, expect } from '@playwright/test';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots';

test.describe('Manual BOM Construction Flow', () => {
  test('should build manual BOM and complete calculation', async ({ page }) => {
    // Navigate to the application
    console.log('Step 1: Navigate to the application...');
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Wait for any loading animations

    // Step 2: Dismiss tour dialog if present
    console.log('Step 2: Dismiss tour dialog if present...');
    const tourDialog = page.locator('text=Step 1: Select a Product').first();
    if (await tourDialog.isVisible()) {
      console.log('Tour dialog found - clicking Finish/Skip...');
      // Try to click "Finish" or "Skip tour"
      const finishBtn = page.locator('button:has-text("Finish")');
      const skipLink = page.locator('text=Skip tour');

      if (await finishBtn.isVisible()) {
        await finishBtn.click();
      } else if (await skipLink.isVisible()) {
        await skipLink.click();
      }
      await page.waitForTimeout(500);
    }

    // Take debug screenshot
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'debug_after_tour.png'),
      fullPage: true
    });

    // Step 3: Click "All Products" to see products without BOM
    console.log('Step 3: Click All Products to see all products...');
    const allProductsBtn = page.locator('button:has-text("All Products")');
    if (await allProductsBtn.isVisible()) {
      await allProductsBtn.click();
      await page.waitForTimeout(500);
    }

    // Step 4: Click on the product selector (combobox)
    console.log('Step 4: Open product selector...');
    const productTrigger = page.locator('[data-testid="product-select-trigger"]').or(
      page.locator('button[role="combobox"]:has-text("Search and select")')
    );

    if (await productTrigger.count() > 0) {
      await productTrigger.first().click();
      await page.waitForTimeout(500);

      // Search for a product (e.g., "Mug" or "Coffee")
      console.log('Searching for a product...');
      const searchInput = page.locator('input[placeholder*="Search"]').first();
      if (await searchInput.isVisible()) {
        await searchInput.fill('Coffee');
        await page.waitForTimeout(1000);
      }

      // Click the first product result
      const productOption = page.locator('[role="option"]').first();
      if (await productOption.isVisible()) {
        console.log('Selecting product...');
        await productOption.click();
        await page.waitForTimeout(1000);
      }
    }

    // Wait for page to update
    await page.waitForTimeout(1000);

    // Take screenshot after product selection
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'debug_product_selected.png'),
      fullPage: true
    });

    // Step 5: Click "Next" to go to BOM Editor if we're on Step 1
    console.log('Step 5: Navigate to BOM Editor (Step 2)...');
    const nextBtn = page.locator('button:has-text("Next")');
    if (await nextBtn.isVisible()) {
      const isNextDisabled = await nextBtn.getAttribute('disabled');
      if (!isNextDisabled) {
        console.log('Clicking Next button...');
        await nextBtn.click();
        await page.waitForTimeout(1000);
      }
    }

    // Take screenshot of BOM Editor
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'debug_bom_editor.png'),
      fullPage: true
    });

    // Step 6: Handle validation errors if present
    console.log('Step 6: Check for and fix validation errors...');
    const errorBox = page.locator('text=Please fix the following errors');

    if (await errorBox.isVisible()) {
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
              await page.waitForTimeout(500);

              // Confirm deletion in the dialog
              const confirmBtn = page.locator('button:has-text("Delete")').last();
              if (await confirmBtn.isVisible()) {
                console.log('Confirming delete...');
                await confirmBtn.click();
                await page.waitForTimeout(500);
              }
              break; // Only delete one row at a time
            } else {
              // If can't delete (e.g., last row), fill it in instead
              console.log('Cannot delete - filling in the component name...');
              await input.fill('Recycled Material');
              await page.waitForTimeout(500);
              break;
            }
          }
        }
      }
    }

    // Check again for any remaining empty inputs and fill them
    await page.waitForTimeout(500);
    const remainingEmptyInputs = await page.locator('input[placeholder="e.g., Cotton, Electricity"]').all();
    for (let idx = 0; idx < remainingEmptyInputs.length; idx++) {
      const val = await remainingEmptyInputs[idx].inputValue();
      if (!val || val.trim() === '') {
        console.log(`Filling remaining empty input #${idx}`);
        await remainingEmptyInputs[idx].fill(`Material ${idx + 1}`);
        // Trigger blur to run validation
        await remainingEmptyInputs[idx].blur();
        await page.waitForTimeout(300);
      }
    }

    // Wait for validation to update
    await page.waitForTimeout(1000);

    // Step 7: Take screenshot of valid BOM state
    console.log('Step 7: Taking screenshot 23: Valid BOM ready...');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '23_valid_bom_ready.png'),
      fullPage: true
    });

    // Step 8: Check if Calculate button is enabled and click it
    console.log('Step 8: Click Calculate button...');
    const calcButton = page.locator('button:has-text("Calculate")');

    // Wait for the button to be visible
    await expect(calcButton).toBeVisible({ timeout: 10000 });

    const isCalcDisabled = await calcButton.getAttribute('disabled');

    if (isCalcDisabled) {
      console.log('Calculate button is still disabled - taking debug screenshot');
      await page.screenshot({
        path: path.join(SCREENSHOT_DIR, '23_calc_button_disabled.png'),
        fullPage: true
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
          await page.waitForTimeout(300);
        }
      }
      await page.waitForTimeout(1000);

      // Check again
      const stillDisabled = await calcButton.getAttribute('disabled');
      if (stillDisabled) {
        throw new Error('Calculate button is disabled - validation issues remain. Errors: ' + validationErrors.join(', '));
      }
    }

    console.log('Clicking Calculate button...');
    await calcButton.click();

    // Step 9: Wait for calculation to complete and results to appear
    console.log('Step 9: Waiting for calculation results...');
    try {
      // Wait for the results page content
      await page.waitForSelector('text=Total Carbon Footprint', { timeout: 30000 });
      console.log('Results page loaded!');
    } catch (e) {
      console.log('Timeout waiting for "Total Carbon Footprint" - checking alternative indicators...');

      // Check if we see "Results" step indicator or any CO2e value
      const resultsStep = page.locator('text=Results').first();
      const co2eText = page.locator('text=kg CO').first();
      const step3Active = page.locator('[data-state="active"]:has-text("3")').or(
        page.locator('.bg-primary:has-text("3")')
      );

      const hasResultsIndicator = await resultsStep.isVisible() ||
        await co2eText.isVisible() ||
        await step3Active.isVisible();

      if (hasResultsIndicator) {
        console.log('Found results content');
      } else {
        // Take a debug screenshot
        await page.screenshot({
          path: path.join(SCREENSHOT_DIR, '24_timeout_debug.png'),
          fullPage: true
        });

        // Get page content for debugging
        const pageText = await page.locator('body').textContent();
        console.log('Page content excerpt:', pageText?.substring(0, 500));

        throw new Error('Could not find results page content');
      }
    }

    // Wait for any animations
    await page.waitForTimeout(1000);

    // Step 10: Take screenshot of results
    console.log('Step 10: Taking screenshot 24: Manual BOM results...');
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '24_manual_bom_results.png'),
      fullPage: true
    });

    console.log('E2E test completed successfully!');
  });
});
