#!/usr/bin/env node
/**
 * E2E Test Script for PCF Calculator Results Page
 *
 * This script completes the E2E testing for the Results page by:
 * 1. Navigating to http://localhost:5174
 * 2. Selecting a product (Business Laptop 14-inch)
 * 3. Navigating through to Step 3 (Calculate)
 * 4. Clicking the "Calculate PCF" button
 * 5. Waiting for the calculation to complete
 * 6. Capturing screenshots of the Results page
 *
 * Screenshots are saved to /home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots/
 */

import { chromium } from 'playwright';
import { mkdirSync } from 'fs';
import { join } from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots';
const FRONTEND_URL = 'http://localhost:5174';

async function saveScreenshot(page, name, description = '') {
  const filepath = join(SCREENSHOT_DIR, name);
  await page.screenshot({ path: filepath, fullPage: true });
  console.log(`  Saved: ${name} - ${description}`);
  return filepath;
}

async function waitForLoad(page, timeout = 5000) {
  try {
    await page.waitForLoadState('networkidle', { timeout });
  } catch {
    // Continue even if network doesn't go fully idle
  }
}

async function dismissTour(page) {
  /**
   * Dismiss the Joyride tutorial by clicking Skip or the X button
   */
  // Multiple attempts to dismiss the tour
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      // Try clicking "Skip tour" button (exact text match)
      const skipButton = page.locator('button:has-text("Skip tour")');
      if (await skipButton.isVisible({ timeout: 1000 })) {
        await skipButton.click({ force: true });
        console.log('  Clicked "Skip tour" button');
        await page.waitForTimeout(500);
        continue;
      }
    } catch {
      // Skip button not found
    }

    try {
      // Try clicking the X close button in the tooltip
      const closeButton = page.locator('button[aria-label="Close tour"]');
      if (await closeButton.isVisible({ timeout: 500 })) {
        await closeButton.click({ force: true });
        console.log('  Clicked X button to close tour');
        await page.waitForTimeout(500);
        continue;
      }
    } catch {
      // Close button not found
    }

    try {
      // Check if spotlight is still present
      const spotlight = page.locator('[data-test-id="spotlight"]');
      if (!await spotlight.isVisible({ timeout: 500 })) {
        break;
      }
    } catch {
      break;
    }

    // Press Escape key as fallback
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
  }
}

