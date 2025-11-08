/**
 * Products API Service
 *
 * Handles API requests for product data from the backend.
 * Integrates with GET /api/v1/products endpoint.
 */

import axios from 'axios';
import type { Product } from '@/types/store.types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = 'v1';

/**
 * API Response for paginated products list
 */
interface ProductsResponse {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Fetch products from backend API
 *
 * @param params - Query parameters for filtering/pagination
 * @returns Promise resolving to array of products
 * @throws Error if API request fails
 */
export async function fetchProducts(params?: {
  limit?: number;
  offset?: number;
  is_finished_product?: boolean;
}): Promise<Product[]> {
  try {
    const response = await axios.get<ProductsResponse>(
      `${API_BASE_URL}/api/${API_VERSION}/products`,
      {
        params: {
          limit: params?.limit || 100,
          offset: params?.offset || 0,
          ...(params?.is_finished_product !== undefined && {
            is_finished_product: params.is_finished_product,
          }),
        },
        timeout: 10000, // 10 second timeout
      }
    );

    return response.data.items;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // Handle Axios-specific errors
      if (error.response) {
        // Server responded with error status
        throw new Error(
          `Failed to fetch products: ${error.response.status} ${error.response.statusText}`
        );
      } else if (error.request) {
        // No response received
        throw new Error(
          'Unable to reach server. Please check your network connection.'
        );
      } else {
        // Request setup error
        throw new Error(`Request error: ${error.message}`);
      }
    }

    // Re-throw unknown errors
    throw error;
  }
}

/**
 * Fetch single product by ID with BOM details
 *
 * @param productId - Product ID
 * @returns Promise resolving to product with BOM
 * @throws Error if product not found or request fails
 */
export async function fetchProductById(productId: number): Promise<Product> {
  try {
    const response = await axios.get<Product>(
      `${API_BASE_URL}/api/${API_VERSION}/products/${productId}`,
      {
        timeout: 10000,
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 404) {
        throw new Error(`Product ${productId} not found`);
      }

      if (error.response) {
        throw new Error(
          `Failed to fetch product: ${error.response.status} ${error.response.statusText}`
        );
      } else if (error.request) {
        throw new Error(
          'Unable to reach server. Please check your network connection.'
        );
      }
    }

    throw error;
  }
}
