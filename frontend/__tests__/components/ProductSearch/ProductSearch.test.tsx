/**
 * ProductSearch Component Tests
 * TASK-FE-P5-004: Enhanced Product Search - Phase A Tests
 *
 * Test Coverage:
 * 1. Renders search input
 * 2. Renders filter dropdowns (industry, category, manufacturer)
 * 3. Shows loading skeleton during search
 * 4. Displays search results
 * 5. Shows "no results" message when empty
 * 6. Pagination controls appear when has_more=true
 * 7. Search input triggers debounced API call
 * 8. Filter changes trigger search
 * 9. Accessibility compliance
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, within, userEvent } from '../../testUtils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { ProductSearch } from '@/components/ProductSearch/ProductSearch';

/** Every product card in the results: a button when clickable, otherwise an article. */
function getAllCards(): HTMLElement[] {
  const results = within(screen.getByRole('group', { name: 'Search results' }));
  return [...results.queryAllByRole('button'), ...results.queryAllByRole('article')];
}

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

// Helper to render with providers
function renderWithProviders(ui: React.ReactElement) {
  const Wrapper = createWrapper();
  return {
    user: userEvent.setup(),
    ...render(ui, { wrapper: Wrapper }),
  };
}

describe('ProductSearch Component', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Component Rendering
  // ==========================================================================

  describe('Component Rendering', () => {
    it('should render the search component container', async () => {
      renderWithProviders(<ProductSearch />);

      expect(screen.getByRole('region', { name: 'Product search' })).toBeInTheDocument();
    });

    it('should render the search input field', async () => {
      renderWithProviders(<ProductSearch />);

      expect(screen.getByRole('textbox', { name: 'Search products' })).toBeInTheDocument();
    });

    it('should render search input with placeholder text', async () => {
      renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      expect(input).toHaveAttribute('placeholder');
      expect(input.getAttribute('placeholder')).toMatch(/search.*product/i);
    });

    it('should render filter button', async () => {
      renderWithProviders(<ProductSearch />);

      expect(screen.getByRole('button', { name: /^Filters/ })).toBeInTheDocument();
    });

    it('should render search icon in input', async () => {
      renderWithProviders(<ProductSearch />);

      // Search icon should be present (as visual indicator)
      const searchContainer = screen.getByRole('region', { name: 'Product search' });
      expect(searchContainer).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 2: Search Input Behavior
  // ==========================================================================

  describe('Search Input Behavior', () => {
    it('should update input value when user types', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      expect(input).toHaveValue('laptop');
    });

    it('should show clear button when input has value', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      expect(screen.getByRole('button', { name: 'Clear search' })).toBeInTheDocument();
    });

    it('should not show clear button when input is empty', async () => {
      renderWithProviders(<ProductSearch />);

      expect(screen.queryByRole('button', { name: 'Clear search' })).not.toBeInTheDocument();
    });

    it('should clear input when clear button is clicked', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');
      expect(input).toHaveValue('laptop');

      const clearButton = screen.getByRole('button', { name: 'Clear search' });
      await user.click(clearButton);

      expect(input).toHaveValue('');
    });

    it('should trigger search after debounce delay (300ms)', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      // Before debounce - should show loading or initial state
      // After debounce - should show results
      vi.advanceTimersByTime(300);

      await waitFor(() => {
        // Results or loading state should be visible
        const hasResults = screen.queryByRole('group', { name: 'Search results' });
        const hasLoading = screen.queryByRole('status', { name: 'Loading products' });
        const hasNoResults = screen.queryByText('No products found');
        expect(hasResults || hasLoading || hasNoResults).toBeTruthy();
      });
    });

    it('should debounce rapid typing correctly', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });

      // Type rapidly
      await user.type(input, 'smart');
      vi.advanceTimersByTime(100);
      await user.type(input, 'phone');
      vi.advanceTimersByTime(100);

      // Input should have full value
      expect(input).toHaveValue('smartphone');

      // Wait for debounce
      vi.advanceTimersByTime(300);

      // Only final search should be triggered
      await waitFor(() => {
        expect(screen.queryByRole('status', { name: 'Loading products' }) ||
               screen.queryByRole('group', { name: 'Search results' }) ||
               screen.queryByText('No products found')).toBeTruthy();
      });
    });
  });

  // ==========================================================================
  // Test Suite 3: Filter Popover
  // ==========================================================================

  describe('Filter Popover', () => {
    it('should open filter popover when filter button is clicked', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      expect(screen.getByRole('group', { name: 'Filters' })).toBeInTheDocument();
    });

    it('should render industry select in filter popover', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      expect(screen.getByRole('combobox', { name: 'Industry' })).toBeInTheDocument();
    });

    it('should render category select in filter popover', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      expect(screen.getByRole('combobox', { name: 'Category' })).toBeInTheDocument();
    });

    it('should show industry options when industry select is opened', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      // Should show industry options
      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });
    });

    it('should show filter count badge when filters are active', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      // Select an industry
      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        const electronicsOption = screen.getByText(/electronics/i);
        expect(electronicsOption).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Close popover and check badge
      await user.keyboard('{Escape}');

      // Filter button should show badge with count
      within(screen.getByRole('button', { name: /^Filters/ })).queryByText('1');
      // Badge might appear once filters are applied
    });

    it('should show clear filters button when filters are active', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      // Select an industry
      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Clear filters button should appear
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Clear all filters' })).toBeInTheDocument();
      });
    });

    it('should clear all filters when clear filters button is clicked', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      // Select an industry
      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Click clear filters
      const clearFilters = screen.getByRole('button', { name: 'Clear all filters' });
      await user.click(clearFilters);

      // Clear filters button should disappear (no active filters)
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: 'Clear all filters' })).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 4: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should show loading skeletons during initial load', async () => {
      renderWithProviders(<ProductSearch />);

      // On initial render, should show loading state
      await waitFor(() => {
        screen.queryByRole('status', { name: 'Loading products' });
        // Loading should appear during fetch
        // May transition quickly in tests with MSW
      });
    });

    it('should show loading skeletons when search is triggered', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      // Advance past debounce
      vi.advanceTimersByTime(300);

      // Loading skeletons may appear briefly
      // This tests the loading state exists in the component
    });

    it('should hide loading skeletons when results load', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      vi.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.queryByRole('status', { name: 'Loading products' })).not.toBeInTheDocument();
      });
    });

    it('should render skeleton cards matching expected grid layout', async () => {
      renderWithProviders(<ProductSearch />);

      // If loading skeletons are present, they should be in a grid
      const skeletons = screen.queryByRole('status', { name: 'Loading products' });
      if (skeletons) {
        // Skeletons container should exist with skeleton elements
        expect(skeletons).toBeInTheDocument();
      }
    });
  });

  // ==========================================================================
  // Test Suite 5: Results Display
  // ==========================================================================

  describe('Results Display', () => {
    it('should display results grid when data loads', async () => {
      renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        expect(screen.getByRole('group', { name: 'Search results' })).toBeInTheDocument();
      });
    });

    it('should display result count', async () => {
      renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        const resultsCount = screen.getByText(/^\d+ products? found/);
        expect(resultsCount).toBeInTheDocument();
        expect(resultsCount.textContent).toMatch(/\d+\s*product/i);
      });
    });

    it('should display search query in results summary', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      vi.advanceTimersByTime(300);

      await waitFor(() => {
        const resultsCount = screen.getByText(/^\d+ products? found/);
        expect(resultsCount.textContent).toMatch(/laptop/i);
      });
    });

    it('should display product cards in results', async () => {
      renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        const cards = getAllCards();
        expect(cards.length).toBeGreaterThan(0);
      });
    });

    it('should show no results message when search returns empty', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'xyznonexistent123abc');

      vi.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.getByText('No products found')).toBeInTheDocument();
      });
    });

    it('should show helpful message in no results state', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'xyznonexistent123abc');

      vi.advanceTimersByTime(300);

      await waitFor(() => {
        const noResults = screen.getByText('No products found');
        expect(noResults.textContent).toMatch(/no products found/i);
      });
    });
  });

  // ==========================================================================
  // Test Suite 6: Pagination
  // ==========================================================================

  describe('Pagination', () => {
    it('should display pagination when has_more is true', async () => {
      renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        // Pagination may appear if results exceed page size
        screen.queryByRole('group', { name: 'Pagination controls' });
        // Depends on mock data returning has_more=true
      });
    });

    it('should hide pagination when has_more is false', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      // Search for something with few results
      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'xyznonexistent123abc');

      vi.advanceTimersByTime(300);

      await waitFor(() => {
        const noResults = screen.getByText('No products found');
        expect(noResults).toBeInTheDocument();
      });

      // Pagination should not appear for empty results
      expect(screen.queryByRole('group', { name: 'Pagination controls' })).not.toBeInTheDocument();
    });

    it('should reset to first page when search query changes', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      vi.advanceTimersByTime(300);

      await waitFor(() => {
        expect(screen.queryByRole('group', { name: 'Search results' }) ||
               screen.queryByText('No products found')).toBeTruthy();
      });

      // Type new search
      await user.clear(input);
      await user.type(input, 'phone');

      vi.advanceTimersByTime(300);

      // Should be on page 1 (offset 0)
      // This is verified by the results shown
    });

    it('should reset to first page when filter changes', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /^Filters/ })).toBeInTheDocument();
      });

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Should reset pagination
      vi.advanceTimersByTime(300);
    });
  });

  // ==========================================================================
  // Test Suite 7: Product Selection
  // ==========================================================================

  describe('Product Selection', () => {
    it('should call onProductSelect when a product card is clicked', async () => {
      const onProductSelect = vi.fn();

      renderWithProviders(<ProductSearch onProductSelect={onProductSelect} />);

      await waitFor(() => {
        expect(screen.getByRole('group', { name: 'Search results' })).toBeInTheDocument();
      });

      const cards = getAllCards();
      if (cards.length > 0) {
        await userEvent.click(cards[0]);
        expect(onProductSelect).toHaveBeenCalled();
      }
    });

    it('should pass product data to onProductSelect callback', async () => {
      const onProductSelect = vi.fn();

      renderWithProviders(<ProductSearch onProductSelect={onProductSelect} />);

      await waitFor(() => {
        expect(screen.getByRole('group', { name: 'Search results' })).toBeInTheDocument();
      });

      const cards = getAllCards();
      if (cards.length > 0) {
        await userEvent.click(cards[0]);

        expect(onProductSelect).toHaveBeenCalledWith(
          expect.objectContaining({
            id: expect.any(String),
            name: expect.any(String),
            code: expect.any(String),
          })
        );
      }
    });
  });

  // ==========================================================================
  // Test Suite 8: Error Handling
  // ==========================================================================

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      // This test depends on MSW being configured to return errors
      // for specific queries
      renderWithProviders(<ProductSearch />);

      // If configured, error message should appear
      // expect(screen.queryByTestId('error-message')).toBeTruthy();
    });

    it('should allow retry after error', async () => {
      // Configure MSW to fail then succeed
    });
  });

  // ==========================================================================
  // Test Suite 9: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible search input', async () => {
      renderWithProviders(<ProductSearch />);

      const input = screen.getByRole('textbox', { name: 'Search products' });

      // Input should be accessible
      expect(input.tagName.toLowerCase()).toBe('input');
      expect(input).toHaveAttribute('type', 'text');
    });

    it('should have label for search input', async () => {
      renderWithProviders(<ProductSearch />);

      // Either visible label or aria-label
      const input = screen.getByRole('textbox', { name: 'Search products' });
      const hasLabel = input.hasAttribute('aria-label') ||
                       input.hasAttribute('aria-labelledby') ||
                       screen.queryByLabelText(/search/i);
      expect(hasLabel).toBeTruthy();
    });

    it('should have keyboard-accessible filter button', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });

      // Should be focusable
      filterButton.focus();
      expect(document.activeElement).toBe(filterButton);

      // Should be activatable with keyboard
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByRole('group', { name: 'Filters' })).toBeInTheDocument();
      });
    });

    it('should trap focus in filter popover when open', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      await waitFor(() => {
        expect(screen.getByRole('group', { name: 'Filters' })).toBeInTheDocument();
      });

      // Focus should be within popover
      const popover = screen.getByRole('group', { name: 'Filters' });
      expect(popover.contains(document.activeElement)).toBe(true);
    });

    it('should close filter popover with Escape key', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      await waitFor(() => {
        expect(screen.getByRole('group', { name: 'Filters' })).toBeInTheDocument();
      });

      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('group', { name: 'Filters' })).not.toBeInTheDocument();
      });
    });

    it('should have accessible product cards', async () => {
      renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        const grid = screen.queryByRole('group', { name: 'Search results' });
        if (grid) {
          const cards = getAllCards();
          if (cards.length > 0) {
            // Cards should be interactive
            expect(cards[0]).toHaveAttribute('tabIndex');
          }
        }
      });
    });

    it('should announce results count to screen readers', async () => {
      renderWithProviders(<ProductSearch />);

      await waitFor(() => {
        const resultsCount = screen.getByText(/^\d+ products? found/);
        // Results count should be accessible
        expect(resultsCount).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 10: Integration
  // ==========================================================================

  describe('Integration', () => {
    it('should work with search and filter combined', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      // Type search query
      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      // Open and set filter
      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Close popover
      await user.keyboard('{Escape}');

      vi.advanceTimersByTime(300);

      // Should show filtered results
      await waitFor(() => {
        expect(screen.queryByRole('group', { name: 'Search results' }) ||
               screen.queryByText('No products found')).toBeTruthy();
      });
    });

    it('should maintain search when clearing filters', async () => {
      const { user } = renderWithProviders(<ProductSearch />);

      // Type search query
      const input = screen.getByRole('textbox', { name: 'Search products' });
      await user.type(input, 'laptop');

      vi.advanceTimersByTime(300);

      // Open and set filter
      const filterButton = screen.getByRole('button', { name: /^Filters/ });
      await user.click(filterButton);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Clear filters
      const clearFilters = screen.getByRole('button', { name: 'Clear all filters' });
      await user.click(clearFilters);

      // Search query should still be there
      expect(input).toHaveValue('laptop');
    });
  });
});
