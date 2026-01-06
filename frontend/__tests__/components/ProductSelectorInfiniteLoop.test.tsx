/**
 * ProductSelector Infinite Loop Bug Tests
 * TASK-FE-P7-042: ProductSelector Infinite API Request Loop Bug
 *
 * These tests verify that the ProductSelector component does NOT make
 * infinite API calls when the dropdown opens. The bug is caused by two
 * competing useEffect hooks (lines 239-253) that both trigger on popover
 * open, creating a race condition.
 *
 * Bug Summary:
 * - Effect 1 (lines 239-243): Triggers on `open`, `debouncedSearch`, `showOnlyWithBom`
 * - Effect 2 (lines 248-253): Triggers on `open`, `products.length`, `isSearching`
 *
 * Race Condition:
 * 1. `open` becomes true -> both effects fire
 * 2. Both call searchProducts() -> isSearching = true
 * 3. First request completes -> setProducts(items), setIsSearching(false)
 * 4. Effect 2 re-runs (dependency isSearching changed)
 * 5. Condition `open && products.length === 0 && !isSearching` may be true
 * 6. Another search triggers -> infinite loop
 *
 * NOTE ON TESTING APPROACH:
 * The infinite loop bug manifests in production due to real async behavior
 * and React's state batching timing. In unit tests with mocked APIs, the
 * promises resolve synchronously which doesn't trigger the same race conditions.
 *
 * These tests serve as:
 * 1. REGRESSION TESTS - They document the expected behavior after the fix
 * 2. API CALL COUNT VERIFICATION - Ensure bounded, reasonable API calls
 * 3. UX VERIFICATION - Products display correctly, spinners disappear
 *
 * TDD Phase A: These tests define the acceptance criteria for the fix.
 * They verify that API call counts remain bounded and stable over time.
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, userEvent, act } from '../testUtils';
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

// Mock products data
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

describe('ProductSelector - Infinite Loop Bug Prevention (TASK-FE-P7-042)', () => {
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

  afterEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Test 1: Verify only limited API calls when dropdown opens
   *
   * EXPECTED BEHAVIOR: When user clicks the dropdown, at most 2 API calls should be made.
   * BUG BEHAVIOR: Multiple API calls are made due to competing useEffect hooks.
   *
   * ACCEPTANCE CRITERIA: searchCallCount <= 2
   */
  test('should make at most 2 API calls when dropdown opens (not infinite)', async () => {
    render(<ProductSelector />);

    // Wait for emission factors to load
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Clear previous calls from emission factors load
    vi.mocked(productsAPI.search).mockClear();

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Wait for products to load
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    // Small delay to allow any additional effect triggers
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 500));
    });

    // Verify bounded API calls
    const searchCallCount = vi.mocked(productsAPI.search).mock.calls.length;
    expect(searchCallCount).toBeLessThanOrEqual(2);
  });

  /**
   * Test 2: Verify API call count does not increase over time
   *
   * EXPECTED BEHAVIOR: After initial load, no additional calls happen automatically.
   * BUG BEHAVIOR: Continuous API calls every few milliseconds.
   *
   * ACCEPTANCE CRITERIA: callsAfterWait === callsAfterInitialLoad
   */
  test('should not make additional API calls after initial load settles', async () => {
    render(<ProductSelector />);

    // Wait for emission factors
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Wait for products to load
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    // Wait for state to settle
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 300));
    });

    // Record call count after initial load
    const callsAfterInitialLoad = vi.mocked(productsAPI.search).mock.calls.length;

    // Wait 1 second more - no new calls should happen
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    });

    const callsAfterWait = vi.mocked(productsAPI.search).mock.calls.length;

    // Verify no new calls during wait period
    expect(callsAfterWait).toBe(callsAfterInitialLoad);
  });

  /**
   * Test 3: Verify products are rendered after API returns (no infinite spinner)
   *
   * EXPECTED BEHAVIOR: Products appear in dropdown after API returns.
   * BUG BEHAVIOR: Spinner shows indefinitely because requests keep firing.
   *
   * ACCEPTANCE CRITERIA: Products visible, no "Searching..." spinner
   */
  test('should display products and hide loading spinner after API returns', async () => {
    render(<ProductSelector />);

    // Wait for emission factors
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Products should be visible within reasonable timeout
    await waitFor(
      () => {
        expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Wait for any spinners to clear
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 500));
    });

    // Spinner should NOT be visible after data loads
    const spinner = screen.queryByText(/Searching.../i);
    expect(spinner).not.toBeInTheDocument();
  });

  /**
   * Test 4: Verify BOM filter toggle triggers only one search
   *
   * EXPECTED BEHAVIOR: Toggling filter triggers ONE new search.
   * BUG BEHAVIOR: May trigger infinite loop due to state changes.
   *
   * ACCEPTANCE CRITERIA: callsAfterToggle <= 2
   */
  test('should make only one API call when BOM filter is toggled', async () => {
    render(<ProductSelector />);

    // Wait for emission factors
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Wait for initial products
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    // Wait for state to settle
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 300));
    });

    // Record call count before toggle
    vi.mocked(productsAPI.search).mockClear();

    // Toggle the BOM filter to "All Products"
    const allProductsButton = screen.getByTestId('bom-filter-all');
    await user.click(allProductsButton);

    // Wait for the search to complete
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    // Wait for any additional triggers
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 500));
    });

    // Verify bounded API calls after toggle
    const callsAfterToggle = vi.mocked(productsAPI.search).mock.calls.length;
    expect(callsAfterToggle).toBeLessThanOrEqual(2);
  });

  /**
   * Test 5: Verify debounced search triggers only after delay
   *
   * EXPECTED BEHAVIOR: Typing triggers ONE search after 300ms debounce.
   * BUG BEHAVIOR: May trigger multiple searches due to effect race condition.
   *
   * ACCEPTANCE CRITERIA: searchCallCount <= 2 after typing
   */
  test('should debounce search input and make limited API calls', async () => {
    render(<ProductSelector />);

    // Wait for emission factors
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Wait for initial products
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    // Wait for state to settle
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 300));
    });

    // Clear call count
    vi.mocked(productsAPI.search).mockClear();

    // Type in search input
    const searchInput = screen.getByTestId('product-search-input');
    await user.type(searchInput, 'cotton');

    // Wait for debounce (300ms) plus some buffer
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 600));
    });

    // Verify bounded API calls after typing
    const searchCallCount = vi.mocked(productsAPI.search).mock.calls.length;
    expect(searchCallCount).toBeLessThanOrEqual(2);
  });

  /**
   * Test 6: Verify call count stability over extended time
   *
   * This test specifically catches infinite loops by waiting
   * and checking that call count doesn't keep increasing.
   *
   * ACCEPTANCE CRITERIA: callsAt2Seconds === callsAt1Second
   */
  test('should maintain stable API call count over 2 seconds', async () => {
    render(<ProductSelector />);

    // Wait for emission factors
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Wait for products
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    // Wait 1 second
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    });

    const callsAt1Second = vi.mocked(productsAPI.search).mock.calls.length;

    // Wait another 1 second
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1000));
    });

    const callsAt2Seconds = vi.mocked(productsAPI.search).mock.calls.length;

    // Verify call count stability
    expect(callsAt2Seconds).toBe(callsAt1Second);
  });

  /**
   * Test 7: Verify total calls remain bounded
   *
   * EXPECTED BEHAVIOR: Total API calls should be < 5 after opening dropdown.
   * BUG BEHAVIOR: Many more calls due to infinite loop.
   *
   * ACCEPTANCE CRITERIA: totalCalls < 5
   */
  test('should have bounded total API calls (less than 5) when dropdown opens', async () => {
    render(<ProductSelector />);

    // Wait for emission factors
    await waitFor(() => {
      expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
    });

    // Clear all previous calls
    vi.mocked(productsAPI.search).mockClear();

    // Open popover
    const selectTrigger = screen.getByRole('combobox');
    await user.click(selectTrigger);

    // Wait for everything to settle
    await waitFor(() => {
      expect(screen.getByText(/Cotton T-Shirt/i)).toBeInTheDocument();
    });

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
    });

    const totalCalls = vi.mocked(productsAPI.search).mock.calls.length;

    // Verify total calls are bounded
    expect(totalCalls).toBeLessThan(5);
  });
});
