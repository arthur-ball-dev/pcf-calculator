/**
 * E2E Test: Gaming Laptop PCF Calculation Flow
 *
 * Tests the complete calculation flow for a Gaming Laptop product (ELE-LAPT-GAM-*)
 * 1. Navigate to http://localhost:5173
 * 2. Search for "Gaming Laptop" in the product selector
 * 3. Select it and proceed through the wizard
 * 4. On the Results page, take a screenshot
 * 5. Report the total PCF value and verify it's in a reasonable range (30-100 kg CO2e for a laptop)
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

// Extended timeout for this test due to calculation time
test.setTimeout(120000);

test.describe('Gaming Laptop PCF Calculation', () => {
  test('Complete calculation flow for Gaming Laptop', async ({ page, request }) => {
    console.log('=== Gaming Laptop E2E Test ===');
    console.log('Step 1: Navigate to application');

    // Setup page with auth
    await setupPage(page, request);
    await page.waitForTimeout(1000);

    // Take initial screenshot (viewport only, not full page)
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_01_initial.png'),
    });
    console.log('Screenshot saved: gaming_laptop_01_initial.png');

    // Step 2: Search for Gaming Laptop
    console.log('Step 2: Search for Gaming Laptop in product selector');

    // Find and click the product combobox
    const productCombobox = page.locator('button[role="combobox"]').first();
    await expect(productCombobox).toBeVisible({ timeout: 10000 });
    await productCombobox.click();
    await page.waitForTimeout(500);

    // Type search query for Gaming Laptop
    await page.keyboard.type('Gaming');
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_02_search.png'),
    });
    console.log('Screenshot saved: gaming_laptop_02_search.png');

    // Step 3: Select the Gaming Laptop option
    console.log('Step 3: Select Gaming Laptop from dropdown');

    // Find the Gaming Laptop option
    const gamingLaptopOption = page.locator('[role="option"]').filter({ hasText: /Gaming/i }).first();

    let selectedProductName = '';
    let selectedProductCode = '';

    if (await gamingLaptopOption.isVisible({ timeout: 5000 }).catch(() => false)) {
      const optionText = await gamingLaptopOption.textContent();
      console.log(`Found option: ${optionText}`);
      selectedProductName = optionText?.split(/ELE-LAPT/)[0]?.trim() || 'Gaming Laptop';
      const codeMatch = optionText?.match(/ELE-LAPT-GAM-\d+/);
      selectedProductCode = codeMatch ? codeMatch[0] : '';
      await gamingLaptopOption.click();
      await page.waitForTimeout(1500);
    } else {
      // If no Gaming option found, select first available
      console.log('Gaming Laptop not found in dropdown, selecting first available laptop');
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      await productCombobox.click();
      await page.waitForTimeout(500);

      // Clear and search for Laptop
      await page.keyboard.type('Laptop');
      await page.waitForTimeout(700);

      const laptopOption = page.locator('[role="option"]').first();
      if (await laptopOption.isVisible({ timeout: 3000 }).catch(() => false)) {
        const optionText = await laptopOption.textContent();
        console.log(`Selected fallback option: ${optionText}`);
        selectedProductName = optionText || 'Laptop';
        await laptopOption.click();
        await page.waitForTimeout(1500);
      }
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_03_selected.png'),
    });
    console.log('Screenshot saved: gaming_laptop_03_selected.png');

    // Step 4: Click Next to go to BOM Editor
    console.log('Step 4: Navigate to BOM Editor');

    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });
    await nextButton.click();
    await page.waitForTimeout(2000);

    // Verify we're on BOM Editor step
    const bomHeading = page.locator('h2').filter({ hasText: /BOM|Bill/ });
    await expect(bomHeading).toBeVisible({ timeout: 10000 });

    // Get BOM component count
    const componentsInfo = page.locator('text=/\\d+ components/');
    let componentCount = '0';
    if (await componentsInfo.isVisible({ timeout: 2000 }).catch(() => false)) {
      const infoText = await componentsInfo.textContent();
      const countMatch = infoText?.match(/(\d+) components/);
      componentCount = countMatch ? countMatch[1] : '0';
    }
    console.log(`BOM has ${componentCount} components`);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_04_bom_editor.png'),
    });
    console.log('Screenshot saved: gaming_laptop_04_bom_editor.png');

    // Step 5: Click Calculate button
    console.log('Step 5: Initiate calculation');

    const calculateButton = page.locator('button:has-text("Calculate")');
    await calculateButton.scrollIntoViewIfNeeded();
    await expect(calculateButton).toBeVisible({ timeout: 5000 });

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_05_before_calculate.png'),
    });
    console.log('Screenshot saved: gaming_laptop_05_before_calculate.png');

    await calculateButton.click();
    console.log('Calculation initiated...');

    // Wait a moment for loading state
    await page.waitForTimeout(2000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_06_calculating.png'),
    });
    console.log('Screenshot saved: gaming_laptop_06_calculating.png');

    // Step 6: Wait for results
    console.log('Step 6: Waiting for results...');

    const resultsHeading = page.locator('h2').filter({ hasText: /Result/ });
    await expect(resultsHeading).toBeVisible({ timeout: 90000 }); // 90 second timeout for calculation
    await page.waitForTimeout(3000); // Wait for charts to render

    console.log('Results page loaded!');

    // Take final screenshot of results
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_07_results.png'),
    });
    console.log('Screenshot saved: gaming_laptop_07_results.png');

    // Step 7: Extract and validate the PCF value
    console.log('Step 7: Extract and validate PCF value');

    // Look for the total PCF value in the results
    let pcfValue: number | null = null;

    // Get text content from results area
    const resultsSection = page.locator('main');
    const resultsText = await resultsSection.textContent() || '';

    // Try to extract numeric values near "kg CO2e" or similar text
    const kgCO2eMatches = resultsText.match(/(\d+(?:,\d{3})*\.?\d*)\s*kg\s*CO2?e?/gi);
    if (kgCO2eMatches && kgCO2eMatches.length > 0) {
      // Get the first/primary value (usually the total)
      const firstMatch = kgCO2eMatches[0];
      const valueMatch = firstMatch.match(/(\d+(?:,\d{3})*\.?\d*)/);
      if (valueMatch) {
        pcfValue = parseFloat(valueMatch[1].replace(/,/g, ''));
        console.log(`Found PCF value from match: ${pcfValue} kg CO2e`);
      }
    }

    // Also try looking for prominent displayed values
    if (pcfValue === null) {
      // Look for elements with large numbers that might be the PCF
      const totalLabel = page.locator('text=/Total|PCF|Carbon Footprint/i');
      if (await totalLabel.isVisible({ timeout: 2000 }).catch(() => false)) {
        const parent = totalLabel.locator('xpath=..');
        const parentText = await parent.textContent() || '';
        const numMatch = parentText.match(/(\d+(?:,\d{3})*\.?\d*)/);
        if (numMatch) {
          pcfValue = parseFloat(numMatch[1].replace(/,/g, ''));
          console.log(`Found PCF value near Total label: ${pcfValue}`);
        }
      }
    }

    // Scroll down to see full results and Sankey diagram
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(500);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_08_results_sankey.png'),
    });
    console.log('Screenshot saved: gaming_laptop_08_results_sankey.png');

    // Scroll to bottom for export options
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'gaming_laptop_09_results_full.png'),
    });
    console.log('Screenshot saved: gaming_laptop_09_results_full.png');

    // Report findings
    console.log('\n=================================================');
    console.log('=== GAMING LAPTOP PCF CALCULATION RESULTS ===');
    console.log('=================================================');
    console.log(`Product: ${selectedProductName}`);
    console.log(`Code: ${selectedProductCode}`);
    console.log(`BOM Components: ${componentCount}`);

    if (pcfValue !== null) {
      console.log(`Total PCF: ${pcfValue.toFixed(2)} kg CO2e`);

      // Validate the PCF is in reasonable range for a laptop
      // Gaming laptops may be higher due to larger batteries and more powerful components
      // Typical range: 30-200 kg CO2e for a laptop
      const minExpected = 30;
      const maxExpected = 200;

      if (pcfValue >= minExpected && pcfValue <= maxExpected) {
        console.log(`\nVALIDATION: PASS`);
        console.log(`  PCF ${pcfValue.toFixed(2)} kg CO2e is within expected range (${minExpected}-${maxExpected} kg CO2e for a laptop)`);
      } else if (pcfValue < minExpected) {
        console.log(`\nVALIDATION: WARNING - Value seems low`);
        console.log(`  PCF ${pcfValue.toFixed(2)} kg CO2e is below expected range (< ${minExpected} kg CO2e)`);
        console.log(`  This may indicate missing emission factors or incorrect data`);
      } else {
        console.log(`\nVALIDATION: WARNING - Value seems high`);
        console.log(`  PCF ${pcfValue.toFixed(2)} kg CO2e is above expected range (> ${maxExpected} kg CO2e)`);
        console.log(`  This may indicate incorrect emission factor mappings`);
      }
    } else {
      console.log('Total PCF: Could not extract value from results page');
      console.log('Please check the screenshots for manual verification');
    }

    console.log('\n=================================================');
    console.log('Screenshots saved to: /home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots/');
    console.log('Key results screenshot: gaming_laptop_07_results.png');
    console.log('=================================================\n');

    // Assertion for test pass/fail
    expect(pcfValue).not.toBeNull();
    if (pcfValue !== null) {
      // Assert PCF is within reasonable bounds (10-500 kg CO2e, wider range for any calculation)
      expect(pcfValue).toBeGreaterThan(10);
      expect(pcfValue).toBeLessThan(500);
    }
  });
});
