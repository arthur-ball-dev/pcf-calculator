/**
 * ProductSearchResults Component
 * TASK-FE-P5-004: Enhanced Product Search
 *
 * Displays a grid of product cards from search results.
 * Shows product name, code, category, manufacturer, and country.
 * Supports click handling for product selection.
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Product } from '@/hooks/useProductSearch';

/**
 * Props for ProductSearchResults component
 */
export interface ProductSearchResultsProps {
  /** List of products to display */
  products: Product[];
  /** Callback when a product is clicked */
  onProductClick?: (product: Product) => void;
  /** Whether to show empty state message when no products */
  showEmptyState?: boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Displays a grid of product cards
 *
 * @example
 * ```tsx
 * <ProductSearchResults
 *   products={searchResults}
 *   onProductClick={(product) => selectProduct(product)}
 *   showEmptyState={true}
 * />
 * ```
 */
export function ProductSearchResults({
  products,
  onProductClick,
  showEmptyState = false,
  className,
}: ProductSearchResultsProps) {
  // Handle empty state
  if (products.length === 0) {
    if (showEmptyState) {
      return (
        <div className="text-center py-12" data-testid="no-results">
          <p className="text-gray-500 mb-2">No products found</p>
          <p className="text-sm text-gray-400">
            Try adjusting your search or filters
          </p>
        </div>
      );
    }
    return null;
  }

  /**
   * Handle card click
   */
  const handleCardClick = (product: Product) => {
    onProductClick?.(product);
  };

  /**
   * Handle keyboard activation
   */
  const handleKeyDown = (event: React.KeyboardEvent, product: Product) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onProductClick?.(product);
    }
  };

  return (
    <div
      className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className || ''}`}
      data-testid="results-grid"
    >
      {products.map((product) => (
        <Card
          key={product.id}
          className={`${onProductClick ? 'cursor-pointer hover:border-blue-300' : ''} transition-colors`}
          onClick={() => handleCardClick(product)}
          onKeyDown={(e) => handleKeyDown(e, product)}
          tabIndex={onProductClick ? 0 : undefined}
          role={onProductClick ? 'button' : undefined}
          data-testid={`product-card-${product.id}`}
        >
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-base">{product.name}</CardTitle>
                <CardDescription className="text-xs">{product.code}</CardDescription>
              </div>
              {product.is_finished_product && (
                <Badge variant="outline" className="text-xs">
                  Finished
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {product.description && (
              <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                {product.description}
              </p>
            )}
            <div className="flex flex-wrap gap-1">
              {product.category && (
                <Badge variant="secondary" className="text-xs">
                  {product.category.name}
                </Badge>
              )}
              {product.manufacturer && (
                <Badge variant="outline" className="text-xs">
                  {product.manufacturer}
                </Badge>
              )}
              {product.country_of_origin && (
                <Badge variant="outline" className="text-xs">
                  {product.country_of_origin}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default ProductSearchResults;
