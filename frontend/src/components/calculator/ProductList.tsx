/**
 * ProductList Component
 *
 * Full-page scrollable product list for the "Select Product" wizard step.
 * Replaces the ProductSelector combobox dropdown with a richer, Emerald Night
 * themed product browsing experience.
 *
 * Features:
 * - Search card with debounced server-side search
 * - BOM toggle switch filter (default: products with BOMs only)
 * - Industry filter pills (dynamically computed from available products)
 * - Grouped product rows by industry with headers
 * - Each row shows product name, code, industry badge, component count, check indicator
 * - Selected product has emerald left border + emerald check circle
 * - Error handling with retry functionality
 * - Request ID deduplication to prevent stale responses
 * - Accessibility-compliant (ARIA labels, keyboard navigation)
 *
 * Replaces: ProductSelector.tsx (Phase 9 Emerald Night 5B rebuild)
 */

import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { Search, Loader2, Check, Grid2X2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { productsAPI } from '@/services/api/products';
import { emissionFactorsAPI } from '@/services/api/emissionFactors';
import { transformAPIBOMToFrontend } from '@/services/bomTransform';
import { useDebounce } from '@/hooks/useDebounce';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import type { UnitType } from '@/types/store.types';
import type { EmissionFactorListItem, ProductDetail } from '@/types/api.types';

// ============================================================================
// Constants
// ============================================================================

/** Debounce delay for search input */
const SEARCH_DEBOUNCE_MS = 300;

/** Industry display labels */
const INDUSTRY_LABELS: Record<string, string> = {
  electronics: 'Electronics',
  apparel: 'Apparel & Textiles',
  footwear: 'Footwear',
  automotive: 'Automotive',
  construction: 'Construction',
  food_beverage: 'Food & Beverage',
  packaging: 'Packaging',
  energy: 'Energy',
  other: 'Other',
};

/** Industry sort order (most common first) */
const INDUSTRY_ORDER = [
  'electronics',
  'apparel',
  'footwear',
  'automotive',
  'construction',
  'food_beverage',
  'packaging',
  'energy',
  'other',
];

/** Industry badge color classes */
const INDUSTRY_BADGE_COLORS: Record<string, string> = {
  electronics: 'bg-blue-500/[0.18] text-blue-400 border-blue-500/[0.22]',
  apparel: 'bg-emerald-500/[0.18] text-emerald-400 border-emerald-500/[0.22]',
  footwear: 'bg-emerald-500/[0.18] text-emerald-400 border-emerald-500/[0.22]',
  automotive: 'bg-red-500/[0.18] text-red-400 border-red-500/[0.22]',
  packaging: 'bg-amber-500/[0.18] text-amber-400 border-amber-500/[0.22]',
  construction: 'bg-purple-500/[0.18] text-purple-400 border-purple-500/[0.22]',
  food_beverage: 'bg-orange-500/[0.18] text-orange-400 border-orange-500/[0.22]',
  energy: 'bg-purple-500/[0.18] text-purple-400 border-purple-500/[0.22]',
};

const DEFAULT_BADGE_COLORS = 'bg-slate-500/[0.18] text-slate-400 border-slate-500/[0.22]';

// ============================================================================
// Sub-components
// ============================================================================

/**
 * Category type for product search results.
 * Can be a CategoryInfo object or null.
 */
interface CategoryInfo {
  id: string;
  code: string;
  name: string;
  industry_sector: string | null;
}

/**
 * Extract industry string from product category field.
 * Handles both CategoryInfo objects and legacy string categories.
 */
function getIndustry(product: ProductDetail): string {
  if (!product.category) return 'other';
  if (typeof product.category === 'string') return product.category.toLowerCase().trim();
  const category = product.category as unknown as CategoryInfo;
  if (category.industry_sector) return category.industry_sector.toLowerCase().trim();
  if (category.code) return category.code.toLowerCase().trim();
  return 'other';
}

/**
 * Group products by industry, sorted by INDUSTRY_ORDER.
 */
function groupProductsByIndustry(products: ProductDetail[]): Map<string, ProductDetail[]> {
  const groups = new Map<string, ProductDetail[]>();

  for (const product of products) {
    const industry = getIndustry(product);
    if (!groups.has(industry)) {
      groups.set(industry, []);
    }
    groups.get(industry)!.push(product);
  }

  // Sort by predefined order
  const sorted = new Map<string, ProductDetail[]>();
  for (const key of INDUSTRY_ORDER) {
    if (groups.has(key)) {
      sorted.set(key, groups.get(key)!);
      groups.delete(key);
    }
  }
  // Append any remaining (unlisted) industries
  for (const [key, items] of groups) {
    sorted.set(key, items);
  }

  return sorted;
}

/**
 * IndustryBadge - renders a colored pill badge for industry sectors.
 */
const IndustryBadge: React.FC<{ industry: string }> = ({ industry }) => {
  const colorClasses = INDUSTRY_BADGE_COLORS[industry] || DEFAULT_BADGE_COLORS;
  const label = INDUSTRY_LABELS[industry] || industry;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[0.75rem] font-semibold uppercase tracking-wide whitespace-nowrap border',
        colorClasses
      )}
    >
      <span className="w-[7px] h-[7px] rounded-full bg-current" />
      {label}
    </span>
  );
};

