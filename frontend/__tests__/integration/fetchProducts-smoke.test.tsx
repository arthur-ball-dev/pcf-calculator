/**
 * Smoke Test - fetchProducts Export
 * TASK-FE-011: Verify fetchProducts export fixes integration test hang
 *
 * This is a minimal test to verify the ProductSelector component
 * can actually call fetchProducts without hanging.
 */

import { describe, test, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../testUtils';
import ProductSelector from '../../src/components/calculator/ProductSelector';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';

describe('Integration: fetchProducts Export Smoke Test', () => {
  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
  });

  test('ProductSelector renders and loads products without hanging', async () => {
    // Render ProductSelector
    render(<ProductSelector />);

    // Verify loading skeleton appears first
    expect(screen.getByTestId('product-selector-skeleton')).toBeInTheDocument();

    // Wait for products to load from MSW (with reasonable timeout)
    await waitFor(
      () => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // Verify the select component is rendered
    expect(screen.getByRole('combobox')).toBeInTheDocument();

    // Success! If we got here, fetchProducts export works
  }, 10000); // 10 second timeout for the entire test

  test('fetchProducts export exists and is usable', async () => {
    // Import the function directly
    const { fetchProducts } = await import('../../src/services/api/products');

    // Verify it exists and is a function
    expect(fetchProducts).toBeDefined();
    expect(typeof fetchProducts).toBe('function');

    // Verify it can be called (will be mocked by MSW)
    const result = await fetchProducts({ is_finished_product: true });

    // Verify we got a result
    expect(result).toBeDefined();
    expect(Array.isArray(result)).toBe(true);
  });
});
