/**
 * Emission Factors API Service
 *
 * Handles API requests for emission factor data.
 * Integrates with GET /api/v1/emission-factors endpoint.
 *
 * Usage:
 * - Fetch all emission factors for BOM transformation (use large limit)
 * - Fetch paginated emission factors for UI display
 */

import client from './client';
import type {
  EmissionFactorListResponse,
  EmissionFactorListItem,
  PaginationParams,
  AttributionResponse,
} from '@/types/api.types';

/**
 * Emission Factors API service
 */
export const emissionFactorsAPI = {
  /**
   * Fetch paginated list of emission factors
   *
   * Default pagination:
   * - limit: 100 (sufficient for most use cases)
   * - offset: 0
   *
   * For BOM transformation, use large limit (e.g., 1000) to fetch all factors at once.
   *
   * @param params - Pagination parameters
   * @returns Promise resolving to array of emission factors
   * @throws APIError if request fails
   */
  list: async (params?: PaginationParams): Promise<EmissionFactorListItem[]> => {
    const response = await client.get<EmissionFactorListResponse>(
      '/api/v1/emission-factors',
      {
        params: {
          limit: params?.limit || 100,
          offset: params?.offset || 0,
        },
      }
    );

    return response.data.items;
  },

  /**
   * Fetch data source attributions
   *
   * Returns license and attribution information for all active data sources.
   * Use this to display required attributions in the UI.
   *
   * @returns Promise resolving to attribution response
   * @throws APIError if request fails
   */
  getAttributions: async (): Promise<AttributionResponse> => {
    const response = await client.get<AttributionResponse>(
      '/api/v1/attributions'
    );
    return response.data;
  },
};