/**
 * ErrorDisplay - error state with retry functionality.
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
 * Loading skeleton for initial emission factors load.
 */
const ProductListSkeleton: React.FC = () => (
  <div className="space-y-6" data-testid="product-list-skeleton">
    <div className="space-y-2">
      <div className="h-8 w-48 bg-white/[0.06] animate-pulse rounded" />
      <div className="h-4 w-80 bg-white/[0.04] animate-pulse rounded" />
    </div>
    <div className="glass-card p-5">
      <div className="h-12 w-full bg-white/[0.04] animate-pulse rounded-[10px]" />
      <div className="flex gap-3 mt-4">
        <div className="h-5 w-20 bg-white/[0.04] animate-pulse rounded-full" />
        <div className="h-7 w-24 bg-white/[0.04] animate-pulse rounded-full" />
        <div className="h-7 w-24 bg-white/[0.04] animate-pulse rounded-full" />
      </div>
    </div>
    <div className="glass-card overflow-hidden">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center px-6 py-3.5 border-b border-white/[0.04]">
          <div className="flex-1 space-y-2">
            <div className="h-4 w-48 bg-white/[0.06] animate-pulse rounded" />
            <div className="h-3 w-24 bg-white/[0.04] animate-pulse rounded" />
          </div>
          <div className="w-[22px] h-[22px] rounded-full bg-white/[0.04] animate-pulse" />
        </div>
      ))}
    </div>
  </div>
);

// ============================================================================
// Main Component
// ============================================================================

