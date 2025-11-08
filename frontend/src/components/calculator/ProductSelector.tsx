/**
 * ProductSelector Component
 *
 * Allows users to select a product from a dropdown list for PCF calculation.
 * Integrates with wizardStore to mark step complete and calculatorStore to save selection.
 *
 * Features:
 * - Fetches products from backend API on mount
 * - Displays products with name and category
 * - Loading skeleton during API request
 * - Error handling with retry functionality
 * - Integration with Zustand stores
 * - Accessibility-compliant (ARIA labels, keyboard navigation)
 */

import React, { useEffect, useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { fetchProducts } from '@/services/api/products';
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
import type { Product } from '@/types/store.types';

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
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error, onRetry }) => {
  return (
    <Alert variant="destructive">
      <AlertDescription className="space-y-3">
        <div>
          <p className="font-semibold">Unable to load products</p>
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

  // Store access
  const { selectedProductId, setSelectedProduct } = useCalculatorStore();
  const { markStepComplete, markStepIncomplete } = useWizardStore();

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
   * Handle product selection
   */
  const handleProductSelect = (value: string) => {
    const productId = parseInt(value, 10);

    if (!isNaN(productId)) {
      setSelectedProduct(productId);

      // Optionally, fetch full product details here
      const selectedProduct = products.find((p) => p.id === productId);
      if (selectedProduct) {
        useCalculatorStore.getState().setSelectedProductDetails(selectedProduct);
      }
    }
  };

  /**
   * Render loading state
   */
  if (isLoading) {
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
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="product-select">Select Product</Label>
        <Select
          value={selectedProductId?.toString() || ''}
          onValueChange={handleProductSelect}
        >
          <SelectTrigger
            id="product-select"
            className="w-full"
            aria-label="Select a product to calculate carbon footprint"
          >
            <SelectValue placeholder="Choose a product to calculate PCF" />
          </SelectTrigger>
          <SelectContent>
            {products.length === 0 ? (
              <div className="px-2 py-6 text-center text-sm text-muted-foreground">
                No products available
              </div>
            ) : (
              products.map((product) => (
                <SelectItem key={product.id} value={String(product.id)}>
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

      {selectedProductId && (
        <Alert className="bg-muted border-muted-foreground/20">
          <AlertDescription className="text-sm text-muted-foreground">
            ✓ Product selected. Click "Next" to edit the Bill of Materials.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};

export default ProductSelector;
