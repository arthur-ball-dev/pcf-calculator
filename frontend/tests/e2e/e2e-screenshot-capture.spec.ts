import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const SCREENSHOT_DIR = '/home/mydev/projects/PCF/product-lca-carbon-calculator/e2e-screenshots';

// Ensure screenshot directory exists
test.beforeAll(async () => {
  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }
});

// Helper function to dismiss any joyride overlays
async function dismissJoyride(page: any) {
  try {
    // Check for joyride portal
    const joyridePortal = page.locator('#react-joyride-portal');
    if (await joyridePortal.isVisible({ timeout: 1000 }).catch(() => false)) {
      // Try to click Skip or close button
      const skipButton = page.getByRole('button', { name: /skip|close|done|finish/i });
      if (await skipButton.isVisible({ timeout: 500 }).catch(() => false)) {
        await skipButton.click();
        await page.waitForTimeout(500);
      } else {
        // Press Escape to close
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
      }
    }

    // Also try removing via JavaScript
    await page.evaluate(() => {
      const portal = document.getElementById('react-joyride-portal');
      if (portal) portal.remove();

      // Also remove any spotlight overlay
      const spotlights = document.querySelectorAll('[data-test-id="spotlight"]');
      spotlights.forEach(el => el.remove());

      // Remove any overlay
      const overlays = document.querySelectorAll('.react-joyride__overlay');
      overlays.forEach(el => el.remove());
    });
    await page.waitForTimeout(200);
  } catch (e) {
    // Joyride might not be present
  }
}

test.describe('E2E Visual Testing - Complete Screenshot Capture', () => {
  test('01 - Main Page Load', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Wait for the app to fully render
    await page.waitForTimeout(1000);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '01_main_page.png'),
      fullPage: true
    });

    // Verify main elements exist
    await expect(page.locator('body')).toBeVisible();
    console.log('Screenshot saved: 01_main_page.png');
  });

  test('02 - Product Dropdown Opens', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Dismiss any tutorial overlays
    await dismissJoyride(page);

    // Look for the product selector/combobox
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '02_product_dropdown.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 02_product_dropdown.png');
  });

  test('03 - Product Selected', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Open dropdown and select a product
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(500);

      // Try to find and click a product option
      const option = page.locator('[role="option"]').first();
      if (await option.isVisible({ timeout: 2000 }).catch(() => false)) {
        await option.click();
        await page.waitForTimeout(1000);
      }
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '03_product_selected.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 03_product_selected.png');
  });

  test('04 - BOM View', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Select a product with BOM
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(500);

      // Look for a finished product option
      const options = page.locator('[role="option"]');
      const count = await options.count();
      if (count > 0) {
        // Click first available product
        await options.first().click();
        await page.waitForTimeout(1500);
      }
    }

    await dismissJoyride(page);

    // Look for BOM content or proceed to next step
    const nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.click({ force: true });
      await page.waitForTimeout(1000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '04_bom_view.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 04_bom_view.png');
  });

  test('05 - Emission Factors', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Navigate through wizard to emission factors
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(300);

      const option = page.locator('[role="option"]').first();
      if (await option.isVisible({ timeout: 2000 }).catch(() => false)) {
        await option.click();
        await page.waitForTimeout(1000);
      }
    }

    await dismissJoyride(page);

    // Click Next to go to BOM step
    let nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.click({ force: true });
      await page.waitForTimeout(1000);
    }

    // Look for emission factor dropdown in BOM
    const efDropdown = page.locator('[role="combobox"]').nth(1);
    if (await efDropdown.isVisible({ timeout: 2000 }).catch(() => false)) {
      await efDropdown.click({ force: true });
      await page.waitForTimeout(500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '05_emission_factors.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 05_emission_factors.png');
  });

  test('06 - Full Wizard Flow', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Step 1: Select product
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(300);

      // Search for a specific product
      await page.keyboard.type('Laptop');
      await page.waitForTimeout(500);

      const option = page.locator('[role="option"]').first();
      if (await option.isVisible({ timeout: 2000 }).catch(() => false)) {
        await option.click();
        await page.waitForTimeout(1000);
      }
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '06_wizard_step1_product.png'),
      fullPage: true
    });

    await dismissJoyride(page);

    // Step 2: Click Next
    let nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '07_wizard_step2_bom.png'),
      fullPage: true
    });

    await dismissJoyride(page);

    // Step 3: Click Next again
    nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.click({ force: true });
      await page.waitForTimeout(1000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '08_wizard_step3_review.png'),
      fullPage: true
    });

    await dismissJoyride(page);

    // Step 4: Calculate or Final step
    const calculateButton = page.getByRole('button', { name: /calculate|submit|finish/i });
    if (await calculateButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await calculateButton.click({ force: true });
      await page.waitForTimeout(2000);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '09_wizard_step4_results.png'),
      fullPage: true
    });
    console.log('Screenshot saved: Wizard flow steps 06-09');
  });

  test('07 - Search Functionality', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Open product dropdown
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(300);

      // Type search query
      await page.keyboard.type('Phone');
      await page.waitForTimeout(800);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '10_search_results.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 10_search_results.png');
  });

  test('08 - Mobile Viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone X
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await dismissJoyride(page);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '11_mobile_view.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 11_mobile_view.png');
  });

  test('09 - Tablet Viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await dismissJoyride(page);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '12_tablet_view.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 12_tablet_view.png');
  });

  test('10 - Error State Simulation', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Try to trigger validation by clicking Next without selection
    const nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.click({ force: true });
      await page.waitForTimeout(500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '13_error_state.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 13_error_state.png');
  });

  test('11 - BOM Table with Multiple Items', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    await dismissJoyride(page);

    // Select a product with multiple BOM items
    const combobox = page.locator('[role="combobox"]').first();
    if (await combobox.isVisible()) {
      await combobox.click({ force: true });
      await page.waitForTimeout(300);

      // Search for Backpack which typically has multiple materials
      await page.keyboard.type('Backpack');
      await page.waitForTimeout(500);

      const option = page.locator('[role="option"]').first();
      if (await option.isVisible({ timeout: 2000 }).catch(() => false)) {
        await option.click();
        await page.waitForTimeout(1500);
      }
    }

    await dismissJoyride(page);

    // Navigate to BOM view
    const nextButton = page.getByRole('button', { name: /next|continue/i });
    if (await nextButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nextButton.click({ force: true });
      await page.waitForTimeout(1500);
    }

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '14_bom_table_items.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 14_bom_table_items.png');
  });

  test('12 - All Components Rendered', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Wait for all lazy-loaded components
    await page.waitForTimeout(2000);

    await dismissJoyride(page);

    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '15_all_components.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 15_all_components.png');
  });

  test('13 - Joyride Tutorial (if available)', async ({ page }) => {
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Capture the joyride tutorial if it appears
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '16_joyride_tutorial.png'),
      fullPage: true
    });
    console.log('Screenshot saved: 16_joyride_tutorial.png');
  });
});