const ProductList: React.FC = () => {
  // ---------------------------------------------------------------------------
  // Search & filter state
  // ---------------------------------------------------------------------------
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedSearch = useDebounce(searchQuery, SEARCH_DEBOUNCE_MS);

  /** BOM filter: default to showing only products with BOMs */
  const [showOnlyWithBom, setShowOnlyWithBom] = useState(true);

  /** Industry filter: null = all industries */
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Products state
  // ---------------------------------------------------------------------------
  const [products, setProducts] = useState<ProductDetail[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [bomError, setBomError] = useState<Error | null>(null);
  const [totalProducts, setTotalProducts] = useState(0);

  // ---------------------------------------------------------------------------
  // Emission factors state
  // ---------------------------------------------------------------------------
  const [emissionFactors, setEmissionFactors] = useState<EmissionFactorListItem[]>([]);
  const [isLoadingEmissionFactors, setIsLoadingEmissionFactors] = useState(true);

  // ---------------------------------------------------------------------------
  // Refs
  // ---------------------------------------------------------------------------
  /** Request ID counter for deduplicating stale API responses */
  const currentRequestIdRef = useRef(0);

  /** Track previous search query for detecting clears */
  const prevSearchQueryRef = useRef('');

  // ---------------------------------------------------------------------------
  // Store access
  // ---------------------------------------------------------------------------
  const {
    selectedProductId,
    setSelectedProduct,
    setLoadingBOM,
    setBomItems,
    setSelectedProductDetails,
  } = useCalculatorStore();

  const { markStepComplete, markStepIncomplete } = useWizardStore();

  // ---------------------------------------------------------------------------
  // Derived state
  // ---------------------------------------------------------------------------

  /** Products grouped by industry for display */
  const groupedProducts = useMemo(() => groupProductsByIndustry(products), [products]);

  /** Available industries derived from current product list */
  const availableIndustries = useMemo(() => {
    const industries = new Set<string>();
    products.forEach((p) => {
      const ind = getIndustry(p);
      if (ind !== 'other') industries.add(ind);
    });
    return INDUSTRY_ORDER.filter((ind) => industries.has(ind));
  }, [products]);

  // ---------------------------------------------------------------------------
  // Load emission factors on mount
  // ---------------------------------------------------------------------------
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

  // ---------------------------------------------------------------------------
  // Search products via API
  // ---------------------------------------------------------------------------
  /**
   * Fetches products from the backend search endpoint.
   * Uses request ID pattern to prevent stale responses from overwriting
   * newer data (race condition fix from TASK-FE-P7-042).
   */
  const searchProducts = useCallback(
    async (query: string, hasBom: boolean, industry?: string | null) => {
      const requestId = ++currentRequestIdRef.current;

      setIsSearching(true);
      setError(null);

      try {
        const result = await productsAPI.search({
          query: query.trim() || undefined,
          limit: 50,
          offset: 0,
          is_finished_product: true,
          has_bom: hasBom || undefined,
          industry: industry || undefined,
        });

        // Only update if this is still the current request
        if (requestId === currentRequestIdRef.current) {
          setProducts(result.items);
          setTotalProducts(result.total);
        }
      } catch (err) {
        if (requestId === currentRequestIdRef.current) {
          setError(err instanceof Error ? err : new Error('Unknown error'));
        }
      } finally {
        if (requestId === currentRequestIdRef.current) {
          setIsSearching(false);
        }
      }
    },
    []
  );

  // ---------------------------------------------------------------------------
  // Effects: trigger search on param changes
  // ---------------------------------------------------------------------------

  /**
   * Consolidated search effect.
   * Fires whenever debounced search, BOM filter, or industry filter changes.
   * Always searches because the product list is always visible (no popover).
   */
  useEffect(() => {
    searchProducts(debouncedSearch, showOnlyWithBom, selectedIndustry);
  }, [debouncedSearch, showOnlyWithBom, selectedIndustry, searchProducts]);

  /**
   * Immediate search on query clear (no debounce wait).
   */
  useEffect(() => {
    if (prevSearchQueryRef.current !== '' && searchQuery === '') {
      searchProducts('', showOnlyWithBom, selectedIndustry);
    }
    prevSearchQueryRef.current = searchQuery;
  }, [searchQuery, showOnlyWithBom, selectedIndustry, searchProducts]);

  /**
   * Sync wizard step completion based on product selection.
   */
  useEffect(() => {
    if (selectedProductId !== null) {
      markStepComplete('select');
    } else {
      markStepIncomplete('select');
    }
  }, [selectedProductId, markStepComplete, markStepIncomplete]);

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  /** Toggle the BOM filter switch */
  const handleBomFilterChange = useCallback((value: boolean) => {
    setShowOnlyWithBom(value);
  }, []);

  /**
   * Handle product selection.
   * Fetches full product details + BOM, transforms BOM, and updates stores.
   */
  const handleProductSelect = async (productId: string, _productName: string) => {
    if (!productId) return;

    try {
      setBomError(null);
      setLoadingBOM(true);
      setSelectedProduct(productId);

      // Fetch full product details with BOM
      const productDetail = await productsAPI.getById(productId);

      // Store product details
      setSelectedProductDetails({
        id: productDetail.id,
        code: productDetail.code,
        name: productDetail.name,
        category: productDetail.category || 'unknown',
        unit: productDetail.unit as UnitType,
        is_finished_product: productDetail.is_finished_product,
      });

      // Transform and store BOM
      const transformedBOM = transformAPIBOMToFrontend(
        productDetail.bill_of_materials,
        emissionFactors
      );
      setBomItems(transformedBOM);
    } catch (err) {
      console.error('Failed to load product BOM:', err);
      setBomError(err instanceof Error ? err : new Error('Failed to load BOM'));
    } finally {
      setLoadingBOM(false);
    }
  };

  /** Retry BOM loading for currently selected product */
  const retryBOMLoad = async () => {
    const product = useCalculatorStore.getState().selectedProduct;
    if (selectedProductId && product) {
      await handleProductSelect(selectedProductId, product.name);
    }
  };

  /** Retry product list load after error */
  const retryLoad = () => {
    setError(null);
    searchProducts(debouncedSearch, showOnlyWithBom, selectedIndustry);
  };

  // ---------------------------------------------------------------------------
  // Render: loading skeleton
  // ---------------------------------------------------------------------------
  if (isLoadingEmissionFactors) {
    return <ProductListSkeleton />;
  }

  // ---------------------------------------------------------------------------
  // Render: fatal error (no products at all)
  // ---------------------------------------------------------------------------
  if (error && products.length === 0) {
    return <ErrorDisplay error={error} onRetry={retryLoad} />;
  }

  // ---------------------------------------------------------------------------
  // Main render
  // ---------------------------------------------------------------------------
  return (
    <div data-testid="product-list" data-tour="product-select" className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="font-heading text-[1.625rem] font-bold tracking-tight text-[var(--text-primary)]">
          Select a Product
        </h1>
        <p className="text-[var(--text-muted)] text-[0.9375rem]">
          Choose a product to calculate its cradle-to-gate carbon footprint
        </p>
      </div>

      {/* Search Card */}
      <div className="glass-card p-5 animate-fadeInUp" style={{ animationDelay: '0.1s' }}>
        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-[var(--text-dim)] pointer-events-none" />
          <input
            type="text"
            placeholder="Search products by name or code..."
            className="w-full py-3 pl-11 pr-4 bg-white/[0.03] border border-[var(--card-border)] rounded-[10px] text-[var(--text-primary)] text-[0.9375rem] placeholder:text-[var(--text-dim)] focus:border-emerald-500/40 focus:ring-[3px] focus:ring-emerald-500/[0.08] focus:outline-none transition-all"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search products"
            data-testid="product-search-input"
          />
        </div>

        {/* Filter Row */}
        <div className="flex items-center gap-3 mt-4 flex-wrap">
          {/* BOM Toggle Switch */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              role="switch"
              aria-checked={showOnlyWithBom}
              aria-label="Show only products with BOMs"
              onClick={() => handleBomFilterChange(!showOnlyWithBom)}
              className={cn(
                'relative w-[38px] h-5 rounded-full transition-colors cursor-pointer',
                showOnlyWithBom ? 'bg-emerald-500' : 'bg-slate-600'
              )}
              data-testid="bom-toggle-switch"
            >
              <span
                className={cn(
                  'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform',
                  showOnlyWithBom && 'translate-x-[18px]'
                )}
              />
            </button>
            <span className="text-[0.8125rem] text-[var(--text-muted)] font-medium">
              With BOMs
            </span>
          </div>

          {/* Separator */}
          <div className="w-px h-5 bg-white/10" />

          {/* Industry Label */}
          <span className="text-[0.8125rem] text-[var(--text-dim)] font-medium">Industry:</span>

          {/* Industry Pills */}
          <div className="flex gap-1.5 flex-wrap">
            <button
              type="button"
              className={cn(
                'px-3.5 py-1.5 rounded-full text-[0.8125rem] font-medium border transition-all cursor-pointer whitespace-nowrap',
                !selectedIndustry
                  ? 'bg-[var(--accent-emerald-dim)] border-emerald-500/35 text-emerald-400'
                  : 'border-[var(--card-border)] text-[var(--text-muted)] hover:border-white/[0.16] hover:text-[var(--text-primary)]'
              )}
              onClick={() => setSelectedIndustry(null)}
              data-testid="industry-filter-all"
            >
              All Industries
            </button>
            {availableIndustries.map((industry) => (
              <button
                key={industry}
                type="button"
                className={cn(
                  'px-3.5 py-1.5 rounded-full text-[0.8125rem] font-medium border transition-all cursor-pointer whitespace-nowrap',
                  selectedIndustry === industry
                    ? 'bg-[var(--accent-emerald-dim)] border-emerald-500/35 text-emerald-400'
                    : 'border-[var(--card-border)] text-[var(--text-muted)] hover:border-white/[0.16] hover:text-[var(--text-primary)]'
                )}
                onClick={() => setSelectedIndustry(industry)}
                data-testid={`industry-filter-${industry}`}
              >
                {INDUSTRY_LABELS[industry] || industry}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Product List Card */}
      <div
        className="glass-card overflow-hidden animate-fadeInUp"
        style={{ animationDelay: '0.2s' }}
      >
        {isSearching ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-[var(--text-dim)]" />
            <span className="ml-2 text-sm text-[var(--text-muted)]">Searching...</span>
          </div>
        ) : products.length === 0 ? (
          <div className="py-12 text-center text-[var(--text-muted)]">
            {searchQuery
              ? `No products found for "${searchQuery}"`
              : showOnlyWithBom
                ? 'No products with BOMs available'
                : 'No products available'}
          </div>
        ) : (
          Array.from(groupedProducts.entries()).map(([industry, industryProducts]) => (
            <div key={industry}>
              {/* Industry Group Header */}
              <div className="px-6 py-2.5 font-heading text-[0.6875rem] font-semibold uppercase tracking-wider text-[var(--text-dim)] bg-white/[0.02] border-b border-[var(--card-border)]">
                {INDUSTRY_LABELS[industry] || industry}
              </div>
              {/* Product Rows */}
              {industryProducts.map((product) => {
                const isSelected = selectedProductId === product.id;
                const bomCount =
                  product.bill_of_materials?.length ||
                  (product as ProductDetail & { bom_count?: number }).bom_count ||
                  0;
                return (
                  <div
                    key={product.id}
                    onClick={() => handleProductSelect(product.id, product.name)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleProductSelect(product.id, product.name);
                      }
                    }}
                    role="option"
                    aria-selected={isSelected}
                    tabIndex={0}
                    className={cn(
                      'flex items-center px-4 sm:px-6 py-3 sm:py-3.5 border-b border-white/[0.04] cursor-pointer transition-colors',
                      isSelected &&
                        'bg-emerald-500/[0.06] border-l-[3px] border-l-emerald-500 pl-[calc(1.5rem-3px)]',
                      !isSelected && 'hover:bg-white/[0.025]'
                    )}
                    data-testid={`product-row-${product.id}`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="font-heading text-[0.9375rem] font-semibold text-[var(--text-primary)] leading-tight">
                        {product.name}
                      </div>
                      <div className="text-[0.8125rem] text-[var(--text-dim)] tabular-nums mt-0.5">
                        {product.code}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 sm:gap-4 shrink-0">
                      {/* Industry badge - hidden on mobile (shown in group header) */}
                      <span className="hidden sm:inline-flex">
                        <IndustryBadge industry={getIndustry(product)} />
                      </span>
                      {/* Component count */}
                      {bomCount > 0 && (
                        <span className="text-[0.75rem] sm:text-[0.8125rem] text-[var(--text-dim)] flex items-center gap-1.5 whitespace-nowrap">
                          <Grid2X2 className="w-3.5 h-3.5" />
                          {bomCount} component{bomCount !== 1 ? 's' : ''}
                        </span>
                      )}
                      {/* Check indicator */}
                      <div
                        className={cn(
                          'w-[22px] h-[22px] rounded-full border-2 flex items-center justify-center shrink-0 ml-4 transition-all',
                          isSelected
                            ? 'bg-emerald-500 border-emerald-500'
                            : 'border-white/15'
                        )}
                      >
                        {isSelected && <Check className="w-3 h-3 text-white" />}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ))
        )}

        {/* Total count footer */}
        {!isSearching && totalProducts > 50 && (
          <div className="border-t border-[var(--card-border)] p-3 text-center text-xs text-[var(--text-dim)]">
            Showing 50 of {totalProducts} results. Type to search for more.
          </div>
        )}
      </div>

      {/* BOM Loading Error */}
      {bomError && <ErrorDisplay error={bomError} onRetry={retryBOMLoad} context="bom" />}
    </div>
  );
};

export default ProductList;
