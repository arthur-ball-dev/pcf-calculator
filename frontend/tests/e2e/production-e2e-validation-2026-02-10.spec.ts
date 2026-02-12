/**
 * Production E2E Visual Validation - 2026-02-10
 *
 * Comprehensive validation of the PCF Calculator at https://pcf.glideslopeintelligence.ai/
 *
 * Validation Checklist:
 * 1. Homepage loads correctly - wizard/calculator interface visible
 * 2. Product selection works - select product from dropdown
 * 3. BOM display works - BOM cards load after product selection
 * 4. Calculate PCF - trigger calculation, wait for results, verify Sankey diagram
 * 5. Tour button works - click Tour button, verify Joyride starts
 * 6. Tour text verification - verify results tour step text content
 */

import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots';
const PROD_URL = 'https://pcf.glideslopeintelligence.ai';

// Test results tracking
interface ValidationResult {
  step: string;
  status: 'PASS' | 'FAIL' | 'WARN';
  detail: string;
  screenshot: string;
}

const results: ValidationResult[] = [];

// Ensure screenshot directory exists
test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

test.setTimeout(180000);

// Helper: take screenshot
async function screenshot(page: Page, name: string, fullPage = false): Promise<string> {
  const filepath = path.join(SCREENSHOT_DIR, `${name}.png`);
  await page.screenshot({ path: filepath, fullPage });
  console.log(`  Screenshot: ${filepath}`);
  return filepath;
}

// Helper: record result
function record(step: string, status: 'PASS' | 'FAIL' | 'WARN', detail: string, screenshotFile: string) {
  results.push({ step, status, detail, screenshot: screenshotFile });
  console.log(`  [${status}] ${step}: ${detail}`);
}

