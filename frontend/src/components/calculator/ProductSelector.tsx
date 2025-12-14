/**
 * ProductSelector Component
 *
 * Allows users to select a product from a dropdown list for PCF calculation.
 * Integrates with wizardStore to mark step complete and calculatorStore to save selection.
 *
 * Features:
 * - Fetches products from backend API on mount
 * - Fetches emission factors for BOM transformation
 * - Loads full product details with BOM when product selected
 * - Transforms API BOM format to frontend format
 * - Populates calculator store with valid BOM items
 * - Displays products with name and category
 * - Loading skeleton during API request
 * - Error handling with retry functionality
 * - Integration with Zustand stores
 * - Accessibility-compliant (ARIA labels, keyboard navigation)
 *
 * Enhanced in TASK-FE-019: BOM loading functionality
 * UPDATED in TASK-FE-020: UUID type system migration (no parseInt conversion)
 */

import React, { useEffect, useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { fetchProducts, productsAPI } from '@/services/api/products';
import { emissionFactorsAPI } from '@/services/api/emissionFactors';
import { transformAPIBOMToFrontend } from '@/services/bomTransform';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import type { Product, UnitType } from '@/types/store.types';
import type { EmissionFactorListItem } from '@/types/api.types';

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
 * Main ProductSelector component
 */
const ProductSelector: React.FC = () => {
  // State
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [bomError, setBomError] = useState<Error | null>(null);

  // Emission factors state
  const [emissionFactors, setEmissionFactors] = useState<EmissionFactorListItem[]>([]);
  const [isLoadingEmissionFactors, setIsLoadingEmissionFactors] = useState(true);

  // Store access
  const { selectedProductId, setSelectedProduct, setLoadingBOM, setBomItems, setSelectedProductDetails } = useCalculatorStore();
  const { markStepComplete, markStepIncomplete } = useWizardStore();

  /**
   * Load emission factors on component mount
   * Fetches all emission factors for BOM transformation
   */
  useEffect(() => {
    const loadEmissionFactors = async () => {
      setIsLoadingEmissionFactors(true);
      try {
        // Fetch all emission factors (use large limit)
        const factors = await emissionFactorsAPI.list({ limit: 1000 });
        setEmissionFactors(factors);
      } catch (err) {
        console.error('Failed to load emission factors:', err);
        // Non-blocking error - BOM transformation will use fallback
        // Set emissionFactorId to null for unmatched components
      } finally {
        setIsLoadingEmissionFactors(false);
      }
    };

    loadEmissionFactors();
  }, []);

  /**
   * Load products from API
   */
  const loadProducts = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const fetchedProducts = await fetchProducts({
        is_finished_product: true, // Only show finished products in selector
      });
      setProducts(fetchedProducts);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Load products on component mount
   */
  useEffect(() => {
    loadProducts();
  }, []);

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
   *
   * Enhanced in TASK-FE-019:
   * 1. Fetches full product details with BOM
   * 2. Transforms API BOM format to frontend format
   * 3. Maps component names to emission factor IDs
   * 4. Populates calculator store with valid BOM items
   *
   * UPDATED in TASK-FE-020:
   * - Removed parseInt() conversion - preserves full UUID strings
   * - Product IDs are now handled as strings throughout
   */
  const handleProductSelect = async (value: string) => {
    const productId = value; // Keep as string (UUIDs are strings)

    if (!productId) return;

    try {
      // Clear previous BOM error
      setBomError(null);

      // Set loading state
      setLoadingBOM(true);

      // Store product ID immediately (for UI feedback)
      // UPDATED: No parseInt conversion - store as string
      setSelectedProduct(productId);

      // Fetch full product details with BOM
      const productDetail = await productsAPI.getById(productId);

      // Store full product details
      // UPDATED: Product ID is already a string from API
      setSelectedProductDetails({
        id: productDetail.id, // String UUID from API
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
      // Show error to user
      setBomError(err instanceof Error ? err : new Error('Failed to load BOM'));
    } finally {
      setLoadingBOM(false);
    }
  };

  /**
   * Retry BOM loading for currently selected product
   */
  const retryBOMLoad = async () => {
    if (selectedProductId !== null) {
      await handleProductSelect(selectedProductId); // Already a string
    }
  };

  /**
   * Render loading state
   */
  if (isLoadingEmissionFactors || isLoading) {
    return <ProductSelectorSkeleton />;
  }

  /**
   * Render error state
   */
  if (error) {
    return <ErrorDisplay error={error} onRetry={loadProducts} />;
  }

  /**
   * Main render
   */
  return (
    <div className="space-y-4" data-testid="product-selector" data-tour="product-select">
      <div className="space-y-2">
        <Label htmlFor="product-select">Select Product</Label>
        <Select
          value={selectedProductId || ''} // Product ID is already a string
          onValueChange={handleProductSelect}
        >
          <SelectTrigger
            id="product-select"
            className="w-full"
            aria-label="Select a product to calculate carbon footprint"
            data-testid="product-select-trigger"
          >
            <SelectValue placeholder="Choose a product to calculate PCF" />
          </SelectTrigger>
          <SelectContent data-testid="product-select-content">
            {products.length === 0 ? (
              <div className="px-2 py-6 text-center text-sm text-muted-foreground">
                No products available
              </div>
            ) : (
              products.map((product) => (
                <SelectItem
                  key={product.id}
                  value={product.id} // Product ID is string UUID
                  data-testid={`product-option-${product.id}`}
                >
                  {product.name}
                  {product.category && (
                    <span className="text-muted-foreground ml-2">
                      ({product.category})
                    </span>
                  )}
                </SelectItem>
              ))
            )}
          </SelectContent>
        </Select>
      </div>

      {/* Product Selected Confirmation - Always show when product selected */}
      {selectedProductId && (
        <Alert className="bg-muted border-muted-foreground/20" data-testid="product-selected-confirmation">
          <AlertDescription className="text-sm text-muted-foreground">
            ✓ Product selected. Click "Next" to edit the Bill of Materials.
          </AlertDescription>
        </Alert>
      )}

      {/* BOM Loading Error - Show below confirmation if BOM fetch failed */}
      {bomError && (
        <ErrorDisplay error={bomError} onRetry={retryBOMLoad} context="bom" />
      )}
    </div>
  );
};

export default ProductSelector;
