/**
 * Products API Service
 *
 * Handles API requests for product data from the backend.
 * Integrates with GET /api/v1/products endpoints.
 */

import client from './client';
import { APIError } from './errors';
import type {
  ProductListResponse,
  ProductDetail,
  PaginationParams,
} from '@/types/api.types';

/**
 * Search parameters for product search endpoint
 */
export interface ProductSearchParams extends PaginationParams {
  query?: string;
  is_finished_product?: boolean;
  has_bom?: boolean;
  category_id?: string;
  industry?: string;
}

/**
 * Search response from backend
 */
interface ProductSearchResponse {
  items: ProductDetail[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/**
 * Products API service
 */
export const productsAPI = {
  /**
   * Fetch paginated list of products
   *
   * @param params - Pagination and filter parameters
   * @returns Promise resolving to array of products
   */
  list: async (
    params?: PaginationParams & { is_finished_product?: boolean }
  ): Promise<ProductDetail[]> => {
    const response = await client.get<ProductListResponse>('/api/v1/products', {
      params: {
        limit: params?.limit || 100,
        offset: params?.offset || 0,
        // Backend expects 'is_finished' not 'is_finished_product'
        ...(params?.is_finished_product !== undefined && {
          is_finished: params.is_finished_product,
        }),
      },
    });

    return response.data.items as unknown as ProductDetail[];
  },

  /**
   * Search products with full-text search
   *
   * @param params - Search and filter parameters
   * @returns Promise resolving to search results with total count
   */
  search: async (
    params?: ProductSearchParams
  ): Promise<{ items: ProductDetail[]; total: number; has_more: boolean }> => {
    const response = await client.get<ProductSearchResponse>('/api/v1/products/search', {
      params: {
        limit: params?.limit || 50,
        offset: params?.offset || 0,
        ...(params?.query && { query: params.query }),
        ...(params?.is_finished_product !== undefined && {
          is_finished_product: params.is_finished_product,
        }),
        ...(params?.has_bom !== undefined && {
          has_bom: params.has_bom,
        }),
        ...(params?.category_id && { category_id: params.category_id }),
        ...(params?.industry && { industry: params.industry }),
      },
    });

    return {
      items: response.data.items,
      total: response.data.total,
      has_more: response.data.has_more,
    };
  },

  /**
   * Fetch single product by ID with BOM details
   *
   * @param productId - Product UUID
   * @returns Promise resolving to product with BOM
   * @throws APIError if product not found
   */
  getById: async (productId: string): Promise<ProductDetail> => {
    try {
      const response = await client.get<ProductDetail>(
        `/api/v1/products/${productId}`
      );
      return response.data;
    } catch (error) {
      // Re-throw APIError from interceptor
      if (error instanceof APIError && error.code === 'NOT_FOUND') {
        throw new APIError('NOT_FOUND', 'Product not found', error);
      }
      throw error;
    }
  },
};

/**
 * Legacy export for ProductSelector component compatibility
 * This export provides a direct function reference for components
 * that import fetchProducts instead of productsAPI.list
 */
export const fetchProducts = productsAPI.list;
