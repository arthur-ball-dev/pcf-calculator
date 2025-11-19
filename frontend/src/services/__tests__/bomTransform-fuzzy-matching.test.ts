/**
 * BOM Transformation Service - Fuzzy Matching Tests
 *
 * BUG-001 FIX: Tests for improved name matching between BOM components and emission factors
 *
 * Problem: BOM components use "Plastic Abs" (spaces, capitalized)
 *          Emission factors use "plastic_abs" (underscores, lowercase)
 *          Current exact match fails, causing emissionFactorId to be null
 *
 * Solution: Normalize both component names and emission factor names by:
 *   - Converting to lowercase
 *   - Trimming whitespace
 *   - Replacing spaces with underscores
 *   - Collapsing multiple spaces to single underscore
 *
 * Following TDD protocol - tests written BEFORE implementation fix.
 */

import { describe, it, expect } from 'vitest';
import {
  transformAPIBOMToFrontend,
  buildEmissionFactorLookup,
} from '../bomTransform';
import type { BOMItemResponse, EmissionFactorListItem } from '@/types/api.types';

describe('BOM Transform - Fuzzy Matching (BUG-001 Fix)', () => {
  describe('Real-world scenario: Cotton T-Shirt BOM matching', () => {
    it('should match "Plastic Abs" component to "plastic_abs" emission factor', () => {
      // Real data from database
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic_abs',
          activity_name: 'plastic_abs', // Database format: lowercase with underscore
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic',
          child_product_name: 'Plastic Abs', // BOM format: Capitalized with space
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result).toHaveLength(1);
      expect(result[0].emissionFactorId).toBe('ef_plastic_abs'); // Should match!
      expect(result[0].emissionFactorId).not.toBeNull(); // Key assertion for BUG-001
    });

    it('should match "Electricity Us" component to "electricity_us" emission factor', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_electricity_us',
          activity_name: 'electricity_us',
      category: 'materials',
          co2e_factor: 0.4,
          unit: 'kg CO2e/kWh',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2021,
          data_quality_rating: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_002',
          child_product_id: 'prod_electricity',
          child_product_name: 'Electricity Us', // Capitalized with space
          quantity: 2.5,
          unit: 'kWh',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result).toHaveLength(1);
      expect(result[0].emissionFactorId).toBe('ef_electricity_us');
      expect(result[0].emissionFactorId).not.toBeNull();
      expect(result[0].category).toBe('energy'); // Should infer correct category
    });

    it('should match "Transport Truck" component to "transport_truck" emission factor', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_transport_truck',
          activity_name: 'transport_truck',
      category: 'materials',
          co2e_factor: 0.1,
          unit: 'kg CO2e/tkm',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_003',
          child_product_id: 'prod_transport',
          child_product_name: 'Transport Truck',
          quantity: 0.1015,
          unit: 'tkm',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result).toHaveLength(1);
      expect(result[0].emissionFactorId).toBe('ef_transport_truck');
      expect(result[0].emissionFactorId).not.toBeNull();
      expect(result[0].category).toBe('transport');
    });

    it('should match all components in Cotton T-Shirt BOM', () => {
      // Full emission factors from database
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_cotton',
          activity_name: 'cotton',
      category: 'materials',
          co2e_factor: 5.89,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_polyester',
          activity_name: 'polyester',
      category: 'materials',
          co2e_factor: 6.4,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_nylon',
          activity_name: 'nylon',
      category: 'materials',
          co2e_factor: 7.5,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_plastic_abs',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_paper',
          activity_name: 'paper',
      category: 'materials',
          co2e_factor: 1.3,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_electricity_us',
          activity_name: 'electricity_us',
      category: 'materials',
          co2e_factor: 0.4,
          unit: 'kg CO2e/kWh',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2021,
          data_quality_rating: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_transport_truck',
          activity_name: 'transport_truck',
      category: 'materials',
          co2e_factor: 0.1,
          unit: 'kg CO2e/tkm',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      // Full BOM from database (Cotton T-Shirt)
      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_cotton',
          child_product_name: 'Cotton', // No space/underscore variation
          quantity: 0.18,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_002',
          child_product_id: 'prod_polyester',
          child_product_name: 'Polyester', // No space/underscore variation
          quantity: 0.015,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_003',
          child_product_id: 'prod_nylon',
          child_product_name: 'Nylon', // No space/underscore variation
          quantity: 0.005,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_004',
          child_product_id: 'prod_plastic',
          child_product_name: 'Plastic Abs', // SPACE - needs matching
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_005',
          child_product_id: 'prod_paper',
          child_product_name: 'Paper', // No space/underscore variation
          quantity: 0.001,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom_006',
          child_product_id: 'prod_electricity',
          child_product_name: 'Electricity Us', // SPACE - needs matching
          quantity: 2.5,
          unit: 'kWh',
          notes: null,
        },
        {
          id: 'bom_007',
          child_product_id: 'prod_transport',
          child_product_name: 'Transport Truck', // SPACE - needs matching
          quantity: 0.1015,
          unit: 'tkm',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result).toHaveLength(7);

      // ALL items should have emission factor IDs (no null values!)
      expect(result[0].emissionFactorId).toBe('ef_cotton');
      expect(result[1].emissionFactorId).toBe('ef_polyester');
      expect(result[2].emissionFactorId).toBe('ef_nylon');
      expect(result[3].emissionFactorId).toBe('ef_plastic_abs'); // BUG-001 fix target
      expect(result[4].emissionFactorId).toBe('ef_paper');
      expect(result[5].emissionFactorId).toBe('ef_electricity_us'); // BUG-001 fix target
      expect(result[6].emissionFactorId).toBe('ef_transport_truck'); // BUG-001 fix target

      // No null emission factor IDs
      const nullFactors = result.filter(item => item.emissionFactorId === null);
      expect(nullFactors).toHaveLength(0);
    });
  });

  describe('buildEmissionFactorLookup normalization', () => {
    it('should normalize emission factor names to lowercase with underscores', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_1',
          activity_name: 'plastic_abs', // Already normalized
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 'ef_2',
          activity_name: 'electricity_us', // Already normalized
      category: 'materials',
          co2e_factor: 0.4,
          unit: 'kg CO2e/kWh',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2021,
          data_quality_rating: 5,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const lookup = buildEmissionFactorLookup(emissionFactors);

      // Keys should be normalized (lowercase, underscores preserved)
      expect(lookup.has('plastic_abs')).toBe(true);
      expect(lookup.has('electricity_us')).toBe(true);

      // Verify lookup retrieves correct factors
      expect(lookup.get('plastic_abs')?.id).toBe('ef_1');
      expect(lookup.get('electricity_us')?.id).toBe('ef_2');
    });

    it('should handle emission factors with spaces (convert to underscores)', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_1',
          activity_name: 'Plastic ABS', // Spaces, capitalized
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const lookup = buildEmissionFactorLookup(emissionFactors);

      // Should normalize to "plastic_abs"
      expect(lookup.has('plastic_abs')).toBe(true);
      expect(lookup.get('plastic_abs')?.id).toBe('ef_1');
    });
  });

  describe('Case sensitivity handling', () => {
    it('should match components regardless of case (all uppercase)', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic',
          child_product_name: 'PLASTIC ABS', // All uppercase
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBe('ef_plastic');
      expect(result[0].emissionFactorId).not.toBeNull();
    });

    it('should match components regardless of case (all lowercase)', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic',
          child_product_name: 'plastic abs', // All lowercase
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBe('ef_plastic');
      expect(result[0].emissionFactorId).not.toBeNull();
    });

    it('should match components with mixed case', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic',
          child_product_name: 'pLaStIc AbS', // Mixed case
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBe('ef_plastic');
      expect(result[0].emissionFactorId).not.toBeNull();
    });
  });

  describe('Whitespace handling', () => {
    it('should trim leading and trailing spaces from component names', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_cotton',
          activity_name: 'cotton',
      category: 'materials',
          co2e_factor: 5.89,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_cotton',
          child_product_name: '  Cotton  ', // Leading and trailing spaces
          quantity: 0.18,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBe('ef_cotton');
      expect(result[0].emissionFactorId).not.toBeNull();
    });

    it('should collapse multiple consecutive spaces to single underscore', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic',
          child_product_name: 'Plastic   Abs', // Multiple spaces
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBe('ef_plastic');
      expect(result[0].emissionFactorId).not.toBeNull();
    });

    it('should handle tabs and other whitespace characters', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic',
          child_product_name: 'Plastic\tAbs', // Tab character
          quantity: 0.002,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBe('ef_plastic');
      expect(result[0].emissionFactorId).not.toBeNull();
    });
  });

  describe('Edge cases', () => {
    it('should still return null for genuinely unmatched components', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_cotton',
          activity_name: 'cotton',
      category: 'materials',
          co2e_factor: 5.89,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_unknown',
          child_product_name: 'Unobtanium', // Not in emission factors
          quantity: 1.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      expect(result[0].emissionFactorId).toBeNull(); // Should remain null
      expect(result[0].category).toBe('other'); // Default category
    });

    it('should handle component names that are similar but not exact matches', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef_plastic_abs',
          activity_name: 'plastic_abs',
      category: 'materials',
          co2e_factor: 3.8,
          unit: 'kg CO2e/kg',
          data_source: 'EPA',
          geography: 'GLO',
          reference_year: 2020,
          data_quality_rating: 4,
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const bomItems: BOMItemResponse[] = [
        {
          id: 'bom_001',
          child_product_id: 'prod_plastic_pet',
          child_product_name: 'Plastic PET', // Different plastic type
          quantity: 0.05,
          unit: 'kg',
          notes: null,
        },
      ];

      const result = transformAPIBOMToFrontend(bomItems, emissionFactors);

      // Should NOT match (plastic_pet !== plastic_abs)
      expect(result[0].emissionFactorId).toBeNull();
    });
  });
});
