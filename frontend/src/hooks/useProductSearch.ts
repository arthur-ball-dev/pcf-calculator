/**
 * useProductSearch Hook
 * TASK-FE-P5-004: Enhanced Product Search
 *
 * TanStack Query hook for the /api/v1/products/search endpoint.
 * Supports query, filters, and pagination.
 */

import { useQuery } from '@tanstack/react-query';
import client from '@/services/api/client';

/**
 * Product category structure
 */
export interface ProductCategory {
  id: string;
  code: string;
  name: string;
  industry_sector: string | null;
}

/**
 * Product structure matching API contract
 */
export interface Product {
  id: string;
  code: string;
  name: string;
  description: string | null;
  unit: string;
  category: ProductCategory | null;
  manufacturer: string | null;
  country_of_origin: string | null;
  is_finished_product: boolean;
  relevance_score: number | null;
  created_at: string;
}

/**
 * Search parameters for product search
 */
export interface ProductSearchParams {
  query?: string;
  categoryId?: string;
  industry?: string;
  manufacturer?: string;
  countryOfOrigin?: string;
  isFinishedProduct?: boolean;
  limit?: number;
  offset?: number;
}

/**
 * Search result structure matching API contract
 */
export interface ProductSearchResult {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Custom hook for product search with TanStack Query
 *
 * @param params - Search parameters
 * @param enabled - Whether the query should be enabled (default: true)
 * @returns TanStack Query result with loading, error, and data states
 *
 * @example
 * ```tsx
 * const { data, isLoading, error } = useProductSearch({
 *   query: 'laptop',
 *   industry: 'electronics',
 *   limit: 20
 * });
 * ```
 */
export function useProductSearch(params: ProductSearchParams, enabled: boolean = true) {
  return useQuery<ProductSearchResult>({
    queryKey: ['products', 'search', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();

      // Build query parameters
      if (params.query) {
        searchParams.set('query', params.query);
      }
      if (params.categoryId) {
        searchParams.set('category_id', params.categoryId);
      }
      if (params.industry) {
        searchParams.set('industry', params.industry);
      }
      if (params.manufacturer) {
        searchParams.set('manufacturer', params.manufacturer);
      }
      if (params.countryOfOrigin) {
        searchParams.set('country_of_origin', params.countryOfOrigin);
      }
      if (params.isFinishedProduct !== undefined) {
        searchParams.set('is_finished_product', String(params.isFinishedProduct));
      }

      // Pagination with defaults
      searchParams.set('limit', String(params.limit || 50));
      searchParams.set('offset', String(params.offset || 0));

      const response = await client.get<ProductSearchResult>(
        `/api/v1/products/search?${searchParams.toString()}`
      );

      return response.data;
    },
    enabled,
    staleTime: 30000, // 30 seconds - cache search results briefly
    placeholderData: (previousData) => previousData, // Keep previous data while refetching
  });
}

export default useProductSearch;
