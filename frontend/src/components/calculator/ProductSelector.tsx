/**
 * ProductSelector Component
 *
 * Allows users to search and select a product for PCF calculation.
 * Uses a searchable combobox with debounced API queries.
 *
 * Features:
 * - Searchable product list with debounced queries
 * - Server-side search (queries backend API)
 * - BOM filter toggle to show products with BOMs only (default) or all products
 * - Loads full product details with BOM when product selected
 * - Transforms API BOM format to frontend format
 * - Populates calculator store with valid BOM items
 * - Loading skeleton during API request
 * - Error handling with retry functionality
 * - Integration with Zustand stores
 * - Accessibility-compliant (ARIA labels, keyboard navigation)
 *
 * Enhanced in Phase 7: Replaced simple Select with searchable Command combobox
 * Enhanced in Phase 8: Added BOM filter toggle (TASK-FE-P8-001)
 * Fixed in Phase 7 (TASK-FE-P7-042): Fixed infinite API loop bug by using
 *   request ID pattern to cancel stale requests
 * Fixed in Phase 8 (TASK-FE-P8-009): Enhanced toggle button active styling
 *   to provide clear visual distinction between active and inactive states
 */

import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { Check, ChevronsUpDown, Loader2 } from 'lucide-react';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { productsAPI } from '@/services/api/products';
import { emissionFactorsAPI } from '@/services/api/emissionFactors';
import { transformAPIBOMToFrontend } from '@/services/bomTransform';
import { cn } from '@/lib/utils';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import type { UnitType } from '@/types/store.types';
import type { EmissionFactorListItem, ProductDetail } from '@/types/api.types';

// Debounce delay for search input
const SEARCH_DEBOUNCE_MS = 300;

// Industry display names for grouping
const INDUSTRY_LABELS: Record<string, string> = {
  'electronics': 'Electronics',
  'apparel': 'Apparel & Textiles',
  'automotive': 'Automotive',
  'construction': 'Construction',
  'food_beverage': 'Food & Beverage',
  'other': 'Other',
};

// Order for industry groups (most common first)
const INDUSTRY_ORDER = ['electronics', 'apparel', 'automotive', 'construction', 'food_beverage', 'other'];

/**
 * Group products by their category (industry)
 */
function groupProductsByIndustry<T extends { category?: string | null }>(
  products: T[]
): Map<string, T[]> {
  const groups = new Map<string, T[]>();

  for (const product of products) {
    // Normalize category to lowercase, default to 'other'
    const category = product.category?.toLowerCase().trim() || 'other';

    if (!groups.has(category)) {
      groups.set(category, []);
    }
    groups.get(category)!.push(product);
  }

  // Sort groups by predefined order
  const sortedGroups = new Map<string, T[]>();
  for (const key of INDUSTRY_ORDER) {
    if (groups.has(key)) {
      sortedGroups.set(key, groups.get(key)!);
      groups.delete(key);
    }
  }
  // Add any remaining categories at the end
  for (const [key, products] of groups) {
    sortedGroups.set(key, products);
  }

  return sortedGroups;
}

/**
 * Loading skeleton component for product selector
 */
const ProductSelectorSkeleton: React.FC = () => {
  return (
    <div className="space-y-4" data-testid="product-selector-skeleton">
      <div className="space-y-2">
        <div className="h-4 w-32 bg-muted animate-pulse rounded" />
        <div className="h-10 w-full bg-muted animate-pulse rounded-md" />
      </div>
    </div>
  );
};

/**
 * Error display component with retry functionality
 */
