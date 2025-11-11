/**
 * BUG-002 Diagnostic Test
 *
 * This test manually steps through the wizard to capture console output
 * and confirm the root cause of wizard navigation failure from Step 1 to Step 2.
 *
 * Expected behavior:
 * 1. Load page
 * 2. Select product → should add 'select' to completedSteps
 * 3. Click Next → should navigate to Step 2 (edit)
 *
 * Actual behavior (BUG-002):
 * - Next button doesn't navigate forward
 * - Debug warning should show completedSteps status
 */

import { test, expect } from '@playwright/test';

test.describe('BUG-002 Diagnosis: Wizard Navigation Broken', () => {
  test('capture console output when clicking Next from Step 1', async ({ page }) => {
    const consoleMessages: string[] = [];
    const consoleWarnings: string[] = [];

    // Capture all console messages
    page.on('console', (msg) => {
      const text = msg.text();
      consoleMessages.push(text);

      if (msg.type() === 'warning') {
        consoleWarnings.push(text);
        console.log('[BROWSER WARNING]:', text);
      } else if (msg.type() === 'log') {
        console.log('[BROWSER LOG]:', text);
      } else if (msg.type() === 'error') {
        console.log('[BROWSER ERROR]:', text);
      }
    });

    // Navigate to app
    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // Wait for ProductSelector to load
    await page.waitForSelector('[data-testid="product-selector"]', { timeout: 10000 });

    console.log('\n=== STEP 1: Product Selection ===');

    // Open the Select dropdown
    const selectTrigger = page.locator('[data-testid="product-select-trigger"]');
    await selectTrigger.click();
    await page.waitForTimeout(500);

    // Select a product
    const productOption = page.locator('[data-testid="product-option-86ec41d652904f738c7f0cd85bfba490"]').first();
    await productOption.click();
    await page.waitForTimeout(1000);

    console.log('Product selected, waiting for step completion...');

    // Check if confirmation appears
    const confirmation = page.locator('[data-testid="product-selected-confirmation"]');
    await expect(confirmation).toBeVisible({ timeout: 5000 });

    console.log('\n=== Checking Zustand Store State ===');

    // Inspect wizardStore state
    const wizardState = await page.evaluate(() => {
      // @ts-ignore - accessing window for debugging
      const store = window.zustandStores?.wizardStore?.getState();
      return store || null;
    });

    console.log('Wizard State:', JSON.stringify(wizardState, null, 2));

    console.log('\n=== STEP 2: Click Next Button ===');

    // Find Next button
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeEnabled({ timeout: 5000 });

    console.log('Next button is enabled, clicking...');
    await nextButton.click();
    await page.waitForTimeout(2000);

    console.log('\n=== Post-Click State ===');

    // Check current step after clicking Next
    const stepIndicator = page.locator('text=/Step \\d of 4/');
    const stepText = await stepIndicator.textContent();
    console.log('Current step indicator:', stepText);

    // Capture final wizard state
    const finalWizardState = await page.evaluate(() => {
      // @ts-ignore
      const store = window.zustandStores?.wizardStore?.getState();
      return store || null;
    });

    console.log('Final Wizard State:', JSON.stringify(finalWizardState, null, 2));

    console.log('\n=== Console Messages Summary ===');
    console.log(`Total messages: ${consoleMessages.length}`);
    console.log(`Warnings: ${consoleWarnings.length}`);

    if (consoleWarnings.length > 0) {
      console.log('\nWarnings captured:');
      consoleWarnings.forEach((warning, idx) => {
        console.log(`  ${idx + 1}. ${warning}`);
      });
    }

    // Test assertions
    console.log('\n=== Verification ===');

    if (stepText?.includes('Step 1')) {
      console.log('❌ FAILED: Still on Step 1 after clicking Next');
      console.log('BUG-002 CONFIRMED: Navigation from Step 1 to Step 2 is broken');
    } else if (stepText?.includes('Step 2')) {
      console.log('✓ PASSED: Successfully navigated to Step 2');
      console.log('BUG-002 is FIXED or not reproduced');
    }

    // Make test fail if still on Step 1 (to highlight the bug)
    expect(stepText).toContain('Step 2');
  });
});
