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
 */

import { useQuery } from '@tanstack/react-query';

export interface EmissionFactor {
  id: number;
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
 */
async function fetchEmissionFactors(): Promise<EmissionFactor[]> {
  const response = await fetch('/api/v1/emission-factors?limit=1000');

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
