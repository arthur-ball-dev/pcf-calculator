/**
 * Calculations API Service
 *
 * Handles API requests for PCF calculations.
 * Integrates with POST /api/v1/calculate and GET /api/v1/calculations/{id} endpoints.
 */

import client from './client';
import type {
  CalculationRequest,
  CalculationStartResponse,
  CalculationStatusResponse,
} from '@/types/api.types';

/**
 * Calculations API service
 */
export const calculationsAPI = {
  /**
   * Submit a new calculation request
   *
   * @param request - Calculation request with product_id and optional calculation_type
   * @returns Promise resolving to calculation ID and initial status
   */
  submit: async (
    request: CalculationRequest
  ): Promise<CalculationStartResponse> => {
    const response = await client.post<CalculationStartResponse>(
      '/api/v1/calculate',
      request
    );
    return response.data;
  },

  /**
   * Get status and results of a calculation
   *
   * @param calculationId - Calculation UUID
   * @returns Promise resolving to calculation status and results (if completed)
   */
  getStatus: async (
    calculationId: string
  ): Promise<CalculationStatusResponse> => {
    const response = await client.get<CalculationStatusResponse>(
      `/api/v1/calculations/${calculationId}`
    );
    return response.data;
  },
};
