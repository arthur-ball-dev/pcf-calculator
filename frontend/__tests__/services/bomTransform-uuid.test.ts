/**
 * BOM Transform UUID Handling Tests (TASK-FE-020 - Test-First)
 *
 * Tests UUID type system migration for emission factor IDs in BOM transformation.
 * These tests expect string types for emission factor IDs.
 *
 * CRITICAL: These tests are written BEFORE implementation (TDD Phase 1).
 * They will fail initially, proving they are valid tests.
 */

import { describe, test, expect } from 'vitest';
import { transformAPIBOMToFrontend } from '../../src/services/bomTransform';
import type { BOMItemResponse, EmissionFactorListItem } from '@/types/api.types';

describe('BOM Transform - UUID Handling', () => {
  describe('Emission Factor ID Type Validation', () => {
    test('should preserve emission factor IDs as UUID strings', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef-uuid-abc123def456',
          activity_name: 'Cotton',
          co2e_factor: 2.5,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'Ecoinvent',
          geography: 'Global',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-uuid-001',
          child_product_name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      expect(transformed[0].emissionFactorId).toBe('ef-uuid-abc123def456');
      expect(typeof transformed[0].emissionFactorId).toBe('string');
      expect(transformed[0].emissionFactorId).not.toBe(1); // Should NOT be coerced to number
    });

    test('should handle 32-character hex UUIDs', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
          activity_name: 'Steel',
          co2e_factor: 1.8,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-uuid-002',
          child_product_name: 'Steel',
          quantity: 2.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      expect(transformed[0].emissionFactorId).toBe('a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6');
      expect(transformed[0].emissionFactorId?.length).toBe(32);
      expect(typeof transformed[0].emissionFactorId).toBe('string');
    });

    test('should preserve null for unmatched components', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef-uuid-123',
          activity_name: 'Cotton',
          co2e_factor: 2.5,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'Ecoinvent',
          geography: 'Global',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-uuid-003',
          child_product_name: 'Unknown Material', // No matching emission factor
          quantity: 1.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      expect(transformed[0].emissionFactorId).toBeNull();
      expect(typeof transformed[0].emissionFactorId).not.toBe('number');
    });
  });

  describe('Multiple BOM Items with Different UUID Formats', () => {
    test('should handle mixed UUID formats in BOM', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef-short-001',
          activity_name: 'Material A',
          co2e_factor: 1.0,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2023,
        },
        {
          id: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
          activity_name: 'Material B',
          co2e_factor: 2.0,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'Ecoinvent',
          geography: 'Global',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-001',
          child_product_name: 'Material A',
          quantity: 1.0,
          unit: 'kg',
          notes: null,
        },
        {
          id: 'bom-002',
          child_product_name: 'Material B',
          quantity: 2.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      // First item - short UUID
      expect(transformed[0].emissionFactorId).toBe('ef-short-001');
      expect(typeof transformed[0].emissionFactorId).toBe('string');

      // Second item - 32-char hex UUID
      expect(transformed[1].emissionFactorId).toBe('a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6');
      expect(typeof transformed[1].emissionFactorId).toBe('string');
      expect(transformed[1].emissionFactorId?.length).toBe(32);
    });
  });

  describe('Case-Insensitive Matching Preserves UUID', () => {
    test('should match case-insensitively but preserve original UUID', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'UUID-ABC-123',
          activity_name: 'COTTON', // Uppercase in database
          co2e_factor: 2.5,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'Ecoinvent',
          geography: 'Global',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-001',
          child_product_name: 'cotton', // Lowercase in BOM
          quantity: 0.5,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      // Should match case-insensitively and preserve original UUID
      expect(transformed[0].emissionFactorId).toBe('UUID-ABC-123');
      expect(typeof transformed[0].emissionFactorId).toBe('string');
    });
  });

  describe('No parseInt Conversion', () => {
    test('should NOT convert string IDs to numbers using parseInt', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: '471fe408a2604386bae572d9fc9a6b5c', // Starts with numbers
          activity_name: 'Test Material',
          co2e_factor: 1.0,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-001',
          child_product_name: 'Test Material',
          quantity: 1.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      // Should preserve full UUID, NOT truncate to number
      expect(transformed[0].emissionFactorId).toBe('471fe408a2604386bae572d9fc9a6b5c');
      expect(transformed[0].emissionFactorId).not.toBe('471');
      expect(transformed[0].emissionFactorId).not.toBe(471);
      expect(typeof transformed[0].emissionFactorId).toBe('string');
    });
  });

  describe('Empty and Edge Cases', () => {
    test('should handle empty emission factors array', () => {
      const emissionFactors: EmissionFactorListItem[] = [];

      const bomData: BOMItemResponse[] = [
        {
          id: 'bom-001',
          child_product_name: 'Unknown Material',
          quantity: 1.0,
          unit: 'kg',
          notes: null,
        },
      ];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      expect(transformed[0].emissionFactorId).toBeNull();
      expect(typeof transformed[0].emissionFactorId).not.toBe('number');
    });

    test('should handle empty BOM array', () => {
      const emissionFactors: EmissionFactorListItem[] = [
        {
          id: 'ef-001',
          activity_name: 'Material',
          co2e_factor: 1.0,
          unit: 'kg CO2e/kg',
          category: 'material',
          data_source: 'EPA',
          geography: 'US',
          reference_year: 2023,
        },
      ];

      const bomData: BOMItemResponse[] = [];

      const transformed = transformAPIBOMToFrontend(bomData, emissionFactors);

      expect(transformed).toEqual([]);
    });
  });
});
