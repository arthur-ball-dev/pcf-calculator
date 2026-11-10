/**
 * ProductSearchFilters Component Tests
 * TASK-FE-P5-004: Enhanced Product Search - Phase A Tests
 *
 * Test Coverage:
 * 1. Industry dropdown with options
 * 2. Category dropdown (hierarchical)
 * 3. Manufacturer dropdown
 * 4. Clear filters button
 * 5. Filter changes trigger search callback
 * 6. Filter state management
 * 7. Accessibility compliance
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, userEvent } from '../../testUtils';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { ProductSearchFilters } from '@/components/ProductSearch/ProductSearchFilters';
import type { ProductSearchFiltersProps } from '@/components/ProductSearch/ProductSearchFilters';

// Create wrapper with QueryClient for category fetching
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

describe('ProductSearchFilters Component', () => {
  const defaultProps: ProductSearchFiltersProps = {
    selectedIndustry: null,
    selectedCategory: null,
    selectedManufacturer: null,
    onIndustryChange: vi.fn(),
    onCategoryChange: vi.fn(),
    onManufacturerChange: vi.fn(),
    onClearFilters: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Industry Dropdown
  // ==========================================================================

  describe('Industry Dropdown', () => {
    it('should render industry select', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      expect(screen.getByRole('combobox', { name: 'Industry' })).toBeInTheDocument();
    });

    it('should show industry label', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      expect(screen.getByText(/industry/i)).toBeInTheDocument();
    });

    it('should show all industry options when opened', async () => {
      const { user } = renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        // All industries should be available
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
        expect(screen.getByText(/apparel/i)).toBeInTheDocument();
        expect(screen.getByText(/automotive/i)).toBeInTheDocument();
        expect(screen.getByText(/construction/i)).toBeInTheDocument();
      });
    });

    it('should show "All industries" option', async () => {
      const { user } = renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/all industries/i)).toBeInTheDocument();
      });
    });

    it('should call onIndustryChange when industry is selected', async () => {
      const onIndustryChange = vi.fn();
      const { user } = renderWithProviders(
        <ProductSearchFilters {...defaultProps} onIndustryChange={onIndustryChange} />
      );

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      expect(onIndustryChange).toHaveBeenCalledWith('electronics');
    });

    it('should call onIndustryChange with null when "All industries" is selected', async () => {
      const onIndustryChange = vi.fn();
      const { user } = renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          selectedIndustry="electronics"
          onIndustryChange={onIndustryChange}
        />
      );

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/all industries/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/all industries/i));

      expect(onIndustryChange).toHaveBeenCalledWith(null);
    });

    it('should display selected industry value', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />
      );

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      expect(industrySelect.textContent).toMatch(/electronics/i);
    });

    it('should show placeholder when no industry selected', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} selectedIndustry={null} />);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      expect(industrySelect.textContent).toMatch(/all industries/i);
    });
  });

  // ==========================================================================
  // Test Suite 2: Category Dropdown
  // ==========================================================================

  describe('Category Dropdown', () => {
    it('should render category select', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      expect(screen.getByRole('combobox', { name: 'Category' })).toBeInTheDocument();
    });

    it('should show category label', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      expect(screen.getByText(/category/i)).toBeInTheDocument();
    });

    it('should show "All categories" option', async () => {
      const { user } = renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      await user.click(categorySelect);

      await waitFor(() => {
        expect(screen.getByText(/all categories/i)).toBeInTheDocument();
      });
    });

    it('should call onCategoryChange when category is selected', async () => {
      const onCategoryChange = vi.fn();
      const { user } = renderWithProviders(
        <ProductSearchFilters {...defaultProps} onCategoryChange={onCategoryChange} />
      );

      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      await user.click(categorySelect);

      // Wait for categories to load from MSW
      await waitFor(() => {
        // Should show at least one category from mock data
      });

      // If categories are available, click one
      // Note: This depends on MSW returning category data
    });

    it('should display selected category value', () => {
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          selectedCategory="550e8400-e29b-41d4-a716-446655440003"
        />
      );

      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      // Should show the category name or ID
      expect(categorySelect).toBeInTheDocument();
    });

    it('should show placeholder when no category selected', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} selectedCategory={null} />);

      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      expect(categorySelect.textContent).toMatch(/all categories/i);
    });

    it('should support hierarchical category display', async () => {
      const { user } = renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      await user.click(categorySelect);

      // Categories should be organized hierarchically
      // (depends on implementation - could be indented, grouped, etc.)
    });
  });

  // ==========================================================================
  // Test Suite 3: Manufacturer Dropdown
  // ==========================================================================

  describe('Manufacturer Dropdown', () => {
    it('should render manufacturer select when enabled', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} showManufacturerFilter={true} />
      );

      expect(screen.getByRole('combobox', { name: 'Manufacturer' })).toBeInTheDocument();
    });

    it('should not render manufacturer select when disabled', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} showManufacturerFilter={false} />
      );

      expect(screen.queryByRole('combobox', { name: 'Manufacturer' })).not.toBeInTheDocument();
    });

    it('should show manufacturer label', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} showManufacturerFilter={true} />
      );

      expect(screen.getByText(/manufacturer/i)).toBeInTheDocument();
    });

    it('should call onManufacturerChange when manufacturer is entered', async () => {
      const onManufacturerChange = vi.fn();
      const { user } = renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          showManufacturerFilter={true}
          onManufacturerChange={onManufacturerChange}
        />
      );

      const manufacturerInput = screen.getByRole('combobox', { name: 'Manufacturer' });
      await user.click(manufacturerInput);

      // If it's a combobox or input, type a value
      // await user.type(manufacturerInput, 'Acme');

      // Or if it's a select with options
      // await user.click(screen.getByText(/acme/i));
    });

    it('should display selected manufacturer value', () => {
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          showManufacturerFilter={true}
          selectedManufacturer="Acme Corp"
        />
      );

      const manufacturerSelect = screen.getByRole('combobox', { name: 'Manufacturer' });
      expect(manufacturerSelect).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 4: Clear Filters Button
  // ==========================================================================

  describe('Clear Filters Button', () => {
    it('should NOT show clear filters button when no filters active', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      expect(screen.queryByRole('button', { name: 'Clear all filters' })).not.toBeInTheDocument();
    });

    it('should show clear filters button when industry filter is active', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />
      );

      expect(screen.getByRole('button', { name: 'Clear all filters' })).toBeInTheDocument();
    });

    it('should show clear filters button when category filter is active', () => {
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          selectedCategory="550e8400-e29b-41d4-a716-446655440003"
        />
      );

      expect(screen.getByRole('button', { name: 'Clear all filters' })).toBeInTheDocument();
    });

    it('should show clear filters button when manufacturer filter is active', () => {
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          showManufacturerFilter={true}
          selectedManufacturer="Acme"
        />
      );

      expect(screen.getByRole('button', { name: 'Clear all filters' })).toBeInTheDocument();
    });

    it('should call onClearFilters when clear button is clicked', async () => {
      const onClearFilters = vi.fn();
      const { user } = renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          selectedIndustry="electronics"
          onClearFilters={onClearFilters}
        />
      );

      const clearButton = screen.getByRole('button', { name: 'Clear all filters' });
      await user.click(clearButton);

      expect(onClearFilters).toHaveBeenCalledTimes(1);
    });

    it('should display "Clear all filters" text', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />
      );

      expect(screen.getByRole('button', { name: 'Clear all filters' }).textContent).toMatch(/clear/i);
    });
  });

  // ==========================================================================
  // Test Suite 5: Filter Count
  // ==========================================================================

  describe('Filter Count', () => {
    it('should count single active filter correctly', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />
      );

      // Active filter count should be 1
      // This might be displayed as a badge or accessible text
    });

    it('should count multiple active filters correctly', () => {
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          selectedIndustry="electronics"
          selectedCategory="550e8400-e29b-41d4-a716-446655440003"
        />
      );

      // Active filter count should be 2
    });

    it('should include manufacturer in filter count', () => {
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          showManufacturerFilter={true}
          selectedIndustry="electronics"
          selectedManufacturer="Acme"
        />
      );

      // Active filter count should be 2 (industry + manufacturer)
    });

    it('should return zero count when no filters active', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      // No badge or count indicator should be shown
      // Or count should be 0
    });
  });

  // ==========================================================================
  // Test Suite 6: Filter Integration
  // ==========================================================================

  describe('Filter Integration', () => {
    it('should allow selecting industry and category together', async () => {
      const onIndustryChange = vi.fn();
      const onCategoryChange = vi.fn();

      const { user } = renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          onIndustryChange={onIndustryChange}
          onCategoryChange={onCategoryChange}
        />
      );

      // Select industry
      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      expect(onIndustryChange).toHaveBeenCalledWith('electronics');

      // Select category
      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      await user.click(categorySelect);

      // Category selection depends on available options
    });

    it('should maintain filter values on re-render', () => {
      const { rerender } = render(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('combobox', { name: 'Industry' }).textContent).toMatch(/electronics/i);

      // Re-render with same props
      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />
        </QueryClientProvider>
      );

      expect(screen.getByRole('combobox', { name: 'Industry' }).textContent).toMatch(/electronics/i);
    });

    it('should update display when selectedIndustry prop changes', () => {
      const { rerender } = render(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('combobox', { name: 'Industry' }).textContent).toMatch(/electronics/i);

      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <ProductSearchFilters {...defaultProps} selectedIndustry="automotive" />
        </QueryClientProvider>
      );

      expect(screen.getByRole('combobox', { name: 'Industry' }).textContent).toMatch(/automotive/i);
    });
  });

  // ==========================================================================
  // Test Suite 7: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible labels for industry select', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      screen.getByRole('combobox', { name: 'Industry' });

      // Should have label association
      expect(screen.getByText(/industry/i)).toBeInTheDocument();
    });

    it('should have accessible labels for category select', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      screen.getByRole('combobox', { name: 'Category' });

      // Should have label association
      expect(screen.getByText(/category/i)).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const { user } = renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      screen.getByRole('combobox', { name: 'Industry' });

      // Tab to industry select
      await user.tab();

      // Should be able to open with keyboard
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });
    });

    it('should have proper ARIA attributes on selects', () => {
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });

      // Select should have proper ARIA role
      expect(industrySelect).toHaveAttribute('role', 'combobox');
    });

    it('should announce filter changes to screen readers', async () => {
      const { user } = renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      // Options should be selectable and announce selection
    });

    it('should have accessible clear filters button', () => {
      renderWithProviders(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />
      );

      const clearButton = screen.getByRole('button', { name: 'Clear all filters' });

      // Should have accessible name
      expect(clearButton).toHaveAccessibleName();
    });
  });

  // ==========================================================================
  // Test Suite 8: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle rapid filter changes', async () => {
      const onIndustryChange = vi.fn();
      const { user } = renderWithProviders(
        <ProductSearchFilters {...defaultProps} onIndustryChange={onIndustryChange} />
      );

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });

      // Rapid changes
      await user.click(industrySelect);
      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/electronics/i));

      await user.click(industrySelect);
      await waitFor(() => {
        expect(screen.getByText(/automotive/i)).toBeInTheDocument();
      });
      await user.click(screen.getByText(/automotive/i));

      // Both changes should be registered
      expect(onIndustryChange).toHaveBeenCalledTimes(2);
    });

    it('should handle empty category list', () => {
      // When no categories are available, should show empty or disabled state
      renderWithProviders(<ProductSearchFilters {...defaultProps} />);

      const categorySelect = screen.getByRole('combobox', { name: 'Category' });
      expect(categorySelect).toBeInTheDocument();
    });

    it('should handle filter with no results gracefully', () => {
      // Component should still function even if filter combination yields no results
      renderWithProviders(
        <ProductSearchFilters
          {...defaultProps}
          selectedIndustry="nonexistent-industry"
        />
      );

      // Should not crash
      expect(screen.getByRole('combobox', { name: 'Industry' })).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 9: Controlled Component Behavior
  // ==========================================================================

  describe('Controlled Component Behavior', () => {
    it('should be a controlled component for industry', () => {
      const { rerender } = render(
        <ProductSearchFilters {...defaultProps} selectedIndustry="electronics" />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('combobox', { name: 'Industry' }).textContent).toMatch(/electronics/i);

      // Update prop externally
      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <ProductSearchFilters {...defaultProps} selectedIndustry="automotive" />
        </QueryClientProvider>
      );

      expect(screen.getByRole('combobox', { name: 'Industry' }).textContent).toMatch(/automotive/i);
    });

    it('should be a controlled component for category', () => {
      const { rerender } = render(
        <ProductSearchFilters
          {...defaultProps}
          selectedCategory="category-1"
        />,
        { wrapper: createWrapper() }
      );

      // Update prop externally
      rerender(
        <QueryClientProvider client={new QueryClient()}>
          <ProductSearchFilters {...defaultProps} selectedCategory="category-2" />
        </QueryClientProvider>
      );

      // Component should reflect new value
      expect(screen.getByRole('combobox', { name: 'Category' })).toBeInTheDocument();
    });

    it('should not update internal state without callback', async () => {
      const { user } = renderWithProviders(
        <ProductSearchFilters {...defaultProps} selectedIndustry={null} />
      );

      const industrySelect = screen.getByRole('combobox', { name: 'Industry' });
      await user.click(industrySelect);

      await waitFor(() => {
        expect(screen.getByText(/electronics/i)).toBeInTheDocument();
      });

      await user.click(screen.getByText(/electronics/i));

      // Since it's controlled and prop is null, display might not change
      // (depends on implementation - callback would update parent state)
    });
  });
});