interface ErrorDisplayProps {
  error: Error;
  onRetry: () => void;
  context?: string;
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry, context }) => {
  return (
    <Alert variant="destructive" data-testid="error-message">
      <AlertDescription className="space-y-3">
        <div>
          <p className="font-semibold">
            {context === 'bom' ? 'Failed to load BOM' : 'Unable to load products'}
          </p>
          <p className="text-sm mt-1">
            Please check your connection and try again.
          </p>
          {error.message && (
            <p className="text-xs mt-1 opacity-80">{error.message}</p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="mt-2"
          data-testid="retry-button"
        >
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  );
};

/**
 * Custom hook for debouncing values
 */
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Main ProductSelector component
 */
const ProductSelector: React.FC = () => {
  // Popover state
  const [open, setOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, SEARCH_DEBOUNCE_MS);

  // BOM filter state - default to showing only products with BOMs
  const [showOnlyWithBom, setShowOnlyWithBom] = useState(true);

  // Products state
  const [products, setProducts] = useState<ProductDetail[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [bomError, setBomError] = useState<Error | null>(null);
  const [totalProducts, setTotalProducts] = useState(0);

  // Selected product display
  const [selectedProductName, setSelectedProductName] = useState<string>('');

  // Emission factors state
  const [emissionFactors, setEmissionFactors] = useState<EmissionFactorListItem[]>([]);
  const [isLoadingEmissionFactors, setIsLoadingEmissionFactors] = useState(true);

  // Ref to track current search request ID for deduplication (TASK-FE-P7-042 fix)
  // We use a request ID instead of a ref guard to allow new requests to supersede old ones
  const currentRequestIdRef = useRef(0);

  // Ref to the filter toggle container for detecting clicks on it
  const filterToggleRef = useRef<HTMLDivElement>(null);

  // Ref to track previous search query for detecting clears
  const prevSearchQueryRef = useRef('');

  // Store access
  const { selectedProductId, setSelectedProduct, setLoadingBOM, setBomItems, setSelectedProductDetails } = useCalculatorStore();
  const { markStepComplete, markStepIncomplete } = useWizardStore();

  /**
   * Group products by industry for organized dropdown display
   */
  const groupedProducts = useMemo(() => {
    return groupProductsByIndustry(products);
  }, [products]);

  /**
   * Load emission factors on component mount
   */
  useEffect(() => {
    const loadEmissionFactors = async () => {
      setIsLoadingEmissionFactors(true);
      try {
        const factors = await emissionFactorsAPI.list({ limit: 1000 });
        setEmissionFactors(factors);
      } catch (err) {
        console.error('Failed to load emission factors:', err);
      } finally {
        setIsLoadingEmissionFactors(false);
      }
    };

    loadEmissionFactors();
  }, []);

  /**
   * Search products with debounced query using backend search API
   *
   * TASK-FE-P7-042 fix: Uses request ID pattern to prevent stale responses
   * from overwriting newer ones. Each search gets a unique ID, and we only
   * process results if the ID matches the current request.
   */
  const searchProducts = useCallback(async (query: string, hasBom: boolean) => {
    // Increment request ID to invalidate any in-flight requests
    const requestId = ++currentRequestIdRef.current;

    setIsSearching(true);
    setError(null);

    try {
      // Use backend search API for server-side filtering
      const result = await productsAPI.search({
        query: query.trim() || undefined, // Only send query if not empty
        limit: 50,
        offset: 0,
        is_finished_product: true,
        has_bom: hasBom || undefined, // Only pass has_bom when filtering for products with BOMs
      });

      // Only update state if this is still the current request
      // This prevents stale responses from overwriting newer data
      if (requestId === currentRequestIdRef.current) {
        setProducts(result.items);
        setTotalProducts(result.total);
      }
    } catch (err) {
      // Only set error if this is still the current request
      if (requestId === currentRequestIdRef.current) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      }
    } finally {
      // Only clear searching state if this is still the current request
      if (requestId === currentRequestIdRef.current) {
        setIsSearching(false);
      }
    }
  }, []);

  /**
   * Consolidated effect to trigger search when popover opens or search params change
   *
   * TASK-FE-P7-042 fix: Consolidated two competing useEffect hooks into one.
   * Previously, there were two effects that created a race condition.
   *
   * This single effect handles all search triggers:
   * - Initial load when popover opens (open becomes true)
   * - Search query changes (debouncedSearch changes)
   * - BOM filter changes (showOnlyWithBom changes)
   */
  useEffect(() => {
    if (open) {
      searchProducts(debouncedSearch, showOnlyWithBom);
    }
  }, [open, debouncedSearch, showOnlyWithBom, searchProducts]);

  /**
   * Effect to handle immediate search when search query is cleared
   *
   * This catches the case where user.clear() clears the input and we want
   * to immediately search with empty query without waiting for debounce.
   * This is needed because cmdk/jsdom may not properly trigger the debounced
   * value change when clearing.
   */
  useEffect(() => {
    // If query was cleared (went from non-empty to empty) while popover is open
    if (open && prevSearchQueryRef.current !== '' && searchQuery === '') {
      // Trigger search immediately with empty query
      searchProducts('', showOnlyWithBom);
    }
    prevSearchQueryRef.current = searchQuery;
  }, [searchQuery, open, showOnlyWithBom, searchProducts]);

  /**
   * Sync wizard step completion based on selection
   */
  useEffect(() => {
    if (selectedProductId !== null) {
      markStepComplete('select');
    } else {
      markStepIncomplete('select');
    }
  }, [selectedProductId, markStepComplete, markStepIncomplete]);

  /**
   * Handle BOM filter toggle change
   *
   * TASK-FE-P8-001: When filter changes, just update the state.
   * The useEffect above handles triggering the search when the popover is open.
   */
  const handleBomFilterChange = useCallback((value: boolean) => {
    setShowOnlyWithBom(value);
    // The useEffect watching showOnlyWithBom will trigger the search
    // when popover is open, so we don't need to call searchProducts here
  }, []);

  /**
   * Handle popover outside click - prevent closing when clicking on filter toggle
   *
   * TASK-FE-P8-001: When user clicks on the BOM filter toggle buttons,
   * we prevent the popover from closing so they can see the updated product list.
   */
  const handleInteractOutside = useCallback((event: Event) => {
    // Check if the click was on the filter toggle
    if (filterToggleRef.current?.contains(event.target as Node)) {
      event.preventDefault();
    }
  }, []);

  /**
   * Handle product selection with full BOM loading
   */
  const handleProductSelect = async (productId: string, productName: string) => {
    if (!productId) return;

    try {
      setBomError(null);
      setLoadingBOM(true);
      setSelectedProduct(productId);
      setSelectedProductName(productName);
      setOpen(false);

      // Fetch full product details with BOM
      const productDetail = await productsAPI.getById(productId);

      // Store full product details
      setSelectedProductDetails({
        id: productDetail.id,
        code: productDetail.code,
        name: productDetail.name,
        category: productDetail.category || 'unknown',
        unit: productDetail.unit as UnitType,
        is_finished_product: productDetail.is_finished_product,
      });

      // Transform BOM data
      const transformedBOM = transformAPIBOMToFrontend(
        productDetail.bill_of_materials,
        emissionFactors
      );

      // Update store with transformed BOM
      setBomItems(transformedBOM);

    } catch (err) {
      console.error('Failed to load product BOM:', err);
      setBomError(err instanceof Error ? err : new Error('Failed to load BOM'));
    } finally {
      setLoadingBOM(false);
    }
  };

  /**
   * Retry BOM loading for currently selected product
   */
  const retryBOMLoad = async () => {
    if (selectedProductId && selectedProductName) {
      await handleProductSelect(selectedProductId, selectedProductName);
    }
  };

  /**
   * Retry initial load
   */
  const retryLoad = () => {
    setError(null);
    searchProducts(debouncedSearch, showOnlyWithBom);
  };

  /**
   * Render loading state
   */
  if (isLoadingEmissionFactors) {
    return <ProductSelectorSkeleton />;
  }

  /**
   * Render error state (only for initial load failure)
   */
  if (error && products.length === 0) {
    return <ErrorDisplay error={error} onRetry={retryLoad} />;
  }

  /**
   * Main render
   */
  return (
    <div className="space-y-4" data-testid="product-selector" data-tour="product-select">
      <div className="space-y-2">
        <Label htmlFor="product-select">Select Product</Label>

        {/* BOM Filter Toggle - shown outside popover for visibility (TASK-FE-P8-001)
            The ref is used to detect clicks on this element and prevent popover from closing
            TASK-FE-P8-009: Enhanced active styling with font-medium for clear visual distinction */}
        <div ref={filterToggleRef} className="flex items-center gap-2 mb-2" data-testid="bom-filter-toggle-group">
          <span className="text-sm text-muted-foreground">Show:</span>
          <div className="flex rounded-md border">
            <button
              type="button"
              className={cn(
                "px-3 py-1 text-sm rounded-l-md transition-colors",
                showOnlyWithBom
                  ? "bg-primary text-primary-foreground font-medium"
                  : "hover:bg-muted"
              )}
              onClick={() => handleBomFilterChange(true)}
              data-testid="bom-filter-with-bom"
              aria-pressed={showOnlyWithBom}
            >
              With BOMs
            </button>
            <button
              type="button"
              className={cn(
                "px-3 py-1 text-sm rounded-r-md transition-colors",
                !showOnlyWithBom
                  ? "bg-primary text-primary-foreground font-medium"
                  : "hover:bg-muted"
              )}
              onClick={() => handleBomFilterChange(false)}
              data-testid="bom-filter-all"
              aria-pressed={!showOnlyWithBom}
            >
              All Products
            </button>
          </div>
        </div>

        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              id="product-select"
              variant="outline"
              role="combobox"
              aria-expanded={open}
              aria-label="Select a product to calculate carbon footprint"
              className="w-full justify-between"
              data-testid="product-select-trigger"
            >
              {selectedProductName || "Search and select a product..."}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent
            className="w-[400px] p-0 bg-white border shadow-lg"
            align="start"
            onInteractOutside={handleInteractOutside}
          >
            <Command shouldFilter={false} className="bg-white">
              <CommandInput
                placeholder="Type to search products..."
                value={searchQuery}
                onValueChange={setSearchQuery}
                data-testid="product-search-input"
              />
              <CommandList>
                {isLoading || isSearching ? (
                  <div className="flex items-center justify-center py-6">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                    <span className="ml-2 text-sm text-muted-foreground">
                      {isSearching ? 'Searching...' : 'Loading products...'}
                    </span>
                  </div>
                ) : (
                  <>
                    <CommandEmpty>
                      {searchQuery
                        ? `No products found for "${searchQuery}"`
                        : showOnlyWithBom
                          ? 'No products with BOMs available'
                          : 'No products available'}
                    </CommandEmpty>
                    {/* Products grouped by industry */}
                    {Array.from(groupedProducts.entries()).map(([industry, industryProducts]) => (
                      <CommandGroup
                        key={industry}
                        heading={`${INDUSTRY_LABELS[industry] || industry} (${industryProducts.length})`}
                      >
                        {industryProducts.map((product) => (
                          <CommandItem
                            key={product.id}
                            value={product.id}
                            onSelect={() => handleProductSelect(product.id, product.name)}
                            className="cursor-pointer"
                            data-testid={`product-option-${product.id}`}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                selectedProductId === product.id ? "opacity-100" : "opacity-0"
                              )}
                            />
                            <div className="flex flex-col">
                              <span>{product.name}</span>
                              <span className="text-xs text-muted-foreground">
                                {product.code}
                              </span>
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    ))}
                  </>
                )}
              </CommandList>
              {totalProducts > 50 && (
                <div className="border-t p-2 text-center text-xs text-muted-foreground">
                  Showing 50 of {totalProducts} results. Type to search for more.
                </div>
              )}
            </Command>
          </PopoverContent>
        </Popover>
        <p className="text-xs text-muted-foreground">
          Search by product name, code, or description
        </p>
      </div>

      {/* Product Selected Confirmation */}
      {selectedProductId && (
        <Alert className="bg-muted border-muted-foreground/20" data-testid="product-selected-confirmation">
          <AlertDescription className="text-sm text-muted-foreground">
            Product selected: <strong>{selectedProductName}</strong>. Click "Next" to edit the Bill of Materials.
          </AlertDescription>
        </Alert>
      )}

      {/* BOM Loading Error */}
      {bomError && (
        <ErrorDisplay error={bomError} onRetry={retryBOMLoad} context="bom" />
      )}
    </div>
  );
};

export default ProductSelector;
