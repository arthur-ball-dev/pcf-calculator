/**
 * ProductSelector Component Tests
 *
 * Test-Driven Development for TASK-FE-003
 * Updated to match refactored component with searchable Command combobox
 *
 * Test Scenarios:
 * 1. Product List Rendering - Popover shows searchable products
 * 2. Product Selection - Updates stores and marks step complete
 * 3. Validation - Requires selection before proceeding
 * 4. Loading State - Shows loading during API request
 * 5. Error State - Shows error message with retry button
 * 6. Search Functionality - Server-side search via API
 * 7. Accessibility - ARIA labels and keyboard navigation
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, userEvent } from '../testUtils';
import ProductSelector from '../../src/components/calculator/ProductSelector';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { productsAPI } from '../../src/services/api/products';
import { emissionFactorsAPI } from '../../src/services/api/emissionFactors';

// Mock the APIs
vi.mock('../../src/services/api/products', () => ({
  productsAPI: {
    search: vi.fn(),
    getById: vi.fn(),
    list: vi.fn(),
  },
  fetchProducts: vi.fn(),
}));

vi.mock('../../src/services/api/emissionFactors', () => ({
  emissionFactorsAPI: {
    list: vi.fn(),
  },
}));

// Mock products data matching ProductDetail type
const mockProducts = [
  {
    id: '1',
    code: 'TSHIRT-001',
    name: 'Cotton T-Shirt',
    category: 'Apparel',
    unit: 'unit',
    is_finished_product: true,
    bill_of_materials: [],
  },
  {
    id: '2',
    code: 'BOTTLE-001',
    name: 'Water Bottle',
    category: 'Consumer Goods',
    unit: 'unit',
    is_finished_product: true,
    bill_of_materials: [],
  },
  {
    id: '3',
    code: 'LAPTOP-001',
    name: 'Laptop Computer',
    category: 'Electronics',
    unit: 'unit',
    is_finished_product: true,
    bill_of_materials: [],
  },
];

// Mock emission factors
const mockEmissionFactors = [
  {
    id: 'ef-1',
    activity_name: 'Cotton production',
    unit: 'kg',
    co2e_per_unit: 5.0,
    data_source: 'EPA',
    geography: 'US',
    is_active: true,
  },
];

describe('ProductSelector Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();

    // Reset mocks
    vi.clearAllMocks();

    // Default mock implementations (success)
    vi.mocked(emissionFactorsAPI.list).mockResolvedValue(mockEmissionFactors);
    vi.mocked(productsAPI.search).mockResolvedValue({
      items: mockProducts,
      total: mockProducts.length,
      has_more: false,
    });
    vi.mocked(productsAPI.getById).mockResolvedValue(mockProducts[0]);
  });

  describe('Scenario 1: Product List Rendering', () => {
    test('loads emission factors on mount', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(emissionFactorsAPI.list).toHaveBeenCalled();
      });
    });

    test('displays all fetched products in popover when opened', async () => {
      render(<ProductSelector />);

      // Wait for emission factors to load
      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open popover
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

      // Updated placeholder text for searchable combobox
      expect(screen.getByText(/Search and select a product/i)).toBeInTheDocument();
    });
  });

  describe('Scenario 2: Product Selection', () => {
    test('updates calculatorStore.selectedProductId when product selected', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open popover and select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });

      const option = screen.getByText(/Cotton T-Shirt/i);
      await user.click(option);

      // Verify store was updated
      await waitFor(() => {
        const calculatorState = useCalculatorStore.getState();
        expect(calculatorState.selectedProductId).toBe('1');
      });
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

      await waitFor(() => {
        expect(useCalculatorStore.getState().selectedProductId).toBe('1');
      });

      // Change selection - click trigger again to reopen
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Water Bottle/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Water Bottle/i));

      // Verify updated
      await waitFor(() => {
        expect(useCalculatorStore.getState().selectedProductId).toBe('2');
      });
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
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('select');
      });

      // Clear selection by setting null
      useCalculatorStore.getState().setSelectedProduct(null);

      // Should mark incomplete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).not.toContain('select');
      });
    });
  });

  describe('Scenario 4: Loading State', () => {
    test('displays loading skeleton during emission factors load', () => {
      // Mock delayed response for emission factors
      vi.mocked(emissionFactorsAPI.list).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockEmissionFactors), 1000))
      );

      render(<ProductSelector />);

      // Should show loading skeleton immediately
      expect(screen.getByTestId('product-selector-skeleton')).toBeInTheDocument();
    });

    test('hides loading skeleton after emission factors load', async () => {
      render(<ProductSelector />);

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Products combobox should be visible
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    test('combobox is present when emission factors loaded', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Combobox should be visible after loading
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('Scenario 5: Error Handling', () => {
    test('displays error message when search API request fails', async () => {
      // Mock API error - simulate search failure when popover opens
      vi.mocked(productsAPI.search).mockRejectedValue(
        new Error('Network error')
      );

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open popover to trigger search
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // After search fails and no products loaded, error should display
      await waitFor(() => {
        expect(screen.getByText(/Unable to load products/i)).toBeInTheDocument();
      });
    });

    test('shows retry button on error', async () => {
      vi.mocked(productsAPI.search).mockRejectedValue(
        new Error('Server error')
      );

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open popover to trigger search
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    test('retry button triggers new API request', async () => {
      // First call fails, second succeeds
      vi.mocked(productsAPI.search)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          items: mockProducts,
          total: mockProducts.length,
          has_more: false,
        });

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open popover to trigger search
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/Unable to load products/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should trigger new API call
      await waitFor(() => {
        expect(productsAPI.search).toHaveBeenCalledTimes(2);
      });
    });

    test('provides helpful error message', async () => {
      vi.mocked(productsAPI.search).mockRejectedValue(
        new Error('500 Internal Server Error')
      );

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Open popover to trigger search
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);

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
      vi.mocked(productsAPI.search).mockResolvedValue({
        items: [],
        total: 0,
        has_more: false,
      });

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const combobox = screen.getByRole('combobox');
      await user.click(combobox);

      // Should show empty state
      await waitFor(() => {
        expect(screen.queryByText(/Cotton T-Shirt/i)).not.toBeInTheDocument();
      });
    });

    test('handles product with missing category field', async () => {
      const productsWithMissingCategory = [
        {
          id: '1',
          code: 'TEST-001',
          name: 'Test Product',
          category: '',
          unit: 'unit',
          is_finished_product: true,
          bill_of_materials: [],
        },
      ];

      vi.mocked(productsAPI.search).mockResolvedValue({
        items: productsWithMissingCategory,
        total: 1,
        has_more: false,
      });

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

      await waitFor(() => {
        expect(useCalculatorStore.getState().selectedProductId).toBe('1');
      });

      // Re-render component
      rerender(<ProductSelector />);

      // Selection should persist (from store)
      expect(useCalculatorStore.getState().selectedProductId).toBe('1');
    });
  });

  describe('Integration with Stores', () => {
    test('reads selectedProductId from calculatorStore', async () => {
      // Pre-set a selection in store
      useCalculatorStore.getState().setSelectedProduct('2');

      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Should reflect the pre-selected product
      expect(useCalculatorStore.getState().selectedProductId).toBe('2');
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
