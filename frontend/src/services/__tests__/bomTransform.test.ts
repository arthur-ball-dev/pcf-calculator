/**
 * BOM Transformation Service Tests
 *
 * Tests for transforming API BOM format to frontend format with emission factor mapping.
 * Following TDD protocol - tests written BEFORE implementation.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  transformAPIBOMToFrontend,
  buildEmissionFactorLookup,
  inferCategory,
} from '../bomTransform';
import type { BOMItemResponse, EmissionFactorListItem } from '@/types/api.types';

describe('bomTransform Service', () => {
  // Mock data
  let mockEmissionFactors: EmissionFactorListItem[];
  let mockAPIBOM: BOMItemResponse[];

  beforeEach(() => {
    // Setup mock emission factors
    mockEmissionFactors = [
      {
        id: '1',
        activity_name: 'Cotton',
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
        co2e_factor: 3.36,
        unit: 'kg CO2e/kg',
        data_source: 'Ecoinvent',
        geography: 'Global',
        reference_year: 2020,
        data_quality_rating: 4,
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: '3',
        activity_name: 'Electricity',
        co2e_factor: 0.5,
        unit: 'kg CO2e/kWh',
        data_source: 'EPA',
        geography: 'US',
        reference_year: 2021,
        data_quality_rating: 5,
        created_at: '2024-01-01T00:00:00Z',
      },
    ];

    // Setup mock API BOM
    mockAPIBOM = [
      {
        id: 'bom_001',
        child_product_id: 'prod_cotton',
        child_product_name: 'Cotton',
        quantity: 0.18,
        unit: 'kg',
        notes: null,
      },
      {
        id: 'bom_002',
        child_product_id: 'prod_polyester',
        child_product_name: 'Polyester',
        quantity: 0.02,
        unit: 'kg',
        notes: 'Collar trim',
      },
    ];
  });

  describe('buildEmissionFactorLookup', () => {
    it('should create a case-insensitive lookup map from emission factors', () => {
      const lookup = buildEmissionFactorLookup(mockEmissionFactors);

      expect(lookup.size).toBe(3);
      expect(lookup.get('cotton')).toBeDefined();
      expect(lookup.get('cotton')?.id).toBe('1');
      expect(lookup.get('polyester')).toBeDefined();
      expect(lookup.get('polyester')?.id).toBe('2');
      expect(lookup.get('electricity')).toBeDefined();
      expect(lookup.get('electricity')?.id).toBe('3');
    });

    it('should handle case-insensitive lookups', () => {
      const lookup = buildEmissionFactorLookup(mockEmissionFactors);

      expect(lookup.get('COTTON')).toBeUndefined(); // Map keys are lowercase
      expect(lookup.get('cotton')?.activity_name).toBe('Cotton');
      expect(lookup.get('polyester')?.activity_name).toBe('Polyester');
    });

    it('should handle multiple emission factors with same activity name (keep first)', () => {
      const duplicateFactors: EmissionFactorListItem[] = [
        ...mockEmissionFactors,
        {
          id: '4',
          activity_name: 'Cotton', // Duplicate
          co2e_factor: 6.0,
          unit: 'kg CO2e/kg',
          data_source: 'DEFRA',
          geography: 'UK',
          reference_year: 2021,
          data_quality_rating: 3,
          created_at: '2024-01-02T00:00:00Z',
        },
      ];

      const lookup = buildEmissionFactorLookup(duplicateFactors);

      expect(lookup.size).toBe(3); // Still 3 unique names
      expect(lookup.get('cotton')?.id).toBe('1'); // First one kept
      expect(lookup.get('cotton')?.data_source).toBe('Ecoinvent');
    });

    it('should handle empty emission factors array', () => {
      const lookup = buildEmissionFactorLookup([]);

      expect(lookup.size).toBe(0);
    });
  });

  describe('inferCategory', () => {
    it('should use emission factor category if available (material)', () => {
      const emissionFactor: EmissionFactorListItem = {
        ...mockEmissionFactors[0],
        id: '1',
        activity_name: 'Cotton',
      };

      const category = inferCategory(emissionFactor, 'Cotton');

      expect(category).toBe('material');
    });

    it('should default to "material" for material-related names when no category', () => {
      const emissionFactor: EmissionFactorListItem = {
        ...mockEmissionFactors[0],
        id: '1',
        activity_name: 'Cotton',
      };

      const category = inferCategory(emissionFactor, 'Cotton');

      expect(category).toBe('material');
    });

    it('should infer "energy" from component name containing energy keywords', () => {
      const category = inferCategory(null, 'Electricity Grid');

      expect(category).toBe('energy');
    });

    it('should infer "transport" from component name containing transport keywords', () => {
      const category = inferCategory(null, 'Truck Transport');

      expect(category).toBe('transport');
    });

    it('should default to "other" when no emission factor and no keyword match', () => {
      const category = inferCategory(null, 'Unknown Component');

      expect(category).toBe('other');
    });
  });

  describe('transformAPIBOMToFrontend', () => {
    it('should transform API BOM to frontend format with emission factor IDs mapped', () => {
      const result = transformAPIBOMToFrontend(mockAPIBOM, mockEmissionFactors);

      expect(result).toHaveLength(2);

      // First item
      expect(result[0]).toEqual({
        id: 'bom_001',
        name: 'Cotton',
        quantity: 0.18,
        unit: 'kg',
        category: 'material',
        emissionFactorId: "1", // Mapped from emission factor id
        notes: undefined,
      });

      // Second item
      expect(result[1]).toEqual({
        id: 'bom_002',
        name: 'Polyester',
        quantity: 0.02,
        unit: 'kg',
        category: 'material',
        emissionFactorId: "2",
        notes: 'Collar trim',
      });
    });

    it('should handle missing emission factor by setting emissionFactorId to null', () => {
      const bomWithUnknown: BOMItemResponse[] = [
        {
          id: 'bom_003',
          child_product_id: 'prod_unknown',
          child_product_name: 'Unknown Material',
          quantity: 1.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomWithUnknown, mockEmissionFactors);

      expect(result).toHaveLength(1);
      expect(result[0]).toEqual({
        id: 'bom_003',
        name: 'Unknown Material',
        quantity: 1.0,
        unit: 'kg',
        category: 'other', // Default when no match
        emissionFactorId: null,
        notes: undefined,
      });
    });

    it('should handle empty BOM array', () => {
      const result = transformAPIBOMToFrontend([], mockEmissionFactors);

      expect(result).toEqual([]);
    });

    it('should handle case-insensitive matching for component names', () => {
      const bomWithDifferentCase: BOMItemResponse[] = [
        {
          id: 'bom_004',
          child_product_id: 'prod_cotton',
          child_product_name: 'cotton', // lowercase
          quantity: 0.5,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_005',
          child_product_id: 'prod_polyester',
          child_product_name: 'POLYESTER', // uppercase
          quantity: 0.1,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomWithDifferentCase, mockEmissionFactors);

      expect(result).toHaveLength(2);
      expect(result[0].emissionFactorId).toBe('1'); // Cotton matched
      expect(result[1].emissionFactorId).toBe('2'); // Polyester matched
    });

    it('should preserve original BOM item ID from API', () => {
      const result = transformAPIBOMToFrontend(mockAPIBOM, mockEmissionFactors);

      expect(result[0].id).toBe('bom_001');
      expect(result[1].id).toBe('bom_002');
    });

    it('should convert notes from null to undefined', () => {
      const result = transformAPIBOMToFrontend(mockAPIBOM, mockEmissionFactors);

      expect(result[0].notes).toBeUndefined(); // Was null in API
      expect(result[1].notes).toBe('Collar trim'); // Had value
    });

    it('should handle invalid data gracefully (skip invalid items)', () => {
      const bomWithInvalid: BOMItemResponse[] = [
        {
          id: 'bom_006',
          child_product_id: 'prod_valid',
          child_product_name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_007',
          child_product_id: 'prod_invalid',
          child_product_name: '', // Empty name
          quantity: 0,
          unit: '',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomWithInvalid, mockEmissionFactors);

      // Should still process valid item
      expect(result.length).toBeGreaterThanOrEqual(1);
      expect(result[0].name).toBe('Cotton');
    });

    it('should handle partial emission factor matches', () => {
      const mixedBOM: BOMItemResponse[] = [
        {
          id: 'bom_008',
          child_product_id: 'prod_cotton',
          child_product_name: 'Cotton',
          quantity: 0.18,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_009',
          child_product_id: 'prod_unknown',
          child_product_name: 'Unknown Component',
          quantity: 0.5,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_010',
          child_product_id: 'prod_polyester',
          child_product_name: 'Polyester',
          quantity: 0.02,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(mixedBOM, mockEmissionFactors);

      expect(result).toHaveLength(3);
      expect(result[0].emissionFactorId).toBe('1'); // Cotton - matched
      expect(result[1].emissionFactorId).toBeNull(); // Unknown - not matched
      expect(result[2].emissionFactorId).toBe('2'); // Polyester - matched
    });

    it('should infer energy category for electricity components', () => {
      const energyBOM: BOMItemResponse[] = [
        {
          id: 'bom_011',
          child_product_id: 'prod_electricity',
          child_product_name: 'Electricity',
          quantity: 10,
          unit: 'kWh',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(energyBOM, mockEmissionFactors);

      expect(result).toHaveLength(1);
      expect(result[0].category).toBe('energy');
      expect(result[0].emissionFactorId).toBe('3'); // Matched to Electricity emission factor
    });
  });

  describe('Edge Cases', () => {
    it('should handle emission factors with no activity_name', () => {
      const factorsWithMissingName: EmissionFactorListItem[] = [
        {
          id: '99',
          activity_name: '', // Empty
          co2e_factor: 1.0,
          unit: 'kg CO2e/kg',
          data_source: 'Test',
          geography: 'Global',
          reference_year: null,
          data_quality_rating: null,
          created_at: '2024-01-01T00:00:00Z',
        },
        ...mockEmissionFactors,
      ];

      const lookup = buildEmissionFactorLookup(factorsWithMissingName);

      // Empty name should be skipped or stored with empty key
      expect(lookup.has('')).toBe(true); // Empty string key exists
      expect(lookup.size).toBe(4); // All factors stored
    });

    it('should handle BOM items with null or undefined unit', () => {
      const bomWithNullUnit: BOMItemResponse[] = [
        {
          id: 'bom_012',
          child_product_id: 'prod_test',
          child_product_name: 'Cotton',
          quantity: 1.0,
          unit: null, // Null unit
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomWithNullUnit, mockEmissionFactors);

      expect(result).toHaveLength(1);
      expect(result[0].unit).toBe(''); // Converted null to empty string or handled
    });
  });
});
