/**
 * BOM Schema UUID Validation Tests (TASK-FE-020 - Test-First)
 *
 * Tests Zod schema validation for UUID types in BOM forms.
 * These tests expect string types for emission factor IDs.
 *
 * CRITICAL: These tests are written BEFORE implementation (TDD Phase 1).
 * They will fail initially, proving they are valid tests.
 */

import { describe, test, expect } from 'vitest';
import { bomFormSchema, bomItemSchema } from '../../src/schemas/bomSchema';

describe('BOM Schema - UUID Validation', () => {
  describe('Emission Factor ID Type Validation', () => {
    test('should validate emission factor IDs as strings', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: 'ef-uuid-123abc',
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(typeof result.data.items[0].emissionFactorId).toBe('string');
      }
    });

    test('should accept 32-character hex UUIDs', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.items[0].emissionFactorId).toBe(
          'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6'
        );
        expect(result.data.items[0].emissionFactorId.length).toBe(32);
      }
    });

    test('should accept UUIDs starting with numeric characters', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: '471fe408a2604386bae572d9fc9a6b5c',
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.items[0].emissionFactorId).toBe(
          '471fe408a2604386bae572d9fc9a6b5c'
        );
        expect(result.data.items[0].emissionFactorId).not.toBe('471');
      }
    });

    test('should reject number types for emission factor ID', () => {
      const invalidData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: 12345, // WRONG: Should be string
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find((issue) =>
          issue.path.includes('emissionFactorId')
        );
        expect(error).toBeDefined();
        expect(error?.message).toMatch(/string/i);
      }
    });
  });

  describe('Single BOM Item Schema', () => {
    test('should validate emission factor ID as string in single item', () => {
      const validItem = {
        id: 'bom-001',
        name: 'Cotton',
        quantity: 0.5,
        unit: 'kg',
        emissionFactorId: 'ef-cotton-uuid-123',
        category: 'material',
      };

      const result = bomItemSchema.safeParse(validItem);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(typeof result.data.emissionFactorId).toBe('string');
      }
    });

    test('should reject integer emission factor ID', () => {
      const invalidItem = {
        id: 'bom-001',
        name: 'Cotton',
        quantity: 0.5,
        unit: 'kg',
        emissionFactorId: 1, // WRONG: Should be string
        category: 'material',
      };

      const result = bomItemSchema.safeParse(invalidItem);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toMatch(/string/i);
      }
    });
  });

  describe('Multiple Items with Different UUID Formats', () => {
    test('should validate mixed UUID formats in multiple items', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.0,
            unit: 'kg',
            emissionFactorId: 'ef-short-001',
            category: 'material',
          },
          {
            id: 'bom-002',
            name: 'Material B',
            quantity: 2.0,
            unit: 'kg',
            emissionFactorId: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
            category: 'energy',
          },
          {
            id: 'bom-003',
            name: 'Material C',
            quantity: 3.0,
            unit: 'kg',
            emissionFactorId: '471fe408a2604386bae572d9fc9a6b5c',
            category: 'transport',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(typeof result.data.items[0].emissionFactorId).toBe('string');
        expect(typeof result.data.items[1].emissionFactorId).toBe('string');
        expect(typeof result.data.items[2].emissionFactorId).toBe('string');
        expect(result.data.items[1].emissionFactorId.length).toBe(32);
        expect(result.data.items[2].emissionFactorId.length).toBe(32);
      }
    });
  });

  describe('Null Handling', () => {
    test('should allow null emission factor ID (user to select later)', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: null,
            category: 'other',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      // Schema allows null emissionFactorId for user to select later
      expect(result.success).toBe(true);
    });
  });

  describe('UUID Format Validation (Optional Enhancement)', () => {
    test('should accept valid UUID format (32-char hex)', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept UUID with uppercase hex characters', () => {
      const validData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: 'A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6',
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(validData);
      expect(result.success).toBe(true);
    });

    test('should accept UUID-like strings (backend compatibility)', () => {
      // Backend may use various UUID formats
      const validFormats = [
        'ef-uuid-123',
        'calc-abc-def',
        'prod-001-test',
        '123-456-789',
      ];

      for (const uuid of validFormats) {
        const validData = {
          items: [
            {
              id: 'bom-001',
              name: 'Material A',
              quantity: 1.5,
              unit: 'kg',
              emissionFactorId: uuid,
              category: 'material',
            },
          ],
        };

        const result = bomFormSchema.safeParse(validData);
        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.data.items[0].emissionFactorId).toBe(uuid);
        }
      }
    });
  });

  describe('Error Messages for Type Mismatches', () => {
    test('should provide clear error message for number type', () => {
      const invalidData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: 471, // Number instead of string
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find((issue) =>
          issue.path.includes('emissionFactorId')
        );
        expect(error).toBeDefined();
        // Error should mention "string" type requirement
        expect(error?.message.toLowerCase()).toContain('string');
      }
    });

    test('should provide clear error message for boolean type', () => {
      const invalidData = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: true, // Boolean instead of string
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(invalidData);
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find((issue) =>
          issue.path.includes('emissionFactorId')
        );
        expect(error).toBeDefined();
      }
    });
  });

  describe('Empty String Handling', () => {
    test('should handle empty string emission factor ID', () => {
      const dataWithEmptyString = {
        items: [
          {
            id: 'bom-001',
            name: 'Material A',
            quantity: 1.5,
            unit: 'kg',
            emissionFactorId: '', // Empty string
            category: 'material',
          },
        ],
      };

      const result = bomFormSchema.safeParse(dataWithEmptyString);
      // Schema should validate but may fail required check
      expect(result.success).toBe(false);
      if (!result.success) {
        const error = result.error.issues.find((issue) =>
          issue.path.includes('emissionFactorId')
        );
        expect(error).toBeDefined();
      }
    });
  });
});