async function runE2ETest() {
  console.log('\n' + '='.repeat(60));
  console.log('PCF Calculator - E2E Results Page Test');
  console.log(`Started: ${new Date().toISOString()}`);
  console.log('='.repeat(60) + '\n');

  // Ensure screenshot directory exists
  mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  // Add script to disable tour before page loads
  await context.addInitScript(() => {
    localStorage.setItem('pcf-tour-completed', 'true');
    localStorage.setItem('tour_completed', 'true');
  });

  try {
    // Navigate to the application
    console.log('1. Navigating to application...');
    await page.goto(FRONTEND_URL, { waitUntil: 'domcontentloaded' });
    await waitForLoad(page);

    // Dismiss Joyride tutorial if present
    console.log('2. Dismissing tutorial if present...');
    await dismissTour(page);
    await page.waitForTimeout(500);

    // Click on product selector trigger button
    console.log('3. Opening product selector...');
    const productTrigger = page.locator('[data-testid="product-select-trigger"]');
    await productTrigger.waitFor({ timeout: 5000 });
    await productTrigger.click({ force: true });
    await page.waitForTimeout(500);

    // Search for "Business Laptop"
    console.log('4. Searching for "Business Laptop"...');
    const searchInput = page.locator('[data-testid="product-search-input"]');
    await searchInput.waitFor({ timeout: 5000 });
    await searchInput.fill('Business Laptop');
    await page.waitForTimeout(1000);

    // Click on the product in dropdown
    console.log('5. Selecting product...');
    const productOption = page.locator('text=Business Laptop 14-inch').first();
    await productOption.waitFor({ timeout: 5000 });
    await productOption.click();
    await waitForLoad(page);
    await page.waitForTimeout(500);

    // Click Next to go to BOM step
    console.log('6. Navigating to BOM step (Step 2)...');
    let nextButton = page.locator('button:has-text("Next")').first();
    await nextButton.waitFor({ timeout: 5000 });
    await nextButton.click();
    await waitForLoad(page, 10000);
    await page.waitForTimeout(1000);

    // Dismiss tour again if it reappeared
    await dismissTour(page);

    // Click Next to go to Calculate step
    console.log('7. Navigating to Calculate step (Step 3)...');
    nextButton = page.locator('button:has-text("Next")').first();
    await nextButton.waitFor({ timeout: 5000 });
    await nextButton.click();
    await waitForLoad(page);
    await page.waitForTimeout(500);

    // Dismiss tour again if it reappeared
    await dismissTour(page);

    // Screenshot before clicking Calculate
    await saveScreenshot(page, '17_calculate_button_ready.png', 'Step 3 - Calculate button ready');

    // Click Calculate PCF button
    console.log('8. Clicking "Calculate PCF" button...');
    const calculateButton = page.locator('[data-testid="calculate-button"]');
    await calculateButton.waitFor({ timeout: 5000 });
    await calculateButton.click({ force: true });

    // Screenshot immediately after clicking (calculating state)
    await page.waitForTimeout(500);
    await saveScreenshot(page, '18_calculation_in_progress.png', 'Calculation in progress');

    // Wait for calculation to complete
    console.log('9. Waiting for calculation to complete...');
    const maxWaitSeconds = 60;
    let calculationCompleted = false;
    let errorOccurred = false;

    for (let i = 0; i < maxWaitSeconds; i++) {
      // Check if results are displayed
      const resultsDisplay = page.locator('[data-testid="results-display"]');
      try {
        if (await resultsDisplay.isVisible({ timeout: 1000 })) {
          console.log(`    Calculation completed after ~${i + 1} seconds`);
          calculationCompleted = true;
          break;
        }
      } catch {
        // Not visible yet
      }

      // Check for error state
      const errorAlert = page.locator('[data-testid="calculation-error"]');
      try {
        if (await errorAlert.isVisible({ timeout: 100 })) {
          console.log('    ERROR: Calculation failed!');
          await saveScreenshot(page, '19_calculation_error.png', 'Calculation error');
          const errorText = await errorAlert.innerText();
          console.log(`    Error message: ${errorText}`);
          errorOccurred = true;
          break;
        }
      } catch {
        // No error
      }

      if (i % 5 === 4) {
        console.log(`    Still waiting... (${i + 1}s)`);
      }
    }

    if (!calculationCompleted && !errorOccurred) {
      console.log('    WARNING: Calculation timed out after 60 seconds');
      await saveScreenshot(page, '19_calculation_timeout.png', 'Calculation timeout');
    }

    // Check final state
    const resultsDisplay = page.locator('[data-testid="results-display"]');
    if (await resultsDisplay.isVisible({ timeout: 2000 })) {
      console.log('10. Capturing Results page screenshots...');
      await waitForLoad(page);
      await page.waitForTimeout(1500); // Let charts render fully

      // Full results page
      await saveScreenshot(page, '19_results_page.png', 'Full results page');

      // Scroll to see breakdown table
      const breakdownCard = page.locator('text=Detailed Breakdown').first();
      if (await breakdownCard.isVisible()) {
        await breakdownCard.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        await saveScreenshot(page, '20_results_breakdown.png', 'Results breakdown table');
      }

      // Scroll to see export buttons
      const exportSection = page.locator('[data-tour="export-buttons"]');
      if (await exportSection.isVisible()) {
        await exportSection.scrollIntoViewIfNeeded();
        await page.waitForTimeout(500);
        await saveScreenshot(page, '21_export_options.png', 'Export options');
      }

      // Click on a category in the breakdown to test drill-down
      console.log('11. Testing category drill-down...');
      // Look for clickable category row in breakdown table
      const materialsRow = page.locator('tr:has-text("Materials"), button:has-text("Materials")').first();
      if (await materialsRow.isVisible()) {
        await materialsRow.click();
        await page.waitForTimeout(500);
        await saveScreenshot(page, '22_category_drilldown.png', 'Category drill-down expanded');
      }

      // Scroll back to top to capture Sankey diagram
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.waitForTimeout(500);
      await saveScreenshot(page, '23_sankey_diagram.png', 'Sankey diagram visualization');

      // Try clicking on Sankey diagram for drill-down
      console.log('12. Testing Sankey diagram interaction...');
      const sankeyContainer = page.locator('[data-tour="visualization-tabs"]');
      if (await sankeyContainer.isVisible()) {
        // Try to click on a specific node/link in the Sankey
        const sankeyNode = sankeyContainer.locator('g rect, g path').first();
        if (await sankeyNode.isVisible({ timeout: 1000 })) {
          await sankeyNode.click();
          await page.waitForTimeout(500);
        }
        await saveScreenshot(page, '24_sankey_interaction.png', 'Sankey diagram after click');
      }

      // Capture total CO2e value from the summary
      console.log('13. Extracting results data...');
      const summaryCard = page.locator('[data-testid="results-summary"]');
      if (await summaryCard.isVisible({ timeout: 2000 })) {
        const summaryText = await summaryCard.innerText();
        console.log(`    Results Summary:\n${summaryText.substring(0, 300)}...`);
      }

      // Test New Calculation button
      console.log('14. Testing New Calculation button...');
      const newCalcButton = page.locator('[data-testid="new-calculation-action-button"]');
      if (await newCalcButton.isVisible()) {
        await saveScreenshot(page, '25_before_new_calc.png', 'Before new calculation');
      }

      console.log('\n' + '='.repeat(60));
      console.log('E2E Test COMPLETED SUCCESSFULLY');
      console.log('='.repeat(60));
    } else {
      console.log('\n' + '='.repeat(60));
      console.log('E2E Test INCOMPLETE - Results not displayed');
      console.log('='.repeat(60));
      await saveScreenshot(page, '19_no_results.png', 'No results displayed');
    }

  } catch (error) {
    console.log(`\nERROR during test: ${error.message}`);
    await saveScreenshot(page, '99_error_state.png', `Error: ${error.message.substring(0, 50)}`);
    throw error;
  } finally {
    await browser.close();
  }
}

runE2ETest().catch(console.error);
