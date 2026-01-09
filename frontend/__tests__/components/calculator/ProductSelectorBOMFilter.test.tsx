/**
 * ProductSelector BOM Filter Tests
 *
 * TASK-FE-P8-001: Tests for BOM Filter Toggle in ProductSelector
 *
 * Test-Driven Development Protocol:
 * - These tests MUST be committed BEFORE implementation
 * - Tests should FAIL initially (toggle component not implemented)
 * - Implementation must make tests PASS without modifying tests
 *
 * Test Scenarios:
 * 1. Toggle renders in default state ("With BOMs" selected)
 * 2. Toggle state change triggers re-search with correct API params
 * 3. Filter persists during search query typing
 * 4. Accessibility requirements (keyboard navigation)
 * 5. Visual feedback for active state
 * 6. Integration with existing ProductSelector behavior
 *
 * UI Requirements:
 * - Toggle visible above search input
 * - "With BOMs" option selected by default
 * - "All Products" option available
 * - Clear visual feedback for active state
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, userEvent } from '../../testUtils';
import ProductSelector from '../../../src/components/calculator/ProductSelector';
import { useWizardStore } from '../../../src/store/wizardStore';
import { useCalculatorStore } from '../../../src/store/calculatorStore';
import { productsAPI } from '../../../src/services/api/products';
import { emissionFactorsAPI } from '../../../src/services/api/emissionFactors';

// Mock the APIs
vi.mock('../../../src/services/api/products', () => ({
  productsAPI: {
    search: vi.fn(),
    getById: vi.fn(),
    list: vi.fn(),
  },
  fetchProducts: vi.fn(),
}));

vi.mock('../../../src/services/api/emissionFactors', () => ({
  emissionFactorsAPI: {
    list: vi.fn(),
  },
}));

// Mock products data - products WITH BOM
const mockProductsWithBOM = [
  {
    id: 'with-bom-1',
    code: 'MOTOR-001',
    name: 'Electric Motor Assembly',
    category: 'Electronics',
    unit: 'unit',
    is_finished_product: true,
    bill_of_materials: [
      { child_product_id: 'child-1', quantity: 2 },
    ],
  },
  {
    id: 'with-bom-2',
    code: 'WIDGET-001',
    name: 'Widget Assembly',
    category: 'Manufacturing',
    unit: 'unit',
    is_finished_product: true,
    bill_of_materials: [
      { child_product_id: 'child-2', quantity: 1 },
    ],
  },
];

// Mock products data - ALL products (including those without BOM)
const mockAllProducts = [
  ...mockProductsWithBOM,
  {
    id: 'no-bom-1',
    code: 'RAW-001',
    name: 'Raw Material A',
    category: 'Raw Materials',
    unit: 'kg',
    is_finished_product: true,
    bill_of_materials: [],
  },
  {
    id: 'no-bom-2',
    code: 'SIMPLE-001',
    name: 'Simple Product',
    category: 'General',
    unit: 'unit',
    is_finished_product: true,
    bill_of_materials: [],
  },
];

// Mock emission factors
const mockEmissionFactors = [
  {
    id: 'ef-1',
    activity_name: 'Manufacturing',
    unit: 'kg',
    co2e_per_unit: 5.0,
    data_source: 'EPA',
    geography: 'US',
    is_active: true,
  },
];

describe('ProductSelector BOM Filter Toggle', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();

    // Reset mocks
    vi.clearAllMocks();

    // Default mock implementations
    vi.mocked(emissionFactorsAPI.list).mockResolvedValue(mockEmissionFactors);
    vi.mocked(productsAPI.getById).mockResolvedValue(mockProductsWithBOM[0]);

    // Default: return products with BOM (matches default filter state)
    vi.mocked(productsAPI.search).mockImplementation(async (params) => {
      if (params?.has_bom === true) {
        return {
          items: mockProductsWithBOM,
          total: mockProductsWithBOM.length,
          has_more: false,
        };
      } else if (params?.has_bom === false || params?.has_bom === undefined) {
        return {
          items: mockAllProducts,
          total: mockAllProducts.length,
          has_more: false,
        };
      }
      return {
        items: mockAllProducts,
        total: mockAllProducts.length,
        has_more: false,
      };
    });
  });

  describe('Scenario 5: Toggle Renders in Default State', () => {
    test('toggle is visible when component loads', async () => {
      render(<ProductSelector />);

      // Wait for component to load
      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Toggle buttons should be visible
      expect(screen.getByTestId('bom-filter-with-bom')).toBeInTheDocument();
      expect(screen.getByTestId('bom-filter-all')).toBeInTheDocument();
    });

    test('"With BOMs" option is selected by default', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const withBomsButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // "With BOMs" should have active styling (aria-pressed or similar)
      expect(withBomsButton).toHaveAttribute('aria-pressed', 'true');
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');
    });

    test('default search triggers API with has_bom=true', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open the dropdown to trigger search
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Wait for API call
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Verify has_bom=true was passed
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBe(true);
    });

    test('toggle displays clear labels', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      expect(screen.getByText('With BOMs')).toBeInTheDocument();
      expect(screen.getByText('All Products')).toBeInTheDocument();
    });
  });

  describe('Scenario 6: Toggle State Change Triggers Re-search', () => {
    test('clicking "All Products" updates filter state', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const allProductsButton = screen.getByTestId('bom-filter-all');
      await user.click(allProductsButton);

      // State should update
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
      expect(screen.getByTestId('bom-filter-with-bom')).toHaveAttribute('aria-pressed', 'false');
    });

    test('clicking "All Products" triggers API without has_bom filter', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown first
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Wait for initial search
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Clear mock to track new calls
      vi.mocked(productsAPI.search).mockClear();

      // Click "All Products"
      const allProductsButton = screen.getByTestId('bom-filter-all');
      await user.click(allProductsButton);

      // Wait for new API call
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Verify has_bom is undefined or not present
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBeUndefined();
    });

    test('switching back to "With BOMs" triggers API with has_bom=true', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Wait for initial search
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Click "All Products" first
      const allProductsButton = screen.getByTestId('bom-filter-all');
      await user.click(allProductsButton);

      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalledTimes(2);
      });

      // Now click "With BOMs" again
      vi.mocked(productsAPI.search).mockClear();
      const withBomsButton = screen.getByTestId('bom-filter-with-bom');
      await user.click(withBomsButton);

      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Verify has_bom=true
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBe(true);
    });

    test('product list updates when filter changes', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Initially should show only products with BOM
      await waitFor(() => {
        expect(screen.getByText('Electric Motor Assembly')).toBeInTheDocument();
      });

      // "Raw Material A" should NOT be visible (no BOM)
      expect(screen.queryByText('Raw Material A')).not.toBeInTheDocument();

      // Switch to "All Products"
      const allProductsButton = screen.getByTestId('bom-filter-all');
      await user.click(allProductsButton);

      // Now all products should be visible
      await waitFor(() => {
        expect(screen.getByText('Raw Material A')).toBeInTheDocument();
        expect(screen.getByText('Simple Product')).toBeInTheDocument();
      });
    });
  });

  describe('Scenario 7: Filter Persists During Search', () => {
    test('typing search query keeps "With BOMs" filter active', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Ensure "With BOMs" is active
      expect(screen.getByTestId('bom-filter-with-bom')).toHaveAttribute('aria-pressed', 'true');

      // Open dropdown and type in search
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Wait for dropdown to open
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Find the search input and type
      const searchInput = screen.getByPlaceholderText(/search/i);
      vi.mocked(productsAPI.search).mockClear();
      await user.type(searchInput, 'motor');

      // Wait for debounced search
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      }, { timeout: 500 });

      // Verify has_bom=true is still passed with the query
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBe(true);
      expect(lastCall[0]?.query).toContain('motor');
    });

    test('typing search query keeps "All Products" filter when selected', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Switch to "All Products"
      const allProductsButton = screen.getByTestId('bom-filter-all');
      await user.click(allProductsButton);

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Type in search
      const searchInput = screen.getByPlaceholderText(/search/i);
      vi.mocked(productsAPI.search).mockClear();
      await user.type(searchInput, 'raw');

      // Wait for debounced search
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      }, { timeout: 500 });

      // Verify has_bom is undefined (All Products filter)
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBeUndefined();
    });

    test('clearing search query maintains filter state', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown and type
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      const searchInput = screen.getByPlaceholderText(/search/i);
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      }, { timeout: 500 });

      // Clear the search
      vi.mocked(productsAPI.search).mockClear();
      await user.clear(searchInput);

      // Wait for search to trigger
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      }, { timeout: 500 });

      // Filter should still be "With BOMs" (has_bom=true)
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBe(true);
    });
  });

  describe('Accessibility', () => {
    test('toggle buttons are keyboard navigable', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const withBomsButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Focus on first button
      withBomsButton.focus();
      expect(withBomsButton).toHaveFocus();

      // Tab to next button
      await user.tab();
      expect(allProductsButton).toHaveFocus();

      // Press Enter to activate
      await user.keyboard('{Enter}');

      // Should now be selected
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
    });

    test('toggle buttons have correct ARIA attributes', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const withBomsButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Both buttons should have role="button" (implicit for button elements)
      expect(withBomsButton.tagName).toBe('BUTTON');
      expect(allProductsButton.tagName).toBe('BUTTON');

      // Should have aria-pressed
      expect(withBomsButton).toHaveAttribute('aria-pressed');
      expect(allProductsButton).toHaveAttribute('aria-pressed');
    });

    test('toggle buttons have accessible labels', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Buttons should have accessible names
      expect(screen.getByRole('button', { name: /with boms/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /all products/i })).toBeInTheDocument();
    });

    test('toggle buttons can be activated with Space key', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Focus and press Space
      allProductsButton.focus();
      await user.keyboard(' ');

      // Should now be selected
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('Visual Feedback', () => {
    test('active toggle button has distinct visual styling', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const withBomsButton = screen.getByTestId('bom-filter-with-bom');

      // Active button should have specific class for styling
      // The implementation should use data-state or className to indicate active
      expect(withBomsButton).toHaveAttribute('aria-pressed', 'true');
    });

    test('toggle group has visible container', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Toggle container should exist
      expect(screen.getByTestId('bom-filter-toggle-group')).toBeInTheDocument();
    });

    test('toggle has label text "Show:"', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Should have descriptive label
      expect(screen.getByText('Show:')).toBeInTheDocument();
    });
  });

  describe('Integration with Existing Functionality', () => {
    test('filter does not interfere with product selection', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Wait for products
      await waitFor(() => {
        expect(screen.getByText('Electric Motor Assembly')).toBeInTheDocument();
      });

      // Select a product
      await user.click(screen.getByText('Electric Motor Assembly'));

      // Verify selection
      await waitFor(() => {
        const calculatorState = useCalculatorStore.getState();
        expect(calculatorState.selectedProductId).toBe('with-bom-1');
      });

      // Wizard step should be marked complete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('select');
      });
    });

    test('filter works with is_finished_product filter', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalled();
      });

      // Verify both filters are applied
      const lastCall = vi.mocked(productsAPI.search).mock.calls.slice(-1)[0];
      expect(lastCall[0]?.has_bom).toBe(true);
      expect(lastCall[0]?.is_finished_product).toBe(true);
    });

    test('confirmation message appears after selecting product with filter active', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown and select
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText('Electric Motor Assembly')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Electric Motor Assembly'));

      // Confirmation should appear
      await waitFor(() => {
        expect(screen.getByText(/Product selected/i)).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles empty results with "With BOMs" filter gracefully', async () => {
      vi.mocked(productsAPI.search).mockResolvedValue({
        items: [],
        total: 0,
        has_more: false,
      });

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Should show empty state or no products message
      await waitFor(() => {
        expect(screen.queryByText('Electric Motor Assembly')).not.toBeInTheDocument();
      });
    });

    test('filter state resets when component remounts', async () => {
      const { unmount } = render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Switch to "All Products"
      const allProductsButton = screen.getByTestId('bom-filter-all');
      await user.click(allProductsButton);
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');

      // Unmount
      unmount();

      // Remount
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Should be back to default "With BOMs"
      expect(screen.getByTestId('bom-filter-with-bom')).toHaveAttribute('aria-pressed', 'true');
    });

    test('rapid toggle clicks do not cause race conditions', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const withBomsButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Rapid clicks
      await user.click(allProductsButton);
      await user.click(withBomsButton);
      await user.click(allProductsButton);

      // Final state should be "All Products"
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
      expect(withBomsButton).toHaveAttribute('aria-pressed', 'false');
    });
  });
});
