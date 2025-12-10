/**
 * ProductSearch Component
 * TASK-FE-P5-004: Enhanced Product Search
 *
 * Main search component integrating:
 * - Search input with debouncing (300ms)
 * - Filter popover with industry/category/manufacturer filters
 * - Results display with loading skeletons
 * - Pagination with Load More
 */

import React, { useState, useCallback } from 'react';
import { MagnifyingGlassIcon, Cross2Icon } from '@radix-ui/react-icons';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useDebounce } from '@/hooks/useDebounce';
import { useProductSearch, type Product } from '@/hooks/useProductSearch';
import { ProductSearchResults } from './ProductSearchResults';
import { ProductSearchFilters } from './ProductSearchFilters';
import { ProductSearchPagination } from './ProductSearchPagination';

/**
 * Page size for search results
 */
const PAGE_SIZE = 20;

/**
 * Props for ProductSearch component
 */
export interface ProductSearchProps {
  /** Callback when a product is selected */
  onProductSelect?: (product: Product) => void;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Main product search component
 *
 * @example
 * ```tsx
 * <ProductSearch
 *   onProductSelect={(product) => {
 *     console.log('Selected:', product.name);
 *   }}
 * />
 * ```
 */
export function ProductSearch({ onProductSelect, className }: ProductSearchProps) {
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedManufacturer, setSelectedManufacturer] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [allItems, setAllItems] = useState<Product[]>([]);

  // Debounce search query
  const debouncedQuery = useDebounce(searchQuery, 300);

  // Fetch products
  const { data, isLoading, isFetching, error } = useProductSearch({
    query: debouncedQuery || undefined,
    industry: selectedIndustry || undefined,
    categoryId: selectedCategory || undefined,
    manufacturer: selectedManufacturer || undefined,
    limit: PAGE_SIZE,
    offset: currentPage * PAGE_SIZE,
  });

  // Update accumulated items when data changes
  React.useEffect(() => {
    if (data?.items) {
      if (currentPage === 0) {
        // Reset items on new search
        setAllItems(data.items);
      } else {
        // Append items for Load More
        setAllItems((prev) => [...prev, ...data.items]);
      }
    }
  }, [data, currentPage]);

  // Count active filters
  const activeFilterCount = [selectedIndustry, selectedCategory, selectedManufacturer].filter(
    Boolean
  ).length;

  // Clear all filters
  const clearFilters = useCallback(() => {
    setSelectedIndustry(null);
    setSelectedCategory(null);
    setSelectedManufacturer(null);
    setCurrentPage(0);
    setAllItems([]);
  }, []);

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(0);
    setAllItems([]);
  };

  // Handle clear search
  const handleClearSearch = () => {
    setSearchQuery('');
    setCurrentPage(0);
    setAllItems([]);
  };

  // Handle filter changes
  const handleIndustryChange = (industry: string | null) => {
    setSelectedIndustry(industry);
    setCurrentPage(0);
    setAllItems([]);
  };

  const handleCategoryChange = (category: string | null) => {
    setSelectedCategory(category);
    setCurrentPage(0);
    setAllItems([]);
  };

  const handleManufacturerChange = (manufacturer: string | null) => {
    setSelectedManufacturer(manufacturer);
    setCurrentPage(0);
    setAllItems([]);
  };

  // Handle Load More
  const handleLoadMore = () => {
    setCurrentPage((prev) => prev + 1);
  };

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    setAllItems([]);
  };

  // Calculate total pages
  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  // Items to display
  const displayItems = currentPage === 0 ? (data?.items || []) : allItems;

  return (
    <div className={`space-y-4 ${className || ''}`} data-testid="product-search">
      {/* Search Header */}
      <div className="flex gap-2">
        {/* Search Input */}
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search products by name, code, or description..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="pl-10 pr-10"
            data-testid="search-input"
            aria-label="Search products"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              data-testid="clear-search"
              aria-label="Clear search"
            >
              <Cross2Icon className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Filter Popover */}
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" className="gap-2" data-testid="filter-button">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
              Filters
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80">
            <ProductSearchFilters
              selectedIndustry={selectedIndustry}
              selectedCategory={selectedCategory}
              selectedManufacturer={selectedManufacturer}
              onIndustryChange={handleIndustryChange}
              onCategoryChange={handleCategoryChange}
              onManufacturerChange={handleManufacturerChange}
              onClearFilters={clearFilters}
              showManufacturerFilter={false}
            />
          </PopoverContent>
        </Popover>
      </div>

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        {data && (
          <>
            <span data-testid="results-count">
              {data.total} product{data.total !== 1 ? 's' : ''} found
              {debouncedQuery && ` for "${debouncedQuery}"`}
            </span>
            {isFetching && !isLoading && (
              <span className="text-blue-500">Updating...</span>
            )}
          </>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          data-testid="loading-skeletons"
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="p-4 border rounded-lg">
              <Skeleton className="h-6 w-3/4 mb-2" />
              <Skeleton className="h-4 w-1/2 mb-4" />
              <Skeleton className="h-4 w-full" />
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-8 text-red-500" data-testid="error-message">
          Failed to load products. Please try again.
        </div>
      )}

      {/* Results Grid */}
      {data && !isLoading && (
        <>
          {data.items.length > 0 || displayItems.length > 0 ? (
            <>
              <ProductSearchResults
                products={currentPage === 0 ? data.items : displayItems}
                onProductClick={onProductSelect}
              />

              {/* Pagination */}
              {(data.has_more || totalPages > 1) && (
                <div className="flex justify-center mt-6" data-testid="pagination">
                  <ProductSearchPagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    totalCount={data.total}
                    hasMore={data.has_more}
                    isLoading={isFetching}
                    itemsShown={displayItems.length}
                    onPageChange={handlePageChange}
                    onLoadMore={handleLoadMore}
                  />
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12" data-testid="no-results">
              <p className="text-gray-500 mb-2">No products found</p>
              {debouncedQuery && (
                <p className="text-sm text-gray-400">
                  Try adjusting your search or filters
                </p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default ProductSearch;