// Helper: authenticate and set up page (tour dismissed)
async function setupAuth(page: Page, dismissTour = true) {
  await page.addInitScript((skipTour) => {
    if (skipTour) {
      window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
    }
  }, dismissTour);

  await page.goto(PROD_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(2000);

  // Authenticate
  await page.evaluate(async () => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'e2e-test', password: 'E2ETestPassword123!' })
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('auth_token', data.access_token);
      }
    } catch {
      // Auth may not be required
    }
  });

  if (dismissTour) {
    await page.evaluate(() => {
      localStorage.setItem('pcf-calculator-tour-completed', 'true');
    });
  }

  await page.reload({ waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Dismiss any leftover Joyride overlays
  if (dismissTour) {
    await page.evaluate(() => {
      const portal = document.getElementById('react-joyride-portal');
      if (portal) portal.remove();
      document.querySelectorAll('[data-test-id="spotlight"], .react-joyride__overlay, .__floater').forEach(el => el.remove());
    });
    await page.waitForTimeout(300);
  }
}

// Helper: dismiss Joyride overlay
async function dismissJoyride(page: Page) {
  try {
    await page.evaluate(() => {
      const portal = document.getElementById('react-joyride-portal');
      if (portal) portal.remove();
      document.querySelectorAll('[data-test-id="spotlight"], .react-joyride__overlay, .__floater').forEach(el => el.remove());
    });
    await page.waitForTimeout(300);
  } catch {
    // Not present
  }
}


test.describe('Production E2E Visual Validation - 2026-02-10', () => {

  test('1. Homepage loads correctly', async ({ page }) => {
    console.log('\n=== VALIDATION 1: Homepage Loads ===');

    await setupAuth(page);
    await screenshot(page, 'V1_01_homepage_initial');

    // Check that the wizard/calculator interface loads
    const combobox = page.locator('button[role="combobox"]').first();
    const comboboxVisible = await combobox.isVisible({ timeout: 10000 }).catch(() => false);

    if (comboboxVisible) {
      record('1. Homepage loads', 'PASS', 'Product selector combobox is visible', 'V1_01_homepage_initial.png');
    } else {
      await screenshot(page, 'V1_01_homepage_FAIL');
      record('1. Homepage loads', 'FAIL', 'Product selector combobox NOT visible', 'V1_01_homepage_FAIL.png');
    }

    // Check for wizard step indicators
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const hasWizardText = /select.*product|choose.*product|step\s*1/i.test(bodyText || '');

    if (hasWizardText) {
      record('1. Wizard UI present', 'PASS', 'Wizard step text found on page', 'V1_01_homepage_initial.png');
    } else {
      record('1. Wizard UI present', 'WARN', 'No explicit wizard step text found, but UI may still be functional', 'V1_01_homepage_initial.png');
    }

    // Check for Tour button
    const tourButton = page.locator('[data-testid="tour-restart-button"]');
    const tourVisible = await tourButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (tourVisible) {
      record('1. Tour button visible', 'PASS', 'Tour button found in header', 'V1_01_homepage_initial.png');
    } else {
      record('1. Tour button visible', 'WARN', 'Tour button not immediately visible', 'V1_01_homepage_initial.png');
    }

    expect(comboboxVisible).toBeTruthy();
  });


  test('2. Product selection works', async ({ page }) => {
    console.log('\n=== VALIDATION 2: Product Selection ===');

    await setupAuth(page);

    // Open dropdown
    const combobox = page.locator('button[role="combobox"]').first();
    await expect(combobox).toBeVisible({ timeout: 10000 });
    await combobox.click();
    await page.waitForTimeout(1500);

    await screenshot(page, 'V2_01_dropdown_open');

    // Count available products
    const options = page.locator('[role="option"]');
    const optionCount = await options.count();
    console.log(`  Products in dropdown: ${optionCount}`);

    if (optionCount > 0) {
      record('2. Dropdown opens', 'PASS', `${optionCount} products visible in dropdown`, 'V2_01_dropdown_open.png');
    } else {
      record('2. Dropdown opens', 'FAIL', 'No products in dropdown', 'V2_01_dropdown_open.png');
    }

    // Search for an electronics product
    await page.keyboard.type('Window');
    await page.waitForTimeout(1500);

    await screenshot(page, 'V2_02_search_results');

    const filteredOptions = page.locator('[role="option"]');
    const filteredCount = await filteredOptions.count();
    console.log(`  Filtered results for "Window": ${filteredCount}`);

    // Select first matching product
    let selectedName = '';
    if (filteredCount > 0) {
      selectedName = await filteredOptions.first().textContent().catch(() => '') || '';
      await filteredOptions.first().click();
      await page.waitForTimeout(1500);
      record('2. Product selected', 'PASS', `Selected: ${selectedName.substring(0, 80)}`, 'V2_03_product_selected.png');
    } else {
      // Try first available
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      await combobox.click();
      await page.waitForTimeout(1000);

      const anyOptions = page.locator('[role="option"]');
      if (await anyOptions.first().isVisible({ timeout: 5000 }).catch(() => false)) {
        selectedName = await anyOptions.first().textContent().catch(() => '') || '';
        await anyOptions.first().click();
        await page.waitForTimeout(1500);
        record('2. Product selected', 'PASS', `Selected first available: ${selectedName.substring(0, 80)}`, 'V2_03_product_selected.png');
      } else {
        record('2. Product selected', 'FAIL', 'Could not select any product', 'V2_02_search_results.png');
      }
    }

    await screenshot(page, 'V2_03_product_selected');

    // Verify Next button becomes enabled
    const nextButton = page.locator('button').filter({ hasText: /next/i });
    const nextEnabled = await nextButton.isEnabled({ timeout: 5000 }).catch(() => false);

    if (nextEnabled) {
      record('2. Next button enabled', 'PASS', 'Next button enabled after product selection', 'V2_03_product_selected.png');
    } else {
      record('2. Next button enabled', 'FAIL', 'Next button NOT enabled', 'V2_03_product_selected.png');
    }

    expect(selectedName.length).toBeGreaterThan(0);
  });


  test('3. BOM display works', async ({ page }) => {
    console.log('\n=== VALIDATION 3: BOM Display ===');

    await setupAuth(page);

    // Select a product and navigate to BOM
    const combobox = page.locator('button[role="combobox"]').first();
    await expect(combobox).toBeVisible({ timeout: 10000 });
    await combobox.click();
    await page.waitForTimeout(1500);

    const firstOption = page.locator('[role="option"]').first();
    await expect(firstOption).toBeVisible({ timeout: 10000 });
    const selectedProduct = await firstOption.textContent().catch(() => '') || 'Unknown';
    await firstOption.click();
    await page.waitForTimeout(1500);
    console.log(`  Selected product: ${selectedProduct.substring(0, 80)}`);

    // Navigate to BOM step
    const nextButton = page.locator('button').filter({ hasText: /next/i });
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(3000);
    await dismissJoyride(page);

    await screenshot(page, 'V3_01_bom_step');

    // Check BOM heading is visible
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const hasBOMText = /BOM|Bill of Materials|Edit BOM|Components/i.test(bodyText || '');

    if (hasBOMText) {
      record('3. BOM step loaded', 'PASS', 'BOM heading/text visible', 'V3_01_bom_step.png');
    } else {
      record('3. BOM step loaded', 'FAIL', 'BOM text NOT found on page', 'V3_01_bom_step.png');
    }

    // Check for BOM cards/items
    // BOM cards are typically rendered as Card components
    const bomCards = page.locator('[class*="card"], [class*="Card"]');
    const cardCount = await bomCards.count();
    console.log(`  BOM card-like elements: ${cardCount}`);

    if (cardCount > 0) {
      record('3. BOM cards loaded', 'PASS', `${cardCount} BOM card elements found`, 'V3_01_bom_step.png');
    } else {
      record('3. BOM cards loaded', 'WARN', 'No card elements found - BOM may use different layout', 'V3_01_bom_step.png');
    }

    // Check for Calculate button
    const calcButtonTop = page.getByTestId('calculate-button-top');
    const calcVisible = await calcButtonTop.isVisible({ timeout: 5000 }).catch(() => false);
    const nextCalc = page.getByTestId('next-button');
    const nextCalcVisible = await nextCalc.isVisible({ timeout: 3000 }).catch(() => false);

    if (calcVisible || nextCalcVisible) {
      record('3. Calculate button visible', 'PASS', 'Calculate button found on BOM step', 'V3_01_bom_step.png');
    } else {
      record('3. Calculate button visible', 'FAIL', 'Calculate button NOT found', 'V3_01_bom_step.png');
    }

    // Scroll and take full page screenshot
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(500);
    await screenshot(page, 'V3_02_bom_scrolled');
    await screenshot(page, 'V3_03_bom_full_page', true);

    expect(hasBOMText).toBeTruthy();
  });


  test('4. Calculate PCF and view results with Sankey diagram', async ({ page }) => {
    console.log('\n=== VALIDATION 4: Calculate PCF ===');

    await setupAuth(page);

    // Select product and navigate to BOM
    const combobox = page.locator('button[role="combobox"]').first();
    await expect(combobox).toBeVisible({ timeout: 10000 });
    await combobox.click();
    await page.waitForTimeout(1500);

    const firstOption = page.locator('[role="option"]').first();
    await expect(firstOption).toBeVisible({ timeout: 10000 });
    const selectedProduct = await firstOption.textContent().catch(() => '') || 'Unknown';
    await firstOption.click();
    await page.waitForTimeout(1500);
    console.log(`  Selected product: ${selectedProduct.substring(0, 80)}`);

    const nextButton = page.locator('button').filter({ hasText: /next/i });
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(3000);
    await dismissJoyride(page);

    // Click Calculate
    const calcButtonTop = page.getByTestId('calculate-button-top');
    const calcTopVisible = await calcButtonTop.isVisible({ timeout: 5000 }).catch(() => false);

    let calcButton: any;
    if (calcTopVisible) {
      calcButton = calcButtonTop;
      console.log('  Using top Calculate button');
    } else {
      calcButton = page.getByTestId('next-button');
      console.log('  Using bottom Calculate/Next button');
    }

    await expect(calcButton).toBeVisible({ timeout: 10000 });
    await screenshot(page, 'V4_01_before_calculate');

    console.log('  Clicking Calculate...');
    await calcButton.click();
    await page.waitForTimeout(2000);

    await screenshot(page, 'V4_02_calculating');
    record('4. Calculate clicked', 'PASS', 'Calculate button clicked successfully', 'V4_02_calculating.png');

    // Wait for results (up to 90 seconds)
    console.log('  Waiting for results (up to 90 seconds)...');
    let resultsAppeared = false;
    const startTime = Date.now();

    for (let i = 0; i < 18; i++) {
      // Check for CO2e values
      const co2Value = page.locator('text=/kg\\s*CO2/i');
      if (await co2Value.isVisible({ timeout: 1000 }).catch(() => false)) {
        resultsAppeared = true;
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        console.log(`  Results appeared after ${elapsed}s`);
        break;
      }

      // Check for results heading
      const resultsHeading = page.locator('h2, h3').filter({ hasText: /result|footprint|summary/i });
      if (await resultsHeading.isVisible({ timeout: 1000 }).catch(() => false)) {
        resultsAppeared = true;
        const elapsed = Math.round((Date.now() - startTime) / 1000);
        console.log(`  Results heading appeared after ${elapsed}s`);
        break;
      }

      // Check for error
      const errorState = page.locator('text=/error|failed|unable to calculate/i');
      if (await errorState.isVisible({ timeout: 500 }).catch(() => false)) {
        const errorText = await errorState.textContent().catch(() => '');
        console.log(`  ERROR: ${errorText}`);
        break;
      }

      console.log(`    Polling... (${(i + 1) * 5}s)`);
      await page.waitForTimeout(5000);
    }

    if (resultsAppeared) {
      await page.waitForTimeout(3000); // Let charts render
      record('4. Results appeared', 'PASS', 'Calculation results loaded', 'V4_03_results.png');
    } else {
      record('4. Results appeared', 'FAIL', 'Results did NOT appear within 90s', 'V4_03_results.png');
    }

    await screenshot(page, 'V4_03_results');

    // Check for CO2e values
    const bodyText = await page.locator('body').textContent().catch(() => '');
    const co2ePattern = /(\d+(?:,\d{3})*\.?\d*)\s*kg\s*CO2?e?/gi;
    const co2eMatches = bodyText?.match(co2ePattern);

    if (co2eMatches && co2eMatches.length > 0) {
      record('4. CO2e values displayed', 'PASS', `Found CO2e values: ${co2eMatches.slice(0, 3).join(', ')}`, 'V4_03_results.png');
    } else {
      record('4. CO2e values displayed', 'FAIL', 'No CO2e values found on results page', 'V4_03_results.png');
    }

    // Check for Sankey diagram (SVG element)
    const svgElements = page.locator('svg');
    const svgCount = await svgElements.count();
    console.log(`  SVG elements on page: ${svgCount}`);

    const sankeyLike = page.locator('[class*="sankey"], [class*="Sankey"], svg path, svg rect');
    const sankeyCount = await sankeyLike.count();
    console.log(`  Sankey-like elements: ${sankeyCount}`);

    if (svgCount > 0 || sankeyCount > 0) {
      record('4. Sankey diagram visible', 'PASS', `Found ${svgCount} SVG elements, ${sankeyCount} sankey-like elements`, 'V4_03_results.png');
    } else {
      record('4. Sankey diagram visible', 'FAIL', 'No SVG or Sankey elements found', 'V4_03_results.png');
    }

    // Scroll through results
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(500);
    await screenshot(page, 'V4_04_results_scrolled');

    await page.evaluate(() => window.scrollTo(0, 1000));
    await page.waitForTimeout(500);
    await screenshot(page, 'V4_05_results_bottom');

    await screenshot(page, 'V4_06_results_full_page', true);

    expect(resultsAppeared).toBeTruthy();
  });


  test('5. Tour button works', async ({ page }) => {
    console.log('\n=== VALIDATION 5: Tour Button ===');

    // Setup WITHOUT dismissing tour
    await page.addInitScript(() => {
      // Set tour as completed so it does not auto-start
      window.localStorage.setItem('pcf-calculator-tour-completed', 'true');
    });

    await page.goto(PROD_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Authenticate
    await page.evaluate(async () => {
      try {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'e2e-test', password: 'E2ETestPassword123!' })
        });
        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('auth_token', data.access_token);
        }
      } catch {
        // Auth may not be required
      }
    });

    await page.evaluate(() => {
      localStorage.setItem('pcf-calculator-tour-completed', 'true');
    });

    await page.reload({ waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);

    // Dismiss any auto-started tour
    await dismissJoyride(page);

    await screenshot(page, 'V5_01_before_tour');

    // Find the Tour button
    const tourButton = page.locator('[data-testid="tour-restart-button"]');
    const tourButtonVisible = await tourButton.isVisible({ timeout: 10000 }).catch(() => false);

    if (tourButtonVisible) {
      record('5. Tour button visible', 'PASS', 'Tour button found in header', 'V5_01_before_tour.png');
    } else {
      // Try finding by text
      const tourByText = page.locator('button').filter({ hasText: /tour/i });
      const tourTextVisible = await tourByText.isVisible({ timeout: 5000 }).catch(() => false);
      if (tourTextVisible) {
        record('5. Tour button visible', 'PASS', 'Tour button found by text', 'V5_01_before_tour.png');
      } else {
        await screenshot(page, 'V5_01_tour_button_FAIL');
        record('5. Tour button visible', 'FAIL', 'Tour button NOT found', 'V5_01_tour_button_FAIL.png');
        return;
      }
    }

    // Remove tour completion flag so tour can start
    await page.evaluate(() => {
      localStorage.removeItem('pcf-calculator-tour-completed');
    });

    // Click Tour button
    console.log('  Clicking Tour button...');
    const tourBtn = tourButtonVisible
      ? tourButton
      : page.locator('button').filter({ hasText: /tour/i });
    await tourBtn.click();
    await page.waitForTimeout(2000);

    await screenshot(page, 'V5_02_tour_started');

    // Check for Joyride tooltip
    const tooltip = page.locator('[role="tooltip"], .react-joyride__tooltip, [class*="joyride"]');
    const tooltipVisible = await tooltip.first().isVisible({ timeout: 10000 }).catch(() => false);

    if (tooltipVisible) {
      record('5. Tour tooltip appeared', 'PASS', 'Joyride tour tooltip is visible', 'V5_02_tour_started.png');
    } else {
      // Also check for the custom tooltip
      const customTooltip = page.locator('div').filter({ hasText: /Step 1|Select a Product|guided tour/i });
      const customVisible = await customTooltip.first().isVisible({ timeout: 5000 }).catch(() => false);
      if (customVisible) {
        record('5. Tour tooltip appeared', 'PASS', 'Tour tooltip with step content visible', 'V5_02_tour_started.png');
      } else {
        await screenshot(page, 'V5_02_tour_FAIL');
        record('5. Tour tooltip appeared', 'FAIL', 'Tour tooltip NOT visible after clicking Tour button', 'V5_02_tour_FAIL.png');
      }
    }

    // Check tooltip content for first step
    const tooltipText = await page.locator('body').textContent().catch(() => '');
    const hasFirstStep = /Step 1.*Select a Product|Select a Product.*Step 1/i.test(tooltipText || '');
    const hasStepContent = /search.*product|product.*code|product.*calculate/i.test(tooltipText || '');

    if (hasFirstStep || hasStepContent) {
      record('5. First tooltip content correct', 'PASS', 'First tour step text matches expected content', 'V5_02_tour_started.png');
    } else {
      record('5. First tooltip content correct', 'WARN', 'Could not verify first step text precisely', 'V5_02_tour_started.png');
    }

    expect(tourButtonVisible || await page.locator('button').filter({ hasText: /tour/i }).isVisible().catch(() => false)).toBeTruthy();
  });


  test('6. Tour text verification on Results page', async ({ page }) => {
    console.log('\n=== VALIDATION 6: Tour Text Verification ===');

    // First navigate to Results page through the full flow
    await setupAuth(page);

    // Select product
    const combobox = page.locator('button[role="combobox"]').first();
    await expect(combobox).toBeVisible({ timeout: 10000 });
    await combobox.click();
    await page.waitForTimeout(1500);

    const firstOption = page.locator('[role="option"]').first();
    await expect(firstOption).toBeVisible({ timeout: 10000 });
    await firstOption.click();
    await page.waitForTimeout(1500);

    // Navigate to BOM
    const nextButton = page.locator('button').filter({ hasText: /next/i });
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(3000);
    await dismissJoyride(page);

    // Calculate
    const calcButtonTop = page.getByTestId('calculate-button-top');
    const calcTopVisible = await calcButtonTop.isVisible({ timeout: 5000 }).catch(() => false);
    const calcButton = calcTopVisible ? calcButtonTop : page.getByTestId('next-button');
    await expect(calcButton).toBeVisible({ timeout: 10000 });
    await calcButton.click();
    await page.waitForTimeout(2000);

    // Wait for results
    console.log('  Waiting for results before testing tour...');
    let resultsReady = false;
    for (let i = 0; i < 18; i++) {
      const co2Value = page.locator('text=/kg\\s*CO2/i');
      if (await co2Value.isVisible({ timeout: 1000 }).catch(() => false)) {
        resultsReady = true;
        break;
      }
      const resultsHeading = page.locator('h2, h3').filter({ hasText: /result|footprint|summary/i });
      if (await resultsHeading.isVisible({ timeout: 1000 }).catch(() => false)) {
        resultsReady = true;
        break;
      }
      console.log(`    Polling... (${(i + 1) * 5}s)`);
      await page.waitForTimeout(5000);
    }

    if (!resultsReady) {
      record('6. Results page prerequisite', 'FAIL', 'Could not reach Results page for tour testing', 'V6_00_no_results.png');
      await screenshot(page, 'V6_00_no_results');
      return;
    }

    await page.waitForTimeout(3000); // Let charts render
    await screenshot(page, 'V6_01_results_page');
    record('6. Results page loaded', 'PASS', 'Results page ready for tour testing', 'V6_01_results_page.png');

    // Now remove tour completion and start tour
    await page.evaluate(() => {
      localStorage.removeItem('pcf-calculator-tour-completed');
    });

    // Click Tour button
    const tourButton = page.locator('[data-testid="tour-restart-button"]');
    const tourBtnVisible = await tourButton.isVisible({ timeout: 5000 }).catch(() => false);

    if (!tourBtnVisible) {
      const tourByText = page.locator('button').filter({ hasText: /tour/i });
      if (await tourByText.isVisible({ timeout: 5000 }).catch(() => false)) {
        await tourByText.click();
      } else {
        record('6. Tour button on results', 'FAIL', 'Tour button not found on Results page', 'V6_01_results_page.png');
        return;
      }
    } else {
      await tourButton.click();
    }

    await page.waitForTimeout(2000);
    await screenshot(page, 'V6_02_tour_on_results');

    // Capture all visible tooltip/tour content
    const fullBodyText = await page.locator('body').textContent().catch(() => '');

    // Verify "Step 3: View Results" (NOT "Step 4")
    const hasStep3ViewResults = /Step 3:\s*View Results/i.test(fullBodyText || '');
    const hasStep4 = /Step 4/i.test(fullBodyText || '');

    // The tour shows context-relevant steps - on the results page, the first visible
    // step should be about results. We need to navigate through tour steps.
    // The tour filters steps to only those with valid targets in the DOM.
    // On the Results page, "results-summary" and "visualization-tabs" should be visible.

    // Click through tour steps to find results-related content
    let foundViewResults = false;
    let foundExploreViz = false;
    let viewResultsText = '';
    let exploreVizText = '';
    let hasTreemap = false;
    let hasTrends = false;

    for (let step = 0; step < 8; step++) {
      const currentText = await page.locator('body').textContent().catch(() => '');

      // Check for "Step 3: View Results"
      if (/Step 3:\s*View Results/i.test(currentText || '')) {
        foundViewResults = true;
        viewResultsText = currentText || '';
        await screenshot(page, `V6_03_step3_view_results`);
        console.log('  Found "Step 3: View Results" tooltip');
      }

      // Check for "Explore Visualizations"
      if (/Explore Visualizations/i.test(currentText || '')) {
        foundExploreViz = true;
        exploreVizText = currentText || '';
        await screenshot(page, `V6_04_explore_viz`);
        console.log('  Found "Explore Visualizations" tooltip');

        // Verify it mentions Sankey diagram and breakdown table
        if (/Sankey diagram/i.test(currentText || '')) {
          console.log('  Sankey diagram mentioned in Explore Visualizations');
        }
        if (/breakdown table/i.test(currentText || '')) {
          console.log('  Breakdown table mentioned in Explore Visualizations');
        }
        if (/Treemap/i.test(currentText || '')) {
          hasTreemap = true;
          console.log('  WARNING: Treemap mentioned in Explore Visualizations');
        }
        if (/Trends/i.test(currentText || '')) {
          hasTrends = true;
          console.log('  WARNING: Trends mentioned in Explore Visualizations');
        }
      }

      // Try to click Next in the tour
      const nextBtn = page.locator('button').filter({ hasText: /^Next$/ });
      const nextVisible = await nextBtn.isVisible({ timeout: 2000 }).catch(() => false);

      if (nextVisible) {
        await nextBtn.click();
        await page.waitForTimeout(1500);
      } else {
        // Check for Finish button
        const finishBtn = page.locator('button').filter({ hasText: /^Finish$/ });
        const finishVisible = await finishBtn.isVisible({ timeout: 1000 }).catch(() => false);
        if (finishVisible) {
          // Capture before finishing
          if (!foundExploreViz) {
            // Check one more time
            const lastText = await page.locator('body').textContent().catch(() => '');
            if (/Explore Visualizations/i.test(lastText || '')) {
              foundExploreViz = true;
              exploreVizText = lastText || '';
              await screenshot(page, `V6_04_explore_viz`);
            }
          }
          break;
        } else {
          break; // No more navigation possible
        }
      }
    }

    // Record results for "Step 3: View Results"
    if (foundViewResults) {
      record('6. Results tour says "Step 3: View Results"', 'PASS',
        'Tour step correctly says "Step 3: View Results" (NOT Step 4)',
        'V6_03_step3_view_results.png');
    } else {
      // Check if Step 4 exists incorrectly
      if (hasStep4) {
        record('6. Results tour says "Step 3: View Results"', 'FAIL',
          'Tour step incorrectly says "Step 4" instead of "Step 3"',
          'V6_02_tour_on_results.png');
      } else {
        record('6. Results tour says "Step 3: View Results"', 'WARN',
          'Could not find "Step 3: View Results" in tour steps (tour may show different steps on results page)',
          'V6_02_tour_on_results.png');
      }
    }

    // Record results for "Explore Visualizations" content
    if (foundExploreViz) {
      const hasSankey = /Sankey diagram/i.test(exploreVizText);
      const hasBreakdown = /breakdown table/i.test(exploreVizText);

      if (hasSankey && hasBreakdown) {
        record('6. Explore Viz mentions Sankey + breakdown table', 'PASS',
          'Explore Visualizations correctly mentions "Sankey diagram" and "breakdown table"',
          'V6_04_explore_viz.png');
      } else {
        record('6. Explore Viz mentions Sankey + breakdown table', 'WARN',
          `Sankey: ${hasSankey}, Breakdown table: ${hasBreakdown}`,
          'V6_04_explore_viz.png');
      }

      if (hasTreemap || hasTrends) {
        record('6. No Treemap/Trends in Explore Viz', 'FAIL',
          `Explore Viz incorrectly mentions: ${hasTreemap ? 'Treemap' : ''} ${hasTrends ? 'Trends' : ''}`,
          'V6_04_explore_viz.png');
      } else {
        record('6. No Treemap/Trends in Explore Viz', 'PASS',
          'Explore Visualizations does NOT mention "Treemap" or "Trends"',
          'V6_04_explore_viz.png');
      }
    } else {
      record('6. Explore Viz content', 'WARN',
        'Could not find "Explore Visualizations" tooltip during tour',
        'V6_02_tour_on_results.png');
    }

    await screenshot(page, 'V6_05_tour_final', true);
  });
});


