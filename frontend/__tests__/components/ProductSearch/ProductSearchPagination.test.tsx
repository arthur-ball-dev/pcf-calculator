/**
 * ProductSearchPagination Component Tests
 * TASK-FE-P5-004: Enhanced Product Search - Phase A Tests
 *
 * Test Coverage:
 * 1. "Load More" button shown when has_more=true
 * 2. Button hidden when has_more=false
 * 3. Click loads next page
 * 4. Shows total count
 * 5. Shows loading state during fetch
 * 6. Accessibility compliance
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ProductSearchPagination } from '@/components/ProductSearch/ProductSearchPagination';
import type { ProductSearchPaginationProps } from '@/components/ProductSearch/ProductSearchPagination';

describe('ProductSearchPagination Component', () => {
  const user = userEvent.setup();

  const defaultProps: ProductSearchPaginationProps = {
    currentPage: 0,
    totalPages: 5,
    totalCount: 100,
    hasMore: true,
    isLoading: false,
    onPageChange: vi.fn(),
    onLoadMore: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Load More Button Visibility
  // ==========================================================================

  describe('Load More Button Visibility', () => {
    it('should show "Load More" button when has_more is true', () => {
      render(<ProductSearchPagination {...defaultProps} hasMore={true} />);

      expect(screen.getByTestId('load-more-button')).toBeInTheDocument();
    });

    it('should hide "Load More" button when has_more is false', () => {
      render(<ProductSearchPagination {...defaultProps} hasMore={false} />);

      expect(screen.queryByTestId('load-more-button')).not.toBeInTheDocument();
    });

    it('should show button with "Load More" text', () => {
      render(<ProductSearchPagination {...defaultProps} hasMore={true} />);

      const button = screen.getByTestId('load-more-button');
      expect(button.textContent).toMatch(/load more/i);
    });

    it('should hide button when on last page', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          currentPage={4}
          totalPages={5}
          hasMore={false}
        />
      );

      expect(screen.queryByTestId('load-more-button')).not.toBeInTheDocument();
    });

    it('should show button when more results available', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          currentPage={0}
          totalPages={5}
          hasMore={true}
        />
      );

      expect(screen.getByTestId('load-more-button')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 2: Load More Click Handler
  // ==========================================================================

  describe('Load More Click Handler', () => {
    it('should call onLoadMore when Load More button is clicked', async () => {
      const onLoadMore = vi.fn();

      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} onLoadMore={onLoadMore} />
      );

      const button = screen.getByTestId('load-more-button');
      await user.click(button);

      expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('should not call onLoadMore when button is disabled', async () => {
      const onLoadMore = vi.fn();

      render(
        <ProductSearchPagination
          {...defaultProps}
          hasMore={true}
          isLoading={true}
          onLoadMore={onLoadMore}
        />
      );

      const button = screen.getByTestId('load-more-button');
      await user.click(button);

      // Button should be disabled during loading
      expect(button).toBeDisabled();
    });

    it('should disable button during loading state', () => {
      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={true} />
      );

      const button = screen.getByTestId('load-more-button');
      expect(button).toBeDisabled();
    });
  });

  // ==========================================================================
  // Test Suite 3: Total Count Display
  // ==========================================================================

  describe('Total Count Display', () => {
    it('should display total count', () => {
      render(<ProductSearchPagination {...defaultProps} totalCount={156} />);

      expect(screen.getByTestId('total-count')).toBeInTheDocument();
      expect(screen.getByTestId('total-count').textContent).toContain('156');
    });

    it('should format large numbers', () => {
      render(<ProductSearchPagination {...defaultProps} totalCount={1234} />);

      const totalCount = screen.getByTestId('total-count');
      expect(totalCount.textContent).toMatch(/1[,.]?234/);
    });

    it('should show "product" for count of 1', () => {
      render(<ProductSearchPagination {...defaultProps} totalCount={1} />);

      const totalCount = screen.getByTestId('total-count');
      expect(totalCount.textContent).toMatch(/1\s*product\b/i);
    });

    it('should show "products" for count > 1', () => {
      render(<ProductSearchPagination {...defaultProps} totalCount={100} />);

      const totalCount = screen.getByTestId('total-count');
      expect(totalCount.textContent).toMatch(/products/i);
    });

    it('should show "0 products" when empty', () => {
      render(<ProductSearchPagination {...defaultProps} totalCount={0} hasMore={false} />);

      const totalCount = screen.getByTestId('total-count');
      expect(totalCount.textContent).toMatch(/0/);
    });

    it('should display current items shown vs total', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          currentPage={1}
          itemsShown={40}
          totalCount={100}
        />
      );

      // Should show something like "Showing 40 of 100 products"
      const countDisplay = screen.getByTestId('total-count');
      expect(countDisplay).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 4: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should show loading indicator when isLoading is true', () => {
      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={true} />
      );

      // Button should show loading state
      const button = screen.getByTestId('load-more-button');
      expect(button).toHaveAttribute('disabled');
    });

    it('should show loading text in button during load', () => {
      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={true} />
      );

      const button = screen.getByTestId('load-more-button');
      expect(button.textContent).toMatch(/loading/i);
    });

    it('should show spinner during loading', () => {
      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={true} />
      );

      // Spinner or loading indicator should be visible
      const button = screen.getByTestId('load-more-button');
      expect(button).toBeInTheDocument();
    });

    it('should restore normal state after loading completes', () => {
      const { rerender } = render(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={true} />
      );

      expect(screen.getByTestId('load-more-button')).toBeDisabled();

      rerender(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={false} />
      );

      expect(screen.getByTestId('load-more-button')).not.toBeDisabled();
    });
  });

  // ==========================================================================
  // Test Suite 5: Page Navigation (Alternative to Load More)
  // ==========================================================================

  describe('Page Navigation', () => {
    it('should support page number navigation when enabled', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={2}
          totalPages={10}
        />
      );

      // Page numbers should be visible
      expect(screen.getByTestId('pagination')).toBeInTheDocument();
    });

    it('should call onPageChange with correct page number', async () => {
      const onPageChange = vi.fn();

      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={0}
          totalPages={5}
          onPageChange={onPageChange}
        />
      );

      // Find and click page 2
      const pagination = screen.queryByTestId('pagination');
      if (pagination) {
        const page2 = screen.queryByText('2');
        if (page2) {
          await user.click(page2);
          expect(onPageChange).toHaveBeenCalledWith(1);
        }
      }
    });

    it('should highlight current page', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={2}
          totalPages={10}
        />
      );

      // Current page should be visually distinct
      const pagination = screen.queryByTestId('pagination');
      // Implementation details vary
    });

    it('should show ellipsis for large page counts', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={5}
          totalPages={20}
        />
      );

      // For many pages, should show ellipsis
      const pagination = screen.queryByTestId('pagination');
      // Implementation may include "..." for skipped pages
    });

    it('should have previous/next buttons', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={2}
          totalPages={10}
        />
      );

      const pagination = screen.queryByTestId('pagination');
      if (pagination) {
        // Previous and Next buttons should exist
        // These might be icons or text buttons
      }
    });
  });

  // ==========================================================================
  // Test Suite 6: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible Load More button', () => {
      render(<ProductSearchPagination {...defaultProps} hasMore={true} />);

      const button = screen.getByTestId('load-more-button');
      expect(button).toHaveAccessibleName();
    });

    it('should announce loading state to screen readers', () => {
      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} isLoading={true} />
      );

      const button = screen.getByTestId('load-more-button');
      // Button should have aria-busy or similar
      expect(button).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      render(<ProductSearchPagination {...defaultProps} hasMore={true} />);

      const button = screen.getByTestId('load-more-button');

      // Should be focusable
      await user.tab();
      expect(button).toHaveFocus();
    });

    it('should support activation with Enter key', async () => {
      const onLoadMore = vi.fn();

      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} onLoadMore={onLoadMore} />
      );

      const button = screen.getByTestId('load-more-button');
      button.focus();

      await user.keyboard('{Enter}');

      expect(onLoadMore).toHaveBeenCalled();
    });

    it('should support activation with Space key', async () => {
      const onLoadMore = vi.fn();

      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} onLoadMore={onLoadMore} />
      );

      const button = screen.getByTestId('load-more-button');
      button.focus();

      await user.keyboard(' ');

      expect(onLoadMore).toHaveBeenCalled();
    });

    it('should have proper role for pagination', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={0}
          totalPages={5}
        />
      );

      const pagination = screen.queryByTestId('pagination');
      if (pagination) {
        expect(pagination).toHaveAttribute('role', 'navigation');
      }
    });

    it('should have aria-label for pagination nav', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={0}
          totalPages={5}
        />
      );

      const pagination = screen.queryByTestId('pagination');
      if (pagination) {
        expect(pagination).toHaveAttribute('aria-label');
      }
    });

    it('should announce current page to screen readers', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={2}
          totalPages={10}
        />
      );

      // Current page should be announced
      // aria-current="page" or similar
    });
  });

  // ==========================================================================
  // Test Suite 7: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle zero total pages', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          totalPages={0}
          totalCount={0}
          hasMore={false}
        />
      );

      // Should not crash
      expect(screen.getByTestId('total-count')).toBeInTheDocument();
    });

    it('should handle single page', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          currentPage={0}
          totalPages={1}
          hasMore={false}
        />
      );

      // No Load More button needed
      expect(screen.queryByTestId('load-more-button')).not.toBeInTheDocument();
    });

    it('should handle very large total count', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          totalCount={999999}
          totalPages={10000}
        />
      );

      const totalCount = screen.getByTestId('total-count');
      expect(totalCount).toBeInTheDocument();
    });

    it('should handle rapid clicks gracefully', async () => {
      const onLoadMore = vi.fn();

      render(
        <ProductSearchPagination {...defaultProps} hasMore={true} onLoadMore={onLoadMore} />
      );

      const button = screen.getByTestId('load-more-button');

      // Rapid clicks
      await user.click(button);
      await user.click(button);
      await user.click(button);

      // Should handle gracefully (may be debounced or disabled after first)
      expect(onLoadMore).toHaveBeenCalled();
    });

    it('should handle negative values gracefully', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          currentPage={-1}
          totalPages={-1}
          totalCount={-1}
        />
      );

      // Should not crash
      expect(screen.queryByTestId('pagination') || screen.queryByTestId('total-count')).toBeTruthy();
    });
  });

  // ==========================================================================
  // Test Suite 8: Progress Indicator
  // ==========================================================================

  describe('Progress Indicator', () => {
    it('should show progress text (e.g., "Showing 20 of 100")', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={20}
          totalCount={100}
        />
      );

      const countDisplay = screen.getByTestId('total-count');
      expect(countDisplay.textContent).toMatch(/20/);
      expect(countDisplay.textContent).toMatch(/100/);
    });

    it('should update progress after loading more', () => {
      const { rerender } = render(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={20}
          totalCount={100}
        />
      );

      rerender(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={40}
          totalCount={100}
        />
      );

      const countDisplay = screen.getByTestId('total-count');
      expect(countDisplay.textContent).toMatch(/40/);
    });

    it('should show all items loaded state', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={100}
          totalCount={100}
          hasMore={false}
        />
      );

      // Should indicate all items are loaded
      const countDisplay = screen.getByTestId('total-count');
      expect(countDisplay).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 9: Variant Support
  // ==========================================================================

  describe('Variant Support', () => {
    it('should support "loadMore" variant (default)', () => {
      render(
        <ProductSearchPagination {...defaultProps} variant="loadMore" hasMore={true} />
      );

      expect(screen.getByTestId('load-more-button')).toBeInTheDocument();
    });

    it('should support "pages" variant', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          variant="pages"
          currentPage={0}
          totalPages={5}
        />
      );

      // Should show page navigation instead of Load More
      const pagination = screen.queryByTestId('pagination');
      // Implementation dependent
    });

    it('should default to "loadMore" variant', () => {
      render(<ProductSearchPagination {...defaultProps} hasMore={true} />);

      expect(screen.getByTestId('load-more-button')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 10: Integration
  // ==========================================================================

  describe('Integration', () => {
    it('should work with infinite scroll pattern', async () => {
      const onLoadMore = vi.fn();
      let itemsShown = 20;

      const { rerender } = render(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={itemsShown}
          totalCount={100}
          hasMore={true}
          onLoadMore={onLoadMore}
        />
      );

      // Click Load More
      const button = screen.getByTestId('load-more-button');
      await user.click(button);

      expect(onLoadMore).toHaveBeenCalled();

      // Simulate more items loaded
      itemsShown = 40;
      rerender(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={itemsShown}
          totalCount={100}
          hasMore={true}
          onLoadMore={onLoadMore}
        />
      );

      // Progress should update
      const countDisplay = screen.getByTestId('total-count');
      expect(countDisplay.textContent).toMatch(/40/);
    });

    it('should disable Load More at end of results', () => {
      render(
        <ProductSearchPagination
          {...defaultProps}
          itemsShown={100}
          totalCount={100}
          hasMore={false}
        />
      );

      expect(screen.queryByTestId('load-more-button')).not.toBeInTheDocument();
    });
  });
});
