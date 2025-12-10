/**
 * ProductSelector BOM Loading Integration Tests
 *
 * Test-Driven Development for TASK-FE-019
 * Tests BOM loading functionality when product is selected
 *
 * Test Scenarios:
 * 1. Product selection triggers full product details fetch with BOM
 * 2. BOM data transformed and populated in calculator store
 * 3. Loading state management during BOM fetch
 * 4. Error handling for failed BOM fetch
 * 5. Emission factors loaded on mount
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import ProductSelector from '../../src/components/calculator/ProductSelector';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import * as productsApi from '../../src/services/api/products';
import * as emissionFactorsApi from '../../src/services/api/emissionFactors';
import type { Product } from '../../src/types/store.types';
import type { ProductDetail, EmissionFactorListItem } from '@/types/api.types';

// Mock products list data
const mockProductsList: Product[] = [
  {
    id: "1",
    code: 'TSHIRT-001',
    name: 'Cotton T-Shirt',
    category: 'Apparel',
    unit: 'unit',
    is_finished_product: true,
  },
  {
    id: "2",
    code: 'BOTTLE-001',
    name: 'Water Bottle',
    category: 'Consumer Goods',
    unit: 'unit',
    is_finished_product: true,
  },
];

// Mock product detail with BOM
const mockProductDetail: ProductDetail = {
  id: '1',
  code: 'TSHIRT-001',
  name: 'Cotton T-Shirt',
  description: 'A cotton t-shirt',
  unit: 'unit',
  category: 'Apparel',
  is_finished_product: true,
  bill_of_materials: [
    {
      id: 'bom_001',
      child_product_id: 'prod_cotton',
      child_product_name: 'Cotton',
      quantity: 0.18,
      unit: 'kg',
      notes: null,
    },
    {
      id: 'bom_002',
      child_product_id: 'prod_polyester',
      child_product_name: 'Polyester',
      quantity: 0.02,
      unit: 'kg',
      notes: 'Collar trim',
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
};

// Mock emission factors
const mockEmissionFactors: EmissionFactorListItem[] = [
  {
    id: '1',
    activity_name: 'Cotton',
    co2e_factor: 5.89,
    unit: 'kg CO2e/kg',
    data_source: 'Ecoinvent',
    geography: 'Global',
    reference_year: 2020,
    data_quality_rating: 4,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    activity_name: 'Polyester',
    co2e_factor: 3.36,
    unit: 'kg CO2e/kg',
    data_source: 'Ecoinvent',
    geography: 'Global',
    reference_year: 2020,
    data_quality_rating: 4,
    created_at: '2024-01-01T00:00:00Z',
  },
];

// Mock the APIs

const mockProducts = [
  { id: "1", name: 'Test Product', category: 'Electronics', code: 'TEST-001' },
];

vi.mock('../../src/services/api/products', () => ({
  productsAPI: {
    list: vi.fn(),
    getById: vi.fn(),
  },
  fetchProducts: vi.fn(),
}));

vi.mock('../../src/services/api/emissionFactors', () => ({
  emissionFactorsAPI: {
    list: vi.fn(),
  },
}));

describe('ProductSelector - BOM Loading Integration (TASK-FE-019)', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();

    // Reset mocks
    vi.clearAllMocks();

    // Default mock implementations
    vi.mocked(productsApi.fetchProducts).mockResolvedValue(mockProductsList);
    vi.mocked(productsApi.productsAPI.getById).mockResolvedValue(mockProductDetail);
    vi.mocked(emissionFactorsApi.emissionFactorsAPI.list).mockResolvedValue(mockEmissionFactors);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Scenario 1: Emission Factors Loading on Mount', () => {
    test('fetches emission factors when component mounts', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(emissionFactorsApi.emissionFactorsAPI.list).toHaveBeenCalledTimes(1);
      });
    });

    test('fetches emission factors with large limit to get all factors', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(emissionFactorsApi.emissionFactorsAPI.list).toHaveBeenCalledWith({
          limit: 1000,
        });
      });
    });

    test('handles emission factors fetch error gracefully (non-blocking)', async () => {
      // Mock emission factors error
      vi.mocked(emissionFactorsApi.emissionFactorsAPI.list).mockRejectedValue(
        new Error('Failed to load emission factors')
      );

      render(<ProductSelector />);

      // Should still render products dropdown
      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Products should load despite emission factors failure
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    test('shows loading skeleton while emission factors are being fetched', () => {
      // Mock delayed emission factors response
      vi.mocked(emissionFactorsApi.emissionFactorsAPI.list).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockEmissionFactors), 500))
      );

      render(<ProductSelector />);

      // Should show loading skeleton
      expect(screen.getByTestId('product-selector-skeleton')).toBeInTheDocument();
    });
  });

  describe('Scenario 2: Product Selection Triggers Full Product Fetch', () => {
    test('fetches full product details when product selected', async () => {
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

      // Should fetch product details with BOM
      await waitFor(() => {
        expect(productsApi.productsAPI.getById).toHaveBeenCalledWith('1');
      });
    });

    test('sets loading state while fetching product details', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Mock delayed product fetch
      vi.mocked(productsApi.productsAPI.getById).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockProductDetail), 200))
      );

      // Select product
      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      // isLoadingBOM should be set in store
      await waitFor(() => {
        expect(useCalculatorStore.getState().isLoadingBOM).toBe(true);
      });

      // After fetch completes, loading should be false
      await waitFor(() => {
        expect(useCalculatorStore.getState().isLoadingBOM).toBe(false);
      }, { timeout: 1000 });
    });

    test('stores full product details in calculator store', async () => {
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

      // Wait for fetch to complete
      await waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.selectedProduct).not.toBeNull();
        expect(state.selectedProduct?.name).toBe('Cotton T-Shirt');
        expect(state.selectedProduct?.code).toBe('TSHIRT-001');
      });
    });
  });

  describe('Scenario 3: BOM Data Transformation and Store Population', () => {
    test('transforms API BOM to frontend format and populates store', async () => {
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

      // Wait for BOM to be populated in store
      await waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.bomItems).toHaveLength(2);
      });

      const { bomItems } = useCalculatorStore.getState();

      // First BOM item - Cotton
      expect(bomItems[0]).toEqual({
        id: 'bom_001',
        name: 'Cotton',
        quantity: 0.18,
        unit: 'kg',
        category: 'material',
        emissionFactorId: "1", // Mapped to emission factor
        notes: undefined,
      });

      // Second BOM item - Polyester
      expect(bomItems[1]).toEqual({
        id: 'bom_002',
        name: 'Polyester',
        quantity: 0.02,
        unit: 'kg',
        category: 'material',
        emissionFactorId: "2",
        notes: 'Collar trim',
      });
    });

    test('handles case-insensitive emission factor matching', async () => {
      // Modify product BOM to have lowercase component names
      const productWithLowercaseComponents: ProductDetail = {
        ...mockProductDetail,
        bill_of_materials: [
          {
            id: 'bom_001',
            child_product_id: 'prod_cotton',
            child_product_name: 'cotton', // lowercase
            quantity: 0.18,
            unit: 'kg',
            notes: null,
          },
        ],
      };

      vi.mocked(productsApi.productsAPI.getById).mockResolvedValue(productWithLowercaseComponents);

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

      // Wait for BOM transformation
      await waitFor(() => {
        const { bomItems } = useCalculatorStore.getState();
        expect(bomItems).toHaveLength(1);
        expect(bomItems[0].emissionFactorId).toBe('1'); // Should match despite case difference
      });
    });

    test('handles missing emission factor gracefully (sets emissionFactorId to null)', async () => {
      // Product with component not in emission factors
      const productWithUnknownComponent: ProductDetail = {
        ...mockProductDetail,
        bill_of_materials: [
          {
            id: 'bom_003',
            child_product_id: 'prod_unknown',
            child_product_name: 'Unknown Material',
            quantity: 1.0,
            unit: 'kg',
            notes: null,
          },
        ],
      };

      vi.mocked(productsApi.productsAPI.getById).mockResolvedValue(productWithUnknownComponent);

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

      // Wait for BOM transformation
      await waitFor(() => {
        const { bomItems } = useCalculatorStore.getState();
        expect(bomItems).toHaveLength(1);
        expect(bomItems[0].emissionFactorId).toBeNull(); // No match found
        expect(bomItems[0].category).toBe('other'); // Default category
      });
    });

    test('handles empty BOM array', async () => {
      const productWithEmptyBOM: ProductDetail = {
        ...mockProductDetail,
        bill_of_materials: [],
      };

      vi.mocked(productsApi.productsAPI.getById).mockResolvedValue(productWithEmptyBOM);

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

      // BOM should be empty
      await waitFor(() => {
        const { bomItems } = useCalculatorStore.getState();
        expect(bomItems).toEqual([]);
      });
    });
  });

  describe('Scenario 4: Error Handling for BOM Fetch', () => {
    test('displays error when product details fetch fails', async () => {
      vi.mocked(productsApi.productsAPI.getById).mockRejectedValue(
        new Error('Product not found')
      );

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

      // Should show error
      await waitFor(() => {
        expect(screen.getByText(/Failed to load BOM/i)).toBeInTheDocument();
      });
    });

    test('sets loading state to false after fetch error', async () => {
      vi.mocked(productsApi.productsAPI.getById).mockRejectedValue(
        new Error('Network error')
      );

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

      // Loading should eventually be false
      await waitFor(() => {
        expect(useCalculatorStore.getState().isLoadingBOM).toBe(false);
      });
    });

    test('shows retry button when BOM fetch fails', async () => {
      vi.mocked(productsApi.productsAPI.getById).mockRejectedValue(
        new Error('Server error')
      );

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

      // Should show retry button in error alert
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    test('retry button refetches product details', async () => {
      // First call fails, second succeeds
      vi.mocked(productsApi.productsAPI.getById)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockProductDetail);

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

      // Wait for error
      await waitFor(() => {
        expect(screen.getByText(/Failed to load BOM/i)).toBeInTheDocument();
      });

      // Click retry
      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Should make another API call
      await waitFor(() => {
        expect(productsApi.productsAPI.getById).toHaveBeenCalledTimes(2);
      });

      // Should succeed and populate BOM
      await waitFor(() => {
        const { bomItems } = useCalculatorStore.getState();
        expect(bomItems).toHaveLength(2);
      });
    });
  });

  describe('Scenario 5: Integration with BOM Editor', () => {
    test('populated BOM items are ready for BOM Editor', async () => {
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

      // Wait for BOM population
      await waitFor(() => {
        const { bomItems } = useCalculatorStore.getState();
        expect(bomItems).toHaveLength(2);

        // Verify all fields are valid for BOM Editor
        bomItems.forEach(item => {
          expect(item.id).toBeDefined();
          expect(item.name).toBeDefined();
          expect(item.quantity).toBeGreaterThan(0);
          expect(item.unit).toBeDefined();
          expect(item.category).toBeDefined();
          // emissionFactorId can be null for unmatched items
          expect(typeof item.emissionFactorId === 'string' || item.emissionFactorId === null).toBe(true);
        });
      });
    });

    test('wizard step remains complete after BOM loads', async () => {
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

      // Verify step complete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('select');
      });

      // Wait for BOM to load
      await waitFor(() => {
        expect(useCalculatorStore.getState().bomItems).toHaveLength(2);
      });

      // Step should still be complete
      expect(useWizardStore.getState().completedSteps).toContain('select');
    });
  });

  describe('Edge Cases', () => {
    test('handles rapid product selection changes (debouncing)', async () => {
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

      // Quickly select second product
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Water Bottle/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Water Bottle/i));

      // Should complete both fetches (or cancel first)
      await waitFor(() => {
        expect(productsApi.productsAPI.getById).toHaveBeenCalled();
      });
    });

    test('handles null or undefined product ID gracefully', async () => {
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      // Set null product ID directly
      useCalculatorStore.getState().setSelectedProduct(null);

      // Should not trigger fetch
      expect(productsApi.productsAPI.getById).not.toHaveBeenCalled();
    });

    test('clears BOM when selecting product with empty BOM', async () => {
      // First select product with BOM
      render(<ProductSelector />);

      await waitFor(() => {
        expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
      });

      const selectTrigger = screen.getByRole('combobox');
      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Cotton T-Shirt/i));

      // Wait for BOM
      await waitFor(() => {
        expect(useCalculatorStore.getState().bomItems).toHaveLength(2);
      });

      // Now select product with empty BOM
      const emptyBOMProduct: ProductDetail = {
        ...mockProductDetail,
        id: '2',
        name: 'Water Bottle',
        bill_of_materials: [],
      };

      vi.mocked(productsApi.productsAPI.getById).mockResolvedValue(emptyBOMProduct);

      await user.click(selectTrigger);
      await waitFor(() => {
        expect(screen.getByText(/Water Bottle/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/Water Bottle/i));

      // BOM should be cleared
      await waitFor(() => {
        expect(useCalculatorStore.getState().bomItems).toEqual([]);
      });
    });
  });
});