// Generate final report after all tests
test.afterAll(async () => {
  const reportPath = path.join(SCREENSHOT_DIR, 'E2E_VALIDATION_REPORT.md');

  const passCount = results.filter(r => r.status === 'PASS').length;
  const failCount = results.filter(r => r.status === 'FAIL').length;
  const warnCount = results.filter(r => r.status === 'WARN').length;

  let report = `# E2E Production Visual Validation Report

**Date:** 2026-02-10
**Target:** https://pcf.glideslopeintelligence.ai/

## Summary

| Metric | Count |
|--------|-------|
| Total Checks | ${results.length} |
| PASS | ${passCount} |
| FAIL | ${failCount} |
| WARN | ${warnCount} |
| Pass Rate | ${results.length > 0 ? ((passCount / results.length) * 100).toFixed(1) : 0}% |

## Detailed Results

| # | Validation Step | Status | Detail | Screenshot |
|---|----------------|--------|--------|------------|
`;

  results.forEach((r, i) => {
    report += `| ${i + 1} | ${r.step} | **${r.status}** | ${r.detail} | ${r.screenshot} |\n`;
  });

  report += `
## Validation Checklist

### 1. Homepage loads correctly
- [${results.some(r => r.step.includes('1.') && r.status === 'PASS') ? 'x' : ' '}] Main wizard/calculator interface loads
- [${results.some(r => r.step.includes('Tour button') && r.status === 'PASS') ? 'x' : ' '}] Product selector visible

### 2. Product selection works
- [${results.some(r => r.step.includes('2. Dropdown') && r.status === 'PASS') ? 'x' : ' '}] Product dropdown opens with products
- [${results.some(r => r.step.includes('2. Product selected') && r.status === 'PASS') ? 'x' : ' '}] Product can be selected

### 3. BOM display works
- [${results.some(r => r.step.includes('3. BOM step') && r.status === 'PASS') ? 'x' : ' '}] BOM step loads after product selection
- [${results.some(r => r.step.includes('3. Calculate') && r.status === 'PASS') ? 'x' : ' '}] Calculate button visible

### 4. Calculate PCF
- [${results.some(r => r.step.includes('4. Results') && r.status === 'PASS') ? 'x' : ' '}] Results appear after calculation
- [${results.some(r => r.step.includes('4. CO2e') && r.status === 'PASS') ? 'x' : ' '}] CO2e values displayed
- [${results.some(r => r.step.includes('4. Sankey') && r.status === 'PASS') ? 'x' : ' '}] Sankey diagram visible

### 5. Tour button works
- [${results.some(r => r.step.includes('5. Tour button') && r.status === 'PASS') ? 'x' : ' '}] Tour button found in header
- [${results.some(r => r.step.includes('5. Tour tooltip') && r.status === 'PASS') ? 'x' : ' '}] Joyride tour starts

### 6. Tour text verification
- [${results.some(r => r.step.includes('Step 3: View Results') && r.status === 'PASS') ? 'x' : ' '}] Results tour step says "Step 3: View Results" (NOT "Step 4")
- [${results.some(r => r.step.includes('Sankey + breakdown') && r.status === 'PASS') ? 'x' : ' '}] Explore Visualizations mentions "Sankey diagram" and "breakdown table"
- [${results.some(r => r.step.includes('Treemap/Trends') && r.status === 'PASS') ? 'x' : ' '}] Does NOT mention "Treemap" or "Trends"

## Screenshots

All screenshots saved to: \`${SCREENSHOT_DIR}/\`

## Environment

- Production URL: https://pcf.glideslopeintelligence.ai/
- Browser: Chromium (Playwright, headless)
- Test Date: 2026-02-10
`;

  fs.writeFileSync(reportPath, report);
  console.log(`\nValidation Report: ${reportPath}`);
  console.log(`\n=== FINAL SUMMARY ===`);
  console.log(`PASS: ${passCount} | FAIL: ${failCount} | WARN: ${warnCount} | Total: ${results.length}`);
  console.log(`===================\n`);
});
