/**
 * BOM Schema Tests - Optional Emission Factor (BUG-001 Fix)
 *
 * Tests for making emissionFactorId optional in BOM validation.
 *
 * Problem: Current schema requires ALL emission factors to be non-null, blocking wizard progression
 *          when component names don't match emission factors in database.
 *
 * Solution: Make emissionFactorId optional (nullable) while still encouraging users to select factors.
 *           Backend validation will catch incomplete data before calculation.
 *
 * Following TDD protocol - tests written BEFORE implementation fix.
 */

import { describe, it, expect } from 'vitest';
import { bomItemSchema, bomFormSchema } from '../bomSchema';
import type { BOMItemFormData } from '../bomSchema';

describe('BOM Schema - Optional Emission Factor (BUG-001 Fix)', () => {
  describe('bomItemSchema with null emissionFactorId', () => {
    it('should allow null emissionFactorId (user hasn\'t selected factor yet)', () => {
      const validItem: BOMItemFormData = {
        id: 'item_001',
        name: 'Cotton',
        quantity: 0.18,
        unit: 'kg',
        category: 'material',
        emissionFactorId: null, // Should be allowed
      };

      const result = bomItemSchema.safeParse(validItem);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.emissionFactorId).toBeNull();
      }
    });

    it('should allow valid emissionFactorId (UUID string)', () => {
      const validItem: BOMItemFormData = {
        id: 'item_002',
        name: 'Polyester',
        quantity: 0.015,
        unit: 'kg',
        category: 'material',
        emissionFactorId: 'ace03647af2b486dbf7579bd523c93e7', // Valid UUID
      };

      const result = bomItemSchema.safeParse(validItem);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.emissionFactorId).toBe('ace03647af2b486dbf7579bd523c93e7');
      }
    });

    it('should reject empty string emissionFactorId', () => {
      const invalidItem = {
        id: 'item_003',
        name: 'Nylon',
        quantity: 0.005,
        unit: 'kg',
        category: 'material',
        emissionFactorId: '', // Empty string should be rejected
      };

      const result = bomItemSchema.safeParse(invalidItem);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              path: ['emissionFactorId'],
              message: expect.stringContaining('emission factor'),
            }),
          ])
        );
      }
    });

    it('should allow undefined emissionFactorId (optional field)', () => {
      const validItem = {
        id: 'item_004',
        name: 'Plastic Abs',
        quantity: 0.002,
        unit: 'kg',
        category: 'material',
        // emissionFactorId is undefined (not provided)
      };

      const result = bomItemSchema.safeParse(validItem);

      expect(result.success).toBe(true);
    });
  });

  describe('bomFormSchema with mixed emission factors', () => {
    it('should allow BOM with some null and some valid emission factors', () => {
      const validForm = {
        items: [
          {
            id: 'item_001',
            name: 'Cotton',
            quantity: 0.18,
            unit: 'kg',
            category: 'material',
            emissionFactorId: 'ace03647af2b486dbf7579bd523c93e7', // Has factor
          },
          {
            id: 'item_002',
            name: 'Polyester',
            quantity: 0.015,
            unit: 'kg',
            category: 'material',
            emissionFactorId: null, // No factor yet
          },
          {
            id: 'item_003',
            name: 'Unknown Component',
            quantity: 0.005,
            unit: 'kg',
            category: 'other',
            emissionFactorId: null, // No factor (no match found)
          },
        ],
      };

      const result = bomFormSchema.safeParse(validForm);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.items).toHaveLength(3);
        expect(result.data.items[0].emissionFactorId).toBe('ace03647af2b486dbf7579bd523c93e7');
        expect(result.data.items[1].emissionFactorId).toBeNull();
        expect(result.data.items[2].emissionFactorId).toBeNull();
      }
    });

    it('should allow BOM with ALL null emission factors', () => {
      const validForm = {
        items: [
          {
            id: 'item_001',
            name: 'Component 1',
            quantity: 1.0,
            unit: 'kg',
            category: 'material',
            emissionFactorId: null,
          },
          {
            id: 'item_002',
            name: 'Component 2',
            quantity: 2.0,
            unit: 'kg',
            category: 'material',
            emissionFactorId: null,
          },
        ],
      };

      const result = bomFormSchema.safeParse(validForm);

      expect(result.success).toBe(true);
    });

    it('should allow BOM with ALL valid emission factors', () => {
      const validForm = {
        items: [
          {
            id: 'item_001',
            name: 'Cotton',
            quantity: 0.18,
            unit: 'kg',
            category: 'material',
            emissionFactorId: 'ace03647af2b486dbf7579bd523c93e7',
          },
          {
            id: 'item_002',
            name: 'Polyester',
            quantity: 0.015,
            unit: 'kg',
            category: 'material',
            emissionFactorId: 'ee31a862ddec4d9c895a7ec93b7abcf7',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validForm);

      expect(result.success).toBe(true);
    });
  });

  describe('Real-world scenario: Cotton T-Shirt BOM validation', () => {
    it('should validate Cotton T-Shirt BOM with all matched emission factors', () => {
      const tshirtBOM = {
        items: [
          {
            id: 'bom_001',
            name: 'Cotton',
            quantity: 0.18,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: 'ace03647af2b486dbf7579bd523c93e7',
          },
          {
            id: 'bom_002',
            name: 'Polyester',
            quantity: 0.015,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: 'ee31a862ddec4d9c895a7ec93b7abcf7',
          },
          {
            id: 'bom_003',
            name: 'Nylon',
            quantity: 0.005,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: '64babc8ae614486a84d4955538e59101',
          },
          {
            id: 'bom_004',
            name: 'Plastic Abs',
            quantity: 0.002,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: '4735bd1d108445c2ba3670a36b69687e',
          },
          {
            id: 'bom_005',
            name: 'Paper',
            quantity: 0.001,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: '964af9773c2a419da95d129c1e8bcce8',
          },
          {
            id: 'bom_006',
            name: 'Electricity Us',
            quantity: 2.5,
            unit: 'kWh',
            category: 'energy' as const,
            emissionFactorId: 'ddc0bdb30ff44b0db4f98d2017a81353',
          },
          {
            id: 'bom_007',
            name: 'Transport Truck',
            quantity: 0.1015,
            unit: 'tkm',
            category: 'transport' as const,
            emissionFactorId: '2ff62330b6a54ca5aeed2d89c6577d95',
          },
        ],
      };

      const result = bomFormSchema.safeParse(tshirtBOM);

      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.items).toHaveLength(7);
        // All items should have emission factor IDs
        result.data.items.forEach((item) => {
          expect(item.emissionFactorId).not.toBeNull();
          expect(item.emissionFactorId).toBeTruthy();
        });
      }
    });

    it('should validate Cotton T-Shirt BOM even if some emission factors are null', () => {
      const tshirtBOMPartialMatch = {
        items: [
          {
            id: 'bom_001',
            name: 'Cotton',
            quantity: 0.18,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: 'ace03647af2b486dbf7579bd523c93e7', // Matched
          },
          {
            id: 'bom_002',
            name: 'Polyester',
            quantity: 0.015,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: null, // Not matched (hypothetical scenario)
          },
          {
            id: 'bom_003',
            name: 'Nylon',
            quantity: 0.005,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: '64babc8ae614486a84d4955538e59101', // Matched
          },
        ],
      };

      const result = bomFormSchema.safeParse(tshirtBOMPartialMatch);

      // Should pass validation (emissionFactorId is now optional)
      expect(result.success).toBe(true);
    });
  });

  describe('Other validation rules still enforced', () => {
    it('should reject item with missing name', () => {
      const invalidItem = {
        id: 'item_001',
        name: '', // Empty name
        quantity: 1.0,
        unit: 'kg',
        category: 'material',
        emissionFactorId: null,
      };

      const result = bomItemSchema.safeParse(invalidItem);

      expect(result.success).toBe(false);
    });

    it('should reject item with zero quantity', () => {
      const invalidItem = {
        id: 'item_001',
        name: 'Cotton',
        quantity: 0, // Zero quantity
        unit: 'kg',
        category: 'material',
        emissionFactorId: null,
      };

      const result = bomItemSchema.safeParse(invalidItem);

      expect(result.success).toBe(false);
    });

    it('should reject item with missing unit', () => {
      const invalidItem = {
        id: 'item_001',
        name: 'Cotton',
        quantity: 1.0,
        unit: '', // Empty unit
        category: 'material',
        emissionFactorId: null,
      };

      const result = bomItemSchema.safeParse(invalidItem);

      expect(result.success).toBe(false);
    });

    it('should reject duplicate component names', () => {
      const invalidForm = {
        items: [
          {
            id: 'item_001',
            name: 'Cotton',
            quantity: 0.18,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: null,
          },
          {
            id: 'item_002',
            name: 'Cotton', // Duplicate name
            quantity: 0.015,
            unit: 'kg',
            category: 'material' as const,
            emissionFactorId: null,
          },
        ],
      };

      const result = bomFormSchema.safeParse(invalidForm);

      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.errors).toEqual(
          expect.arrayContaining([
            expect.objectContaining({
              message: 'Component names must be unique',
            }),
          ])
        );
      }
    });
  });
});
