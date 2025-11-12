/**
 * useEmissionFactors Hook
 *
 * Custom hook for fetching emission factors from the API.
 * Uses React Query for caching and state management.
 *
 * Returns:
 * - data: Array of emission factors
 * - isLoading: Loading state
 * - error: Error state
 *
 * UPDATED: TASK-FE-020 - UUID type system migration
 * - EmissionFactor.id: string (was number)
 * - Preserves full UUID strings from API responses
 */

import { useQuery } from '@tanstack/react-query';

export interface EmissionFactor {
  id: string; // UPDATED: number → string (UUID)
  activity_name: string;
  co2e_factor: number;
  unit: string;
  category: 'material' | 'energy' | 'transport' | 'other';
  data_source: string;
  geography: string;
  reference_year: number;
}

/**
 * Fetch emission factors from API
 *
 * Uses full URL to backend API server (http://localhost:8000)
 * to avoid issues with relative paths and Vite dev server
 */
async function fetchEmissionFactors(): Promise<EmissionFactor[]> {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const response = await fetch(`${API_BASE_URL}/api/v1/emission-factors?limit=1000`);

  if (!response.ok) {
    throw new Error('Failed to fetch emission factors');
  }

  const data = await response.json();
  return data.items || [];
}

/**
 * Hook to fetch and cache emission factors
 */
export function useEmissionFactors() {
  return useQuery({
    queryKey: ['emission-factors'],
    queryFn: fetchEmissionFactors,
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
  });
}
