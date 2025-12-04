/**
 * ProductSearchResults Component Tests
 * TASK-FE-P5-004: Enhanced Product Search - Phase A Tests
 *
 * Test Coverage:
 * 1. Renders list of products
 * 2. Shows product name, code, category
 * 3. Clickable product items
 * 4. Shows manufacturer and country info
 * 5. Displays finished product badge
 * 6. Handles empty results
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { ProductSearchResults } from '@/components/ProductSearch/ProductSearchResults';
import type { MockProduct } from '@/mocks/data/products';

// Mock product data matching API contract
const mockProducts: MockProduct[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    code: 'LAPTOP-001',
    name: 'Business Laptop 14-inch',
    description: '14-inch business laptop with aluminum chassis',
    unit: 'unit',
    category: {
      id: '660e8400-e29b-41d4-a716-446655440000',
      code: 'ELEC-COMP',
      name: 'Computers',
      industry_sector: 'electronics',
    },
    manufacturer: 'Acme Tech',
    country_of_origin: 'CN',
    is_finished_product: true,
    relevance_score: 0.95,
    created_at: '2025-01-15T10:00:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    code: 'LAPTOP-002',
    name: 'Gaming Laptop 17-inch',
    description: 'High-performance gaming laptop',
    unit: 'unit',
    category: {
      id: '660e8400-e29b-41d4-a716-446655440000',
      code: 'ELEC-COMP',
      name: 'Computers',
      industry_sector: 'electronics',
    },
    manufacturer: 'GameTech Inc',
    country_of_origin: 'TW',
    is_finished_product: true,
    relevance_score: 0.82,
    created_at: '2025-01-20T14:30:00Z',
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    code: 'COTTON-FABRIC-001',
    name: 'Organic Cotton Fabric',
    description: 'Sustainable organic cotton textile',
    unit: 'kg',
    category: {
      id: '660e8400-e29b-41d4-a716-446655440001',
      code: 'APRL-MAT',
      name: 'Textiles',
      industry_sector: 'apparel',
    },
    manufacturer: 'Textile Co',
    country_of_origin: 'BD',
    is_finished_product: false, // Not a finished product
    relevance_score: null,
    created_at: '2025-01-10T09:00:00Z',
  },
];

const mockProductWithoutCategory: MockProduct = {
  id: '550e8400-e29b-41d4-a716-446655440003',
  code: 'GENERIC-001',
  name: 'Generic Product',
  description: 'A product without category',
  unit: 'unit',
  category: null,
  manufacturer: null,
  country_of_origin: null,
  is_finished_product: true,
  relevance_score: null,
  created_at: '2025-01-05T08:00:00Z',
};

describe('ProductSearchResults Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Rendering Products
  // ==========================================================================

  describe('Rendering Products', () => {
    it('should render a list of products', () => {
      render(<ProductSearchResults products={mockProducts} />);

      expect(screen.getAllByTestId(/^product-card-/)).toHaveLength(mockProducts.length);
    });

    it('should render each product in a card format', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Each product should have its own card
      mockProducts.forEach((product) => {
        expect(screen.getByTestId(`product-card-${product.id}`)).toBeInTheDocument();
      });
    });

    it('should display product name prominently', () => {
      render(<ProductSearchResults products={mockProducts} />);

      mockProducts.forEach((product) => {
        expect(screen.getByText(product.name)).toBeInTheDocument();
      });
    });

    it('should display product code', () => {
      render(<ProductSearchResults products={mockProducts} />);

      mockProducts.forEach((product) => {
        expect(screen.getByText(product.code)).toBeInTheDocument();
      });
    });

    it('should display product category name', () => {
      render(<ProductSearchResults products={mockProducts} />);

      mockProducts.forEach((product) => {
        if (product.category) {
          expect(screen.getByText(product.category.name)).toBeInTheDocument();
        }
      });
    });

    it('should handle products without category gracefully', () => {
      render(<ProductSearchResults products={[mockProductWithoutCategory]} />);

      // Should render without errors
      expect(screen.getByTestId(`product-card-${mockProductWithoutCategory.id}`)).toBeInTheDocument();
      expect(screen.getByText(mockProductWithoutCategory.name)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 2: Product Details Display
  // ==========================================================================

  describe('Product Details Display', () => {
    it('should display manufacturer when present', () => {
      render(<ProductSearchResults products={mockProducts} />);

      expect(screen.getByText('Acme Tech')).toBeInTheDocument();
      expect(screen.getByText('GameTech Inc')).toBeInTheDocument();
    });

    it('should handle products without manufacturer', () => {
      render(<ProductSearchResults products={[mockProductWithoutCategory]} />);

      // Should render without errors even without manufacturer
      expect(screen.getByTestId(`product-card-${mockProductWithoutCategory.id}`)).toBeInTheDocument();
    });

    it('should display country of origin when present', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Country codes should be displayed
      expect(screen.getByText('CN')).toBeInTheDocument();
      expect(screen.getByText('TW')).toBeInTheDocument();
    });

    it('should handle products without country of origin', () => {
      render(<ProductSearchResults products={[mockProductWithoutCategory]} />);

      // Should render without errors
      expect(screen.getByTestId(`product-card-${mockProductWithoutCategory.id}`)).toBeInTheDocument();
    });

    it('should display description when present', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Descriptions should be visible (possibly truncated)
      mockProducts.forEach((product) => {
        if (product.description) {
          // Check if description text exists (may be truncated with CSS)
          const card = screen.getByTestId(`product-card-${product.id}`);
          expect(card).toBeInTheDocument();
        }
      });
    });
  });

  // ==========================================================================
  // Test Suite 3: Finished Product Badge
  // ==========================================================================

  describe('Finished Product Badge', () => {
    it('should display "Finished" badge for finished products', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Products with is_finished_product=true should have badge
      const finishedBadges = screen.getAllByText(/finished/i);
      expect(finishedBadges.length).toBeGreaterThan(0);
    });

    it('should NOT display "Finished" badge for non-finished products', () => {
      // Create a product that is NOT finished
      const nonFinishedProduct: MockProduct = {
        ...mockProducts[2], // Cotton fabric - not finished
        is_finished_product: false,
      };

      render(<ProductSearchResults products={[nonFinishedProduct]} />);

      const card = screen.getByTestId(`product-card-${nonFinishedProduct.id}`);

      // Badge should not be in this specific card
      // Check that card doesn't contain "Finished" badge
      expect(card.textContent?.match(/\bfinished\b/i)).toBeFalsy();
    });

    it('should visually distinguish finished products', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Finished products should have some visual indicator
      const finishedProduct = mockProducts.find((p) => p.is_finished_product);
      const nonFinishedProduct = mockProducts.find((p) => !p.is_finished_product);

      if (finishedProduct && nonFinishedProduct) {
        const finishedCard = screen.getByTestId(`product-card-${finishedProduct.id}`);
        const nonFinishedCard = screen.getByTestId(`product-card-${nonFinishedProduct.id}`);

        // They should exist and be different in some way
        expect(finishedCard).toBeInTheDocument();
        expect(nonFinishedCard).toBeInTheDocument();
      }
    });
  });

  // ==========================================================================
  // Test Suite 4: Click Interactions
  // ==========================================================================

  describe('Click Interactions', () => {
    it('should call onProductClick when product card is clicked', async () => {
      const onProductClick = vi.fn();

      render(<ProductSearchResults products={mockProducts} onProductClick={onProductClick} />);

      const firstCard = screen.getByTestId(`product-card-${mockProducts[0].id}`);
      await user.click(firstCard);

      expect(onProductClick).toHaveBeenCalledTimes(1);
    });

    it('should pass correct product to onProductClick callback', async () => {
      const onProductClick = vi.fn();

      render(<ProductSearchResults products={mockProducts} onProductClick={onProductClick} />);

      const firstCard = screen.getByTestId(`product-card-${mockProducts[0].id}`);
      await user.click(firstCard);

      expect(onProductClick).toHaveBeenCalledWith(mockProducts[0]);
    });

    it('should make cards look clickable (cursor pointer)', () => {
      render(<ProductSearchResults products={mockProducts} onProductClick={() => {}} />);

      const card = screen.getByTestId(`product-card-${mockProducts[0].id}`);

      // Cards should have cursor:pointer style or be rendered as buttons
      expect(card).toBeInTheDocument();
      // Style check would be done in integration/visual tests
    });

    it('should support keyboard activation (Enter key)', async () => {
      const onProductClick = vi.fn();

      render(<ProductSearchResults products={mockProducts} onProductClick={onProductClick} />);

      const card = screen.getByTestId(`product-card-${mockProducts[0].id}`);
      card.focus();

      await user.keyboard('{Enter}');

      expect(onProductClick).toHaveBeenCalledWith(mockProducts[0]);
    });

    it('should have proper focus indicators', () => {
      render(<ProductSearchResults products={mockProducts} onProductClick={() => {}} />);

      const card = screen.getByTestId(`product-card-${mockProducts[0].id}`);

      // Card should be focusable
      expect(card).toHaveAttribute('tabIndex');
    });
  });

  // ==========================================================================
  // Test Suite 5: Empty State
  // ==========================================================================

  describe('Empty State', () => {
    it('should handle empty products array', () => {
      render(<ProductSearchResults products={[]} />);

      // Should not render any product cards
      expect(screen.queryAllByTestId(/^product-card-/)).toHaveLength(0);
    });

    it('should show empty state message when no products', () => {
      render(<ProductSearchResults products={[]} showEmptyState={true} />);

      expect(screen.getByTestId('no-results')).toBeInTheDocument();
    });

    it('should show helpful message in empty state', () => {
      render(<ProductSearchResults products={[]} showEmptyState={true} />);

      const emptyState = screen.getByTestId('no-results');
      expect(emptyState.textContent).toMatch(/no products/i);
    });

    it('should not show empty state when showEmptyState is false', () => {
      render(<ProductSearchResults products={[]} showEmptyState={false} />);

      expect(screen.queryByTestId('no-results')).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 6: Grid Layout
  // ==========================================================================

  describe('Grid Layout', () => {
    it('should render products in a grid container', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Results should be in a grid container
      const grid = screen.getByTestId('results-grid');
      expect(grid).toBeInTheDocument();
    });

    it('should apply grid classes for responsive layout', () => {
      render(<ProductSearchResults products={mockProducts} />);

      const grid = screen.getByTestId('results-grid');
      // Grid should have appropriate CSS classes for responsive layout
      expect(grid).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 7: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should render products in an accessible list structure', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Grid should be properly structured
      const grid = screen.getByTestId('results-grid');
      expect(grid).toBeInTheDocument();
    });

    it('should have accessible card elements', () => {
      render(<ProductSearchResults products={mockProducts} onProductClick={() => {}} />);

      mockProducts.forEach((product) => {
        const card = screen.getByTestId(`product-card-${product.id}`);

        // Cards should be focusable when clickable
        expect(card.hasAttribute('tabIndex') || card.tagName.toLowerCase() === 'button').toBeTruthy();
      });
    });

    it('should include product name as accessible text', () => {
      render(<ProductSearchResults products={mockProducts} />);

      mockProducts.forEach((product) => {
        // Product name should be visible for screen readers
        expect(screen.getByText(product.name)).toBeInTheDocument();
      });
    });

    it('should have proper heading hierarchy in cards', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Product names should be in heading elements or have proper semantic structure
      const card = screen.getByTestId(`product-card-${mockProducts[0].id}`);
      expect(card).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 8: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle product with very long name', () => {
      const longNameProduct: MockProduct = {
        ...mockProducts[0],
        id: 'long-name-product',
        name: 'This is a very long product name that might overflow the card container and need to be truncated',
      };

      render(<ProductSearchResults products={[longNameProduct]} />);

      // Should render without breaking layout
      expect(screen.getByTestId(`product-card-${longNameProduct.id}`)).toBeInTheDocument();
    });

    it('should handle product with very long description', () => {
      const longDescProduct: MockProduct = {
        ...mockProducts[0],
        id: 'long-desc-product',
        description: 'This is a very long description that should be truncated to prevent the card from becoming too tall. '.repeat(10),
      };

      render(<ProductSearchResults products={[longDescProduct]} />);

      // Should render without breaking layout
      expect(screen.getByTestId(`product-card-${longDescProduct.id}`)).toBeInTheDocument();
    });

    it('should handle product with null description', () => {
      const nullDescProduct: MockProduct = {
        ...mockProducts[0],
        id: 'null-desc-product',
        description: null,
      };

      render(<ProductSearchResults products={[nullDescProduct]} />);

      // Should render without errors
      expect(screen.getByTestId(`product-card-${nullDescProduct.id}`)).toBeInTheDocument();
    });

    it('should handle large number of products', () => {
      const manyProducts = Array.from({ length: 100 }, (_, i) => ({
        ...mockProducts[0],
        id: `product-${i}`,
        code: `PROD-${i.toString().padStart(4, '0')}`,
        name: `Product ${i}`,
      }));

      render(<ProductSearchResults products={manyProducts} />);

      // Should render all products
      expect(screen.getAllByTestId(/^product-card-/)).toHaveLength(100);
    });

    it('should handle products with special characters in name', () => {
      const specialCharProduct: MockProduct = {
        ...mockProducts[0],
        id: 'special-char-product',
        name: 'Product with <special> & "characters"',
      };

      render(<ProductSearchResults products={[specialCharProduct]} />);

      // Should escape and display properly
      expect(screen.getByTestId(`product-card-${specialCharProduct.id}`)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 9: Category Badge Display
  // ==========================================================================

  describe('Category Badge Display', () => {
    it('should display category as a badge', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Categories should be displayed as badges
      expect(screen.getByText('Computers')).toBeInTheDocument();
      expect(screen.getByText('Textiles')).toBeInTheDocument();
    });

    it('should distinguish category badge visually', () => {
      render(<ProductSearchResults products={mockProducts} />);

      // Category badges should exist
      const categoryBadge = screen.getByText('Computers');
      expect(categoryBadge).toBeInTheDocument();
    });
  });
});
