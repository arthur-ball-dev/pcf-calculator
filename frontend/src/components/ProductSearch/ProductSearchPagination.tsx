/**
 * ProductSearchPagination Component
 * TASK-FE-P5-004: Enhanced Product Search
 *
 * Pagination controls for product search results.
 * Supports "Load More" and traditional page navigation variants.
 */

import { Button } from '@/components/ui/button';

/**
 * Pagination variant type
 */
export type PaginationVariant = 'loadMore' | 'pages';

/**
 * Props for ProductSearchPagination component
 */
export interface ProductSearchPaginationProps {
  /** Current page index (0-based) */
  currentPage: number;
  /** Total number of pages */
  totalPages: number;
  /** Total count of items */
  totalCount: number;
  /** Whether more results exist */
  hasMore: boolean;
  /** Whether currently loading */
  isLoading: boolean;
  /** Number of items currently shown (for progress display) */
  itemsShown?: number;
  /** Callback when page changes */
  onPageChange: (page: number) => void;
  /** Callback when Load More is clicked */
  onLoadMore: () => void;
  /** Pagination variant (default: 'loadMore') */
  variant?: PaginationVariant;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Format large numbers with thousands separator
 */
function formatNumber(num: number): string {
  return num.toLocaleString();
}

/**
 * Get pluralized product text
 */
function getProductText(count: number): string {
  return count === 1 ? 'product' : 'products';
}

/**
 * Pagination component for product search
 *
 * @example
 * ```tsx
 * <ProductSearchPagination
 *   currentPage={page}
 *   totalPages={10}
 *   totalCount={200}
 *   hasMore={true}
 *   isLoading={false}
 *   itemsShown={20}
 *   onPageChange={setPage}
 *   onLoadMore={loadMore}
 * />
 * ```
 */
export function ProductSearchPagination({
  currentPage,
  totalPages,
  totalCount,
  hasMore,
  isLoading,
  itemsShown,
  onPageChange,
  onLoadMore,
  variant = 'loadMore',
  className,
}: ProductSearchPaginationProps) {
  // Render total count display
  const renderTotalCount = () => {
    const shown = itemsShown ?? Math.min((currentPage + 1) * 20, totalCount);
    const displayCount = Math.max(0, totalCount);

    if (itemsShown !== undefined) {
      return (
        <span data-testid="total-count">
          Showing {formatNumber(shown)} of {formatNumber(displayCount)} {getProductText(displayCount)}
        </span>
      );
    }

    return (
      <span data-testid="total-count">
        {formatNumber(displayCount)} {getProductText(displayCount)}
      </span>
    );
  };

  // Render Load More variant
  const renderLoadMore = () => {
    if (!hasMore) {
      return (
        <div className={`flex flex-col items-center gap-2 ${className || ''}`}>
          {renderTotalCount()}
        </div>
      );
    }

    return (
      <div className={`flex flex-col items-center gap-4 ${className || ''}`}>
        {renderTotalCount()}
        <Button
          variant="outline"
          onClick={onLoadMore}
          disabled={isLoading}
          data-testid="load-more-button"
        >
          {isLoading ? 'Loading...' : 'Load More'}
        </Button>
      </div>
    );
  };

  // Render Pages variant
  const renderPages = () => {
    if (totalPages <= 1) {
      return (
        <div className={`flex flex-col items-center gap-2 ${className || ''}`}>
          {renderTotalCount()}
        </div>
      );
    }

    // Generate page numbers to display
    const getPageNumbers = (): (number | 'ellipsis')[] => {
      const pages: (number | 'ellipsis')[] = [];
      const maxVisible = 7;

      if (totalPages <= maxVisible) {
        for (let i = 0; i < totalPages; i++) {
          pages.push(i);
        }
      } else {
        // Always show first page
        pages.push(0);

        if (currentPage > 2) {
          pages.push('ellipsis');
        }

        // Show pages around current
        const start = Math.max(1, currentPage - 1);
        const end = Math.min(totalPages - 2, currentPage + 1);

        for (let i = start; i <= end; i++) {
          pages.push(i);
        }

        if (currentPage < totalPages - 3) {
          pages.push('ellipsis');
        }

        // Always show last page
        pages.push(totalPages - 1);
      }

      return pages;
    };

    return (
      <div className={`flex flex-col items-center gap-4 ${className || ''}`}>
        {renderTotalCount()}
        <nav
          className="flex items-center gap-1"
          role="navigation"
          aria-label="Pagination"
          data-testid="pagination"
        >
          {/* Previous Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 0 || isLoading}
            aria-label="Previous page"
          >
            Previous
          </Button>

          {/* Page Numbers */}
          {getPageNumbers().map((page, index) => {
            if (page === 'ellipsis') {
              return (
                <span key={`ellipsis-${index}`} className="px-2">
                  ...
                </span>
              );
            }

            return (
              <Button
                key={page}
                variant={page === currentPage ? 'default' : 'outline'}
                size="sm"
                onClick={() => onPageChange(page)}
                disabled={isLoading}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page + 1}
              </Button>
            );
          })}

          {/* Next Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages - 1 || isLoading}
            aria-label="Next page"
          >
            Next
          </Button>
        </nav>
      </div>
    );
  };

  return variant === 'pages' ? renderPages() : renderLoadMore();
}

export default ProductSearchPagination;
