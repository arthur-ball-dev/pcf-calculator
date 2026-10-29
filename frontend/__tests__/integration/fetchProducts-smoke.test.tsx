/**
 * Smoke Test - fetchProducts Export & ProductList Component
 * TASK-FE-011: Verify fetchProducts export and ProductList rendering
 *
 * Updated for Emerald Night UI rebuild:
 * - ProductSelector replaced by ProductList component
 * - ProductList uses productsAPI.search (not productsAPI.list)
 * - No combobox/dropdown; products display in a full-page list
 * - Loading skeleton has testid "product-list-skeleton"
 */

import { describe, test, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../testUtils';
import ProductList from '../../src/components/calculator/ProductList';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';

describe('Integration: fetchProducts Export Smoke Test', () => {
  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
  });

  test('ProductList renders and loads products without hanging', async () => {
    // Render ProductList
    render(<ProductList />);

    // Verify loading skeleton appears first
    expect(screen.getByTestId('product-list-skeleton')).toBeInTheDocument();

    // Wait for products to load from MSW (with reasonable timeout)
    await waitFor(
      () => {
        expect(screen.queryByTestId('product-list-skeleton')).not.toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // Verify the product list container is rendered
    expect(screen.getByTestId('product-list')).toBeInTheDocument();

    // Verify search input is present
    expect(screen.getByTestId('product-search-input')).toBeInTheDocument();

    // Success! If we got here, ProductList renders and loads data
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
