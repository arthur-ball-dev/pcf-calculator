/**
 * API Service Layer - Main Export
 *
 * Centralized API service providing:
 * - Products API (list, detail)
 * - Calculations API (submit, poll status)
 * - Error handling (APIError)
 *
 * @example
 * import api from '@/services/api';
 *
 * // Fetch products
 * const products = await api.products.list();
 *
 * // Submit calculation
 * const result = await api.calculations.submit({ product_id: 'prod-123' });
 *
 * // Poll calculation status
 * const status = await api.calculations.getStatus(result.calculation_id);
 */

import { productsAPI } from './products';
import { calculationsAPI } from './calculations';

export { APIError } from './errors';
export type {
  ProductListItem,
  ProductDetail,
  BOMItemResponse,
  CalculationRequest,
  CalculationStartResponse,
  CalculationStatusResponse,
  APIErrorCode,
} from '@/types/api.types';

/**
 * Main API service object
 */
const api = {
  products: productsAPI,
  calculations: calculationsAPI,
};

export default api;
