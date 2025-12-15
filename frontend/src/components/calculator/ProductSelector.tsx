/**
 * ProductSelector Component
 *
 * Allows users to search and select a product for PCF calculation.
 * Uses a searchable combobox with debounced API queries.
 *
 * Features:
 * - Searchable product list with debounced queries
 * - Server-side search (queries backend API)
 * - Loads full product details with BOM when product selected
 * - Transforms API BOM format to frontend format
 * - Populates calculator store with valid BOM items
 * - Loading skeleton during API request
 * - Error handling with retry functionality
 * - Integration with Zustand stores
 * - Accessibility-compliant (ARIA labels, keyboard navigation)
 *
 * Enhanced in Phase 7: Replaced simple Select with searchable Command combobox
 */

import React, { useEffect, useState, useCallback } from 'react';
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

  // Store access
  const { selectedProductId, setSelectedProduct, setLoadingBOM, setBomItems, setSelectedProductDetails } = useCalculatorStore();
  const { markStepComplete, markStepIncomplete } = useWizardStore();

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
   */
  const searchProducts = useCallback(async (query: string) => {
    setIsSearching(true);
    setError(null);

    try {
      // Use backend search API for server-side filtering
      const result = await productsAPI.search({
        query: query.trim() || undefined, // Only send query if not empty
        limit: 50,
        offset: 0,
        is_finished_product: true,
      });

      setProducts(result.items);
      setTotalProducts(result.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setIsSearching(false);
    }
  }, []);

  /**
   * Initial load and search effect
   */
  useEffect(() => {
    if (open) {
      searchProducts(debouncedSearch);
    }
  }, [open, debouncedSearch, searchProducts]);

  /**
   * Load initial products when popover opens
   */
  useEffect(() => {
    if (open && products.length === 0 && !isSearching) {
      setIsLoading(true);
      searchProducts('').finally(() => setIsLoading(false));
    }
  }, [open, products.length, isSearching, searchProducts]);

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
    searchProducts(debouncedSearch);
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
          <PopoverContent className="w-[400px] p-0 bg-white border shadow-lg" align="start">
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
                        : 'No products available'}
                    </CommandEmpty>
                    <CommandGroup heading={`Products (${totalProducts}${totalProducts >= 50 ? '+' : ''})`}>
                      {products.map((product) => (
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
                              {product.category && ` • ${product.category}`}
                            </span>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
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
            ✓ Product selected: <strong>{selectedProductName}</strong>. Click "Next" to edit the Bill of Materials.
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