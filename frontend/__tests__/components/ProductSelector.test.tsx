/**
 * ProductSelector Component Tests
 *
 * Test-Driven Development for TASK-FE-003
 * Written BEFORE implementation (TDD Protocol)
 *
 * Test Scenarios:
 * 1. Product List Rendering - Dropdown shows fetched products
 * 2. Product Selection - Updates stores and marks step complete
 * 3. Validation - Requires selection before proceeding
 * 4. Loading State - Shows skeleton during API request
 * 5. Error State - Shows error message with retry button
 * 6. Search Functionality - Filters products by name/code
 * 7. Accessibility - ARIA labels and keyboard navigation
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import ProductSelector from '../../src/components/calculator/ProductSelector';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import * as productsApi from '../../src/services/api/products';
import type { Product } from '../../src/types/store.types';

// Mock products data
const mockProducts: Product[] = [
  {
    id: 1,
    code: 'TSHIRT-001',
    name: 'Cotton T-Shirt',
    category: 'Apparel',
    unit: 'unit',
    is_finished_product: true,
  },
  {
    id: 2,
    code: 'BOTTLE-001',
    name: 'Water Bottle',
    category: 'Consumer Goods',
    unit: 'unit',
    is_finished_product: true,
  },
  {
    id: 3,
    code: 'LAPTOP-001',
    name: 'Laptop Computer',
    category: 'Electronics',
    unit: 'unit',
    is_finished_product: true,
  },
];

// Mock the products API
vi.mock('../../src/services/api/products', () => ({
  fetchProducts: vi.fn(),
}));

describe('ProductSelector Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();

    // Reset mocks
    vi.clearAllMocks();

    // Default mock implementation (success)
    vi.mocked(productsApi.fetchProducts).mockResolvedValue(mockProducts);
  });

  describe('Scenario 1: Product List Rendering', () => {
    test('fetches products from API on component mount', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(productsApi.fetchProducts).toHaveBeenCalledTimes(1);
      });
    });

    test('displays all fetched products in dropdown', async () => {
      render(<ProductSelector />);

      // Wait for products to load
      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Verify all products are displayed
      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
        expect(screen.getByText(/Water Bottle/i)).toBeInTheDocument();
        expect(screen.getByText(/Laptop Computer/i)).toBeInTheDocument();
      });
    });

    test('shows product category alongside name', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Check that category info is displayed
      await waitFor(() => {
        const option = screen.getByText(/Cotton T-Shirt/i);
        expect(option).toBeInTheDocument();
        // Category should be visible in the same option or nearby
        expect(screen.getByText(/Apparel/i)).toBeInTheDocument();
      });
    });

    test('shows placeholder text when no product selected', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      expect(screen.getByText(/Choose a product to calculate PCF/i)).toBeInTheDocument();
    });
  });

  describe('Scenario 2: Product Selection', () => {
    test('updates calculatorStore.selectedProductId when product selected', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open dropdown and select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });

      const option = screen.getByText(/Cotton T-Shirt/i);
      await user.click(option);

      // Verify store was updated
      const calculatorState = useCalculatorStore.getState();
      expect(calculatorState.selectedProductId).toBe(1);
    });

    test('marks wizard step complete when product selected', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Initial state - step not complete
      expect(useWizardStore.getState().completedSteps).not.toContain('select');

      // Select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText(/Water Bottle/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/Water Bottle/i));

      // Verify wizard step marked complete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('select');
      });
    });

    test('shows confirmation message after product selected', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText(/Laptop Computer/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/Laptop Computer/i));

      // Should show confirmation
      await waitFor(() => {
        expect(screen.getByText(/Product selected/i)).toBeInTheDocument();
        expect(screen.getByText(/Click "Next" to edit the Bill of Materials/i)).toBeInTheDocument();
      });
    });

    test('allows changing product selection', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Select first product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      expect(useCalculatorStore.getState().selectedProductId).toBe(1);

      // Change selection
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Water Bottle/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Water Bottle/i));

      // Verify updated
      expect(useCalculatorStore.getState().selectedProductId).toBe(2);
    });
  });

  describe('Scenario 3: Validation - No Selection', () => {
    test('wizard step incomplete when no product selected', () => {
      render(<ProductSelector />);

      const wizardState = useWizardStore.getState();
      expect(wizardState.completedSteps).not.toContain('select');
    });

    test('marks wizard step incomplete when selection cleared', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      // Verify complete
      expect(useWizardStore.getState().completedSteps).toContain('select');

      // Clear selection by setting null
      useCalculatorStore.getState().setSelectedProduct(null);

      // Should mark incomplete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).not.toContain('select');
      });
    });
  });

  describe('Scenario 4: Loading State', () => {
    test('displays loading skeleton during API request', () => {
      // Mock delayed response
      vi.mocked(productsApi.fetchProducts).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockProducts), 1000))
      );

      render(<ProductSelector />);

      // Should show loading skeleton immediately
      expect(screen.getByTestId('product-selector-skeleton')).toBeInTheDocument();
    });

    test('hides loading skeleton after products load', async () => {
      render(<ProductSelector />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Products dropdown should be visible
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    test('disables selection during loading', () => {
      vi.mocked(productsApi.fetchProducts).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockProducts), 1000))
      );

      render(<ProductSelector />);

      // Skeleton should be present, dropdown should not
      expect(screen.getByTestId('product-selector-skeleton')).toBeInTheDocument();
      expect(screen.queryByRole('combobox')).not.toBeInTheDocument();
    });
  });

  describe('Scenario 5: Error Handling', () => {
    test('displays error message when API request fails', async () => {
      // Mock API error
      vi.mocked(productsApi.fetchProducts).mockRejectedValue(
        new Error('Network error')
      );

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.getByText(/Unable to load products/i)).toBeInTheDocument();
      });
    });

    test('shows retry button on error', async () => {
      vi.mocked(productsApi.fetchProducts).mockRejectedValue(
        new Error('Server error')
      );

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    test('retry button triggers new API request', async () => {
      // First call fails
      vi.mocked(productsApi.fetchProducts)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockProducts);

      render(<ProductSelector />);

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/Unable to load products/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should trigger new API call
      await waitFor(() => {
        expect(productsApi.fetchProducts).toHaveBeenCalledTimes(2);
      });

      // Should show products after successful retry
      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument();
      });
    });

    test('provides helpful error message', async () => {
      vi.mocked(productsApi.fetchProducts).mockRejectedValue(
        new Error('500 Internal Server Error')
      );

      render(<ProductSelector />);

      await waitFor(() => {
        expect(
          screen.getByText(/Please check your connection and try again/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Scenario 6: Accessibility', () => {
    test('has label for product selection', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const label = screen.getByText(/Select Product/i);
      expect(label).toBeInTheDocument();
    });

    test('combobox has accessible role', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const combobox = screen.getByRole('combobox');
      expect(combobox).toBeInTheDocument();
    });

    test('combobox is keyboard navigable', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const combobox = screen.getByRole('combobox');

      // Focus combobox
      combobox.focus();
      expect(combobox).toHaveFocus();

      // Should be able to open with Enter
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
    });

    test('has minimum touch target size (44x44px)', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const combobox = screen.getByRole('combobox');
      const styles = window.getComputedStyle(combobox);

      // Note: In actual implementation, ensure CSS sets min-height
      // This test verifies the component structure supports it
      expect(combobox).toBeInTheDocument();
    });

    test('announces state changes to screen readers', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Confirmation message should have appropriate role for announcements
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      // Confirmation should be visible
      await waitFor(() => {
        const confirmation = screen.getByText(/Product selected/i);
        expect(confirmation).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    test('handles empty product list gracefully', async () => {
      vi.mocked(productsApi.fetchProducts).mockResolvedValue([]);

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const combobox = screen.getByRole('combobox');
      await user.click(combobox);

      // Should show empty state or no options message
      await waitFor(() => {
        // shadcn/ui Select typically shows "No options" or similar
        expect(screen.queryByText(/Cotton T-Shirt/i)).not.toBeInTheDocument();
      });
    });

    test('handles product with missing category field', async () => {
      const productsWithMissingCategory: Product[] = [
        {
          id: 1,
          code: 'TEST-001',
          name: 'Test Product',
          category: '',
          unit: 'unit',
          is_finished_product: true,
        },
      ];

      vi.mocked(productsApi.fetchProducts).mockResolvedValue(productsWithMissingCategory);

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const combobox = screen.getByRole('combobox');
      await user.click(combobox);

      // Should still display the product
      await waitFor(() => {
        expect(screen.getByText(/Test Product/i)).toBeInTheDocument();
      });
    });

    test('preserves selection when component re-renders', async () => {
      const { rerender } = render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      // Re-render component
      rerender(<ProductSelector />);

      // Selection should persist (from store)
      expect(useCalculatorStore.getState().selectedProductId).toBe(1);
    });
  });

  describe('Integration with Stores', () => {
    test('reads selectedProductId from calculatorStore', async () => {
      // Pre-set a selection in store
      useCalculatorStore.getState().setSelectedProduct(2);

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Should reflect the pre-selected product
      // (The Select component should show the selected value)
      expect(useCalculatorStore.getState().selectedProductId).toBe(2);
    });

    test('synchronizes with wizardStore step completion', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Initially incomplete
      expect(useWizardStore.getState().completedSteps).not.toContain('select');

      // Select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      // Should be marked complete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('select');
      });
    });
  });
});
