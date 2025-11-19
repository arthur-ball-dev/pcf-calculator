/**
 * Emission Factors API Service Tests
 *
 * Tests for emission factors API integration.
 * Following TDD protocol - tests written BEFORE implementation.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { emissionFactorsAPI } from '../emissionFactors';
import client from '../client';
import type { EmissionFactorListResponse } from '@/types/api.types';

// Mock the axios client
vi.mock('../client');

describe('emissionFactorsAPI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('should fetch emission factors with default pagination', async () => {
      const mockResponse: EmissionFactorListResponse = {
        items: [
          {
            id: '1',
            activity_name: 'Cotton',
            category: 'materials',
            co2e_factor: 5.89,
            unit: 'kg CO2e/kg',
            data_source: 'Ecoinvent',
            geography: 'Global',
            reference_year: 2020,
            data_quality_rating: 4,
            created_at: '2024-01-01T00:00:00Z',
          },
          {
            id: '2',
            activity_name: 'Polyester',
            category: 'materials',
            co2e_factor: 3.36,
            unit: 'kg CO2e/kg',
            data_source: 'Ecoinvent',
            geography: 'Global',
            reference_year: 2020,
            data_quality_rating: 4,
            created_at: '2024-01-01T00:00:00Z',
          },
        ],
        total: 2,
        limit: 100,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await emissionFactorsAPI.list();

      expect(client.get).toHaveBeenCalledWith('/api/v1/emission-factors', {
        params: {
          limit: 100,
          offset: 0,
        },
      });
      expect(result).toEqual(mockResponse.items);
      expect(result).toHaveLength(2);
    });

    it('should fetch emission factors with custom pagination params', async () => {
      const mockResponse: EmissionFactorListResponse = {
        items: [],
        total: 50,
        limit: 20,
        offset: 10,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await emissionFactorsAPI.list({ limit: 20, offset: 10 });

      expect(client.get).toHaveBeenCalledWith('/api/v1/emission-factors', {
        params: {
          limit: 20,
          offset: 10,
        },
      });
      expect(result).toEqual([]);
    });

    it('should fetch all emission factors with large limit', async () => {
      const mockItems = Array.from({ length: 100 }, (_, i) => ({
        id: String(i + 1),
        activity_name: `Factor ${i + 1}`,
        category: 'materials',
        co2e_factor: 1.0 + i * 0.1,
        unit: 'kg CO2e/kg',
        data_source: 'Test',
        geography: 'Global',
        reference_year: 2020,
        data_quality_rating: 4,
        created_at: '2024-01-01T00:00:00Z',
      }));

      const mockResponse: EmissionFactorListResponse = {
        items: mockItems,
        total: 100,
        limit: 1000,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await emissionFactorsAPI.list({ limit: 1000 });

      expect(client.get).toHaveBeenCalledWith('/api/v1/emission-factors', {
        params: {
          limit: 1000,
          offset: 0,
        },
      });
      expect(result).toHaveLength(100);
    });

    it('should handle empty response', async () => {
      const mockResponse: EmissionFactorListResponse = {
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await emissionFactorsAPI.list();

      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });

    it('should handle API errors gracefully', async () => {
      const mockError = new Error('Network error');
      vi.mocked(client.get).mockRejectedValue(mockError);

      await expect(emissionFactorsAPI.list()).rejects.toThrow('Network error');
    });

    it('should handle server errors (500)', async () => {
      const mockError = new Error('Internal Server Error');
      vi.mocked(client.get).mockRejectedValue(mockError);

      await expect(emissionFactorsAPI.list()).rejects.toThrow(
        'Internal Server Error'
      );
    });
  });

  describe('Edge Cases', () => {
    it('should handle invalid response structure', async () => {
      // Response missing required fields
      const invalidResponse = {
        // Missing items array
        total: 0,
        limit: 100,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: invalidResponse });

      const result = await emissionFactorsAPI.list();

      // Should return undefined or handle gracefully
      expect(result).toBeUndefined();
    });

    it('should handle null pagination params', async () => {
      const mockResponse: EmissionFactorListResponse = {
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await emissionFactorsAPI.list({});

      expect(client.get).toHaveBeenCalledWith('/api/v1/emission-factors', {
        params: {
          limit: 100,
          offset: 0,
        },
      });
      expect(result).toEqual([]);
    });

    it('should handle very large offset (pagination edge case)', async () => {
      const mockResponse: EmissionFactorListResponse = {
        items: [],
        total: 1000,
        limit: 100,
        offset: 2000, // Offset beyond total
      };

      vi.mocked(client.get).mockResolvedValue({ data: mockResponse });

      const result = await emissionFactorsAPI.list({ offset: 2000 });

      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });
  });
});
