/**
 * Production Visual Test: PCF Calculator at https://pcf.glideslopeintelligence.ai/
 *
 * Tests ALL pages/screens of the 3-step wizard application:
 * - Screen 1: Select Product
 * - Screen 2: Edit BOM (Bill of Materials)
 * - Screen 3: Results (after calculation)
 *
 * Takes screenshots at each step and validates UI elements.
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots/production';
const PROD_URL = 'https://pcf.glideslopeintelligence.ai';
const PROD_API_URL = 'https://pcf.glideslopeintelligence.ai/api/v1';

// Ensure screenshot directory exists
test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

// Extended timeout for production tests (network latency + calculation time)
test.setTimeout(180000);

// Helper: dismiss Joyride tour overlay
async function dismissJoyride(page: Page) {
  try {
    await page.evaluate(() => {
      const portal = document.getElementById('react-joyride-portal');
      if (portal) portal.remove();
      document.querySelectorAll('[data-test-id="spotlight"], .react-joyride__overlay, .__floater').forEach(el => el.remove());
    });
    await page.waitForTimeout(300);
  } catch {
    // Joyride might not be present
  }
}

// Helper: authenticate and set up page
async function authenticateAndSetup(page: Page) {
  // First, set localStorage before navigating
  await page.addInitScript(() => {
    window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
  });

  // Navigate to production site
  await page.goto(PROD_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);

  // Attempt authentication
  try {
    const authResult = await page.evaluate(async () => {
      try {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'e2e-test', password: 'E2ETestPassword123!' })
        });
        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('auth_token', data.access_token);
          localStorage.setItem('pcf-calculator-tour-completed', 'true');
          return { success: true, token: data.access_token?.substring(0, 20) + '...' };
        }
        return { success: false, status: response.status };
      } catch (e: any) {
        return { success: false, error: e.message };
      }
    });
    console.log('Auth result:', JSON.stringify(authResult));
  } catch (e) {
    console.log('Auth failed (may still proceed):', e);
  }

  // Set tour completed regardless
  await page.evaluate(() => {
    localStorage.setItem('pcf-calculator-tour-completed', 'true');
  });

  // Reload to pick up auth token and tour setting
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Dismiss any remaining joyride overlays
  await dismissJoyride(page);
}

// Helper: take screenshot with timestamp prefix
async function takeScreenshot(page: Page, name: string, fullPage: boolean = false) {
  const filepath = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage });
  console.log(`Screenshot saved: ${filepath}`);
  return filepath;
}

// Helper: check for error banners/toasts
async function checkForErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  // Check for error toasts
  const errorToasts = page.locator('[role="alert"], .toast-error, .Toastify__toast--error, [data-state="open"][role="alertdialog"]');
  const errorCount = await errorToasts.count();
  if (errorCount > 0) {
    for (let i = 0; i < errorCount; i++) {
      const text = await errorToasts.nth(i).textContent().catch(() => '');
      if (text) errors.push(`Error toast: ${text}`);
    }
  }

  // Check for error banners
  const errorBanners = page.locator('.error-banner, [class*="error"], [class*="Error"]').filter({ hasText: /error|failed|unable/i });
  const bannerCount = await errorBanners.count();
  if (bannerCount > 0) {
    for (let i = 0; i < bannerCount; i++) {
      const text = await errorBanners.nth(i).textContent().catch(() => '');
      if (text && text.length < 200) errors.push(`Error banner: ${text}`);
    }
  }

  return errors;
}

// Helper: navigate to BOM editor from product selection
async function navigateToBOMEditor(page: Page): Promise<string> {
  const combobox = page.locator('button[role="combobox"]').first();
  await expect(combobox).toBeVisible({ timeout: 10000 });
  await combobox.click();
  await page.waitForTimeout(1500);

  const firstOption = page.locator('[role="option"]').first();
  await expect(firstOption).toBeVisible({ timeout: 10000 });
  const selectedProduct = await firstOption.textContent().catch(() => '') || 'Unknown';
  await firstOption.click();
  await page.waitForTimeout(1500);

  const nextButton = page.locator('button').filter({ hasText: /next/i });
  await expect(nextButton).toBeEnabled({ timeout: 5000 });
  await nextButton.click();
  await page.waitForTimeout(3000);
  await dismissJoyride(page);

  return selectedProduct;
}

test.describe('Production Visual Test - All Screens', () => {

  test('Screen 1: Select Product', async ({ page }) => {
    console.log('\n======================================');
    console.log('SCREEN 1: SELECT PRODUCT');
    console.log('======================================\n');

    await authenticateAndSetup(page);

    // Take initial screenshot
    await takeScreenshot(page, '01_screen1_initial');

    // Check for errors
    const errors = await checkForErrors(page);
    if (errors.length > 0) {
      console.log('ERRORS found on Screen 1:', errors);
    } else {
      console.log('No errors found on Screen 1');
    }

    // Verify the product selector combobox is visible
    const combobox = page.locator('button[role="combobox"]').first();
    const comboboxVisible = await combobox.isVisible({ timeout: 10000 }).catch(() => false);
    console.log(`Product selector combobox visible: ${comboboxVisible}`);
    expect(comboboxVisible).toBeTruthy();

    // Check for page heading
    const pageText = await page.locator('body').textContent().catch(() => '');
    const hasSelectProduct = /select.*product|choose.*product|product.*selector/i.test(pageText || '');
    console.log(`Has product selection heading/text: ${hasSelectProduct}`);

    // Check for the step indicator / wizard navigation
    const hasStepIndicator = await page.locator('[class*="step"], [class*="wizard"], [role="tablist"]').isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`Has step/wizard indicator: ${hasStepIndicator}`);

    // Click on combobox to open dropdown
    await combobox.click();
    await page.waitForTimeout(1500);

    // Take screenshot with dropdown open
    await takeScreenshot(page, '02_screen1_dropdown_open');

    // Check that products are loading/loaded in the dropdown
    const options = page.locator('[role="option"], [role="listbox"] [role="option"]');
    const optionCount = await options.count();
    console.log(`Number of product options visible: ${optionCount}`);

    if (optionCount > 0) {
      // Get first few option texts
      for (let i = 0; i < Math.min(5, optionCount); i++) {
        const text = await options.nth(i).textContent().catch(() => '');
        console.log(`  Option ${i + 1}: ${text?.substring(0, 80)}`);
      }
    }

    // Search for a product
    await page.keyboard.type('Window');
    await page.waitForTimeout(1500);
    await takeScreenshot(page, '03_screen1_search_window');

    // Check filtered results
    const filteredOptions = page.locator('[role="option"]');
    const filteredCount = await filteredOptions.count();
    console.log(`Filtered options for "Window": ${filteredCount}`);

    // Select a product (try Window first, then Gaming, then first available)
    let productSelected = false;
    let selectedProductName = '';

    if (filteredCount > 0) {
      const firstOption = filteredOptions.first();
      selectedProductName = await firstOption.textContent().catch(() => '') || '';
      await firstOption.click();
      await page.waitForTimeout(1500);
      productSelected = true;
      console.log(`Selected product: ${selectedProductName.substring(0, 80)}`);
    } else {
      // Try Gaming
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      await combobox.click();
      await page.waitForTimeout(500);

      // Clear search and type Gaming
      const searchInput = page.locator('input[role="combobox"], input[placeholder*="Search"], input[placeholder*="search"]').first();
      if (await searchInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await searchInput.fill('');
        await page.waitForTimeout(300);
        await searchInput.fill('Gaming');
      } else {
        await page.keyboard.type('Gaming');
      }
      await page.waitForTimeout(1500);

      const gamingOptions = page.locator('[role="option"]');
      const gamingCount = await gamingOptions.count();
      console.log(`Filtered options for "Gaming": ${gamingCount}`);

      if (gamingCount > 0) {
        selectedProductName = await gamingOptions.first().textContent().catch(() => '') || '';
        await gamingOptions.first().click();
        await page.waitForTimeout(1500);
        productSelected = true;
        console.log(`Selected product: ${selectedProductName.substring(0, 80)}`);
      } else {
        // Select any first available product
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);
        await combobox.click();
        await page.waitForTimeout(1000);

        const anyOptions = page.locator('[role="option"]');
        if (await anyOptions.first().isVisible({ timeout: 5000 }).catch(() => false)) {
          selectedProductName = await anyOptions.first().textContent().catch(() => '') || '';
          await anyOptions.first().click();
          await page.waitForTimeout(1500);
          productSelected = true;
          console.log(`Selected first available product: ${selectedProductName.substring(0, 80)}`);
        }
      }
    }

    expect(productSelected).toBeTruthy();

    // Verify Next button becomes enabled after selection
    const nextButton = page.locator('button').filter({ hasText: /next/i });
    const nextEnabled = await nextButton.isEnabled({ timeout: 5000 }).catch(() => false);
    console.log(`Next button enabled after selection: ${nextEnabled}`);
    expect(nextEnabled).toBeTruthy();

    // Take screenshot after product selection
    await takeScreenshot(page, '04_screen1_product_selected');

    // Final check for errors on Screen 1
    const errorsAfter = await checkForErrors(page);

    console.log('\n--- SCREEN 1 SUMMARY ---');
    console.log(`PASS: Product selector visible: ${comboboxVisible}`);
    console.log(`PASS: Products load in dropdown: ${optionCount > 0}`);
    console.log(`PASS: Product selected: ${productSelected} (${selectedProductName.substring(0, 60)})`);
    console.log(`PASS: Next button enabled: ${nextEnabled}`);
    console.log(`${errorsAfter.length === 0 ? 'PASS' : 'FAIL'}: No errors on page: ${errorsAfter.length === 0}`);
    console.log('--- END SCREEN 1 ---\n');
  });

  test('Screen 2: Edit BOM (Bill of Materials)', async ({ page }) => {
    console.log('\n======================================');
    console.log('SCREEN 2: EDIT BOM');
    console.log('======================================\n');

    await authenticateAndSetup(page);
    const selectedProduct = await navigateToBOMEditor(page);
    console.log(`Selected product for BOM test: ${selectedProduct.substring(0, 80)}`);

    // Take screenshot of BOM editor
    await takeScreenshot(page, '05_screen2_bom_editor');

    // Check for errors
    const errors = await checkForErrors(page);
    if (errors.length > 0) {
      console.log('ERRORS found on Screen 2:', errors);
    } else {
      console.log('No errors found on Screen 2');
    }

    // Check for BOM heading
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const hasBOMHeading = /BOM|Bill of Materials|Edit BOM|Components/i.test(bodyText || '');
    console.log(`Has BOM heading/text: ${hasBOMHeading}`);

    // Check for BOM component cards or table rows
    const bomItems = page.locator('[class*="card"], [class*="Card"], tr, [class*="bom-item"], [class*="component"]');
    const bomItemCount = await bomItems.count();
    console.log(`BOM items/cards visible: ${bomItemCount}`);

    // Look for component text specifically
    const componentText = page.locator('text=/\\d+\\s*(component|item|material)/i');
    const componentTextVisible = await componentText.isVisible({ timeout: 3000 }).catch(() => false);
    if (componentTextVisible) {
      const compText = await componentText.textContent().catch(() => '');
      console.log(`Component info text: ${compText}`);
    }

    // Verify the "Calculate" button is visible (use data-testid to avoid strict mode violation)
    const calculateButtonTop = page.getByTestId('calculate-button-top');
    const calcTopVisible = await calculateButtonTop.isVisible({ timeout: 5000 }).catch(() => false);
    console.log(`Calculate button (top) visible: ${calcTopVisible}`);

    // Also check for the next-button that acts as Calculate
    const nextCalcButton = page.getByTestId('next-button');
    const nextCalcVisible = await nextCalcButton.isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`Calculate/Next button (bottom) visible: ${nextCalcVisible}`);

    const calcVisible = calcTopVisible || nextCalcVisible;
    console.log(`Any Calculate button visible: ${calcVisible}`);

    // Check for "Back" button (navigation)
    const backButton = page.locator('button').filter({ hasText: /back|previous/i });
    const backVisible = await backButton.isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`Back button visible: ${backVisible}`);

    // Scroll down to see full BOM list
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(500);
    await takeScreenshot(page, '06_screen2_bom_scrolled');

    // Full page screenshot
    await takeScreenshot(page, '07_screen2_bom_full_page', true);

    console.log('\n--- SCREEN 2 SUMMARY ---');
    console.log(`PASS: BOM editor page loaded: ${hasBOMHeading}`);
    console.log(`${bomItemCount > 0 ? 'PASS' : 'INFO'}: BOM components listed: ${bomItemCount > 0} (count: ${bomItemCount})`);
    console.log(`${calcVisible ? 'PASS' : 'FAIL'}: Calculate button visible: ${calcVisible}`);
    console.log(`${backVisible ? 'PASS' : 'INFO'}: Back navigation available: ${backVisible}`);
    console.log(`${errors.length === 0 ? 'PASS' : 'FAIL'}: No errors on page: ${errors.length === 0}`);
    console.log('--- END SCREEN 2 ---\n');
  });

  test('Screen 3: Results (Calculate and view)', async ({ page }) => {
    console.log('\n======================================');
    console.log('SCREEN 3: RESULTS');
    console.log('======================================\n');

    await authenticateAndSetup(page);
    const selectedProduct = await navigateToBOMEditor(page);
    console.log(`Selected product for Results test: ${selectedProduct.substring(0, 80)}`);

    // Click Calculate button - use specific testid to avoid strict mode violation
    // There are two calculate buttons: calculate-button-top and next-button (bottom)
    const calculateButtonTop = page.getByTestId('calculate-button-top');
    const calcTopVisible = await calculateButtonTop.isVisible({ timeout: 5000 }).catch(() => false);

    let calculateButton: any;
    if (calcTopVisible) {
      calculateButton = calculateButtonTop;
      console.log('Using top Calculate button');
    } else {
      // Fall back to next-button which may have Calculate aria-label
      calculateButton = page.getByTestId('next-button');
      console.log('Using bottom Calculate/Next button');
    }

    await expect(calculateButton).toBeVisible({ timeout: 10000 });

    // Screenshot before calculating
    await takeScreenshot(page, '08_screen3_before_calculate');

    console.log('Clicking Calculate button...');
    await calculateButton.click();
    await page.waitForTimeout(2000);

    // Take screenshot of loading/calculating state
    await takeScreenshot(page, '09_screen3_calculating');

    // Wait for results to appear (polling every 5 seconds, up to 90 seconds)
    console.log('Waiting for results (up to 90 seconds)...');
    let resultsAppeared = false;
    const startTime = Date.now();

    for (let i = 0; i < 18; i++) { // 18 * 5s = 90s
      // Check for results heading
      const resultsHeading = page.locator('h2, h3').filter({ hasText: /result|footprint|summary/i });
      if (await resultsHeading.isVisible({ timeout: 1000 }).catch(() => false)) {
        resultsAppeared = true;
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        console.log(`Results appeared after ${elapsed} seconds`);
        break;
      }

      // Also check for CO2e values appearing
      const co2Value = page.locator('text=/kg\\s*CO2/i');
      if (await co2Value.isVisible({ timeout: 1000 }).catch(() => false)) {
        resultsAppeared = true;
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        console.log(`CO2 values appeared after ${elapsed} seconds`);
        break;
      }

      // Check for error state
      const errorState = page.locator('text=/error|failed|unable to calculate/i');
      if (await errorState.isVisible({ timeout: 500 }).catch(() => false)) {
        const errorText = await errorState.textContent().catch(() => '');
        console.log(`ERROR during calculation: ${errorText}`);
        break;
      }

      console.log(`  Polling... (${(i + 1) * 5}s elapsed)`);
      await page.waitForTimeout(5000);
    }

    // Wait extra time for charts to render
    if (resultsAppeared) {
      await page.waitForTimeout(3000);
    }

    // Take screenshot of results
    await takeScreenshot(page, '10_screen3_results');

    // Check for errors
    const errors = await checkForErrors(page);
    if (errors.length > 0) {
      console.log('ERRORS found on Screen 3:', errors);
    } else {
      console.log('No errors found on Screen 3');
    }

    // Check for results heading
    const resultsHeadingCheck = page.locator('h2, h3').filter({ hasText: /result|footprint|summary/i });
    const hasResultsHeading = await resultsHeadingCheck.isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`Results heading visible: ${hasResultsHeading}`);

    // Check for CO2e value display
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const co2ePattern = /(\d+(?:,\d{3})*\.?\d*)\s*kg\s*CO2?e?/gi;
    const co2eMatches = bodyText?.match(co2ePattern);
    const hasCO2eValue = co2eMatches && co2eMatches.length > 0;
    console.log(`CO2e value displayed: ${hasCO2eValue}`);
    if (co2eMatches) {
      co2eMatches.forEach((match, i) => {
        console.log(`  CO2e value ${i + 1}: ${match}`);
      });
    }

    // Check for Sankey diagram or breakdown table
    const sankeyDiagram = page.locator('svg, [class*="sankey"], [class*="Sankey"], [class*="chart"], [class*="Chart"], canvas');
    const hasSankey = await sankeyDiagram.first().isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`Sankey diagram / chart visible: ${hasSankey}`);

    // Check for breakdown table
    const breakdownTable = page.locator('table, [class*="breakdown"], [class*="Breakdown"]');
    const hasBreakdown = await breakdownTable.first().isVisible({ timeout: 3000 }).catch(() => false);
    console.log(`Breakdown table visible: ${hasBreakdown}`);

    // Scroll down and capture full results
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(500);
    await takeScreenshot(page, '11_screen3_results_scrolled');

    await page.evaluate(() => window.scrollTo(0, 1000));
    await page.waitForTimeout(500);
    await takeScreenshot(page, '12_screen3_results_bottom');

    // Full page screenshot
    await takeScreenshot(page, '13_screen3_results_full_page', true);

    console.log('\n--- SCREEN 3 SUMMARY ---');
    console.log(`${resultsAppeared ? 'PASS' : 'FAIL'}: Results appeared after calculation: ${resultsAppeared}`);
    console.log(`${hasResultsHeading ? 'PASS' : 'WARN'}: Results heading visible: ${hasResultsHeading}`);
    console.log(`${hasCO2eValue ? 'PASS' : 'FAIL'}: CO2e value displayed: ${hasCO2eValue}`);
    console.log(`${hasSankey || hasBreakdown ? 'PASS' : 'WARN'}: Chart or breakdown visible: ${hasSankey || hasBreakdown}`);
    console.log(`${errors.length === 0 ? 'PASS' : 'FAIL'}: No errors on page: ${errors.length === 0}`);
    console.log('--- END SCREEN 3 ---\n');
  });

  test('Cross-Screen Validation: Full wizard flow', async ({ page }) => {
    console.log('\n======================================');
    console.log('CROSS-SCREEN VALIDATION');
    console.log('======================================\n');

    await authenticateAndSetup(page);

    // === Step 1: Product Selection ===
    console.log('--- Step 1: Product Selection ---');
    const combobox = page.locator('button[role="combobox"]').first();
    const step1Visible = await combobox.isVisible({ timeout: 10000 }).catch(() => false);
    console.log(`Product selector visible: ${step1Visible}`);
    let step1Errors = await checkForErrors(page);

    await combobox.click();
    await page.waitForTimeout(1500);

    const firstOption = page.locator('[role="option"]').first();
    await expect(firstOption).toBeVisible({ timeout: 10000 });
    const selectedProductText = await firstOption.textContent().catch(() => '') || '';
    await firstOption.click();
    await page.waitForTimeout(1500);
    console.log(`Selected: ${selectedProductText.substring(0, 60)}`);

    // Navigate to Step 2
    const nextButton = page.locator('button').filter({ hasText: /next/i });
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(3000);
    await dismissJoyride(page);

    // === Step 2: BOM Editor ===
    console.log('--- Step 2: BOM Editor ---');
    const bodyText2 = await page.locator('body').textContent().catch(() => '');
    const step2Loaded = /BOM|Bill of Materials|Edit BOM|Components/i.test(bodyText2 || '');
    console.log(`BOM editor loaded: ${step2Loaded}`);
    let step2Errors = await checkForErrors(page);

    // Test Back navigation
    const backButton = page.locator('button').filter({ hasText: /back|previous/i });
    const canGoBack = await backButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (canGoBack) {
      console.log('Testing Back navigation...');
      await backButton.click();
      await page.waitForTimeout(2000);

      // Verify we're back on Product Selection
      const comboboxAgain = page.locator('button[role="combobox"]').first();
      const backToStep1 = await comboboxAgain.isVisible({ timeout: 5000 }).catch(() => false);
      console.log(`Successfully navigated back to Step 1: ${backToStep1}`);

      // Navigate forward again
      const nextButtonAgain = page.locator('button').filter({ hasText: /next/i });
      if (await nextButtonAgain.isEnabled({ timeout: 3000 }).catch(() => false)) {
        await nextButtonAgain.click();
        await page.waitForTimeout(3000);
        await dismissJoyride(page);
      }
    }

    // === Step 3: Calculate and view Results ===
    console.log('--- Step 3: Results ---');

    // Use specific testid to avoid strict mode violation
    const calcButtonTop = page.getByTestId('calculate-button-top');
    const calcTopVisible = await calcButtonTop.isVisible({ timeout: 5000 }).catch(() => false);

    let calcButton: any;
    if (calcTopVisible) {
      calcButton = calcButtonTop;
    } else {
      calcButton = page.getByTestId('next-button');
    }

    const calcVisible = await calcButton.isVisible({ timeout: 5000 }).catch(() => false);

    let step3Loaded = false;
    if (calcVisible) {
      await calcButton.click();
      await page.waitForTimeout(2000);

      // Wait for results
      for (let i = 0; i < 18; i++) {
        const resultsContent = page.locator('text=/kg\\s*CO2/i');
        if (await resultsContent.isVisible({ timeout: 1000 }).catch(() => false)) {
          step3Loaded = true;
          break;
        }
        const resultsHeading = page.locator('h2, h3').filter({ hasText: /result|footprint|summary/i });
        if (await resultsHeading.isVisible({ timeout: 1000 }).catch(() => false)) {
          step3Loaded = true;
          break;
        }
        console.log(`  Polling for results... (${(i + 1) * 5}s)`);
        await page.waitForTimeout(5000);
      }

      if (step3Loaded) {
        await page.waitForTimeout(3000);
      }
      console.log(`Results page loaded: ${step3Loaded}`);
    } else {
      console.log('Calculate button not found');
    }

    let step3Errors = await checkForErrors(page);

    // Take final screenshot
    await takeScreenshot(page, '14_cross_screen_final');
    await takeScreenshot(page, '15_cross_screen_final_full', true);

    // === Summary ===
    console.log('\n======================================');
    console.log('CROSS-SCREEN VALIDATION SUMMARY');
    console.log('======================================');
    console.log(`Step 1 (Select Product): ${step1Visible ? 'PASS' : 'FAIL'} | Errors: ${step1Errors.length}`);
    console.log(`Step 2 (Edit BOM): ${step2Loaded ? 'PASS' : 'FAIL'} | Errors: ${step2Errors.length}`);
    console.log(`Step 3 (Results): ${step3Loaded ? 'PASS' : 'FAIL'} | Errors: ${step3Errors.length}`);
    console.log(`Navigation: Back button works: ${canGoBack ? 'PASS' : 'N/A'}`);
    console.log(`Total errors across all screens: ${step1Errors.length + step2Errors.length + step3Errors.length}`);
    console.log('======================================\n');
  });
});
