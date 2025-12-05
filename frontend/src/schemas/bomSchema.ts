/**
 * BOM Validation Schema
 *
 * Zod schema for validating Bill of Materials (BOM) forms.
 * Implements field-level and array-level validation including:
 * - Required fields (name, quantity, unit, category)
 * - Optional emission factor (allows null/undefined for unmatched components)
 * - Empty string rejection for emissionFactorId
 * - Quantity > 0 validation
 * - Unique component names (case-insensitive)
 * - Minimum 1 item constraint
 * - Maximum 100 items constraint
 *
 * Used by BOMEditor with React Hook Form's useFieldArray.
 *
 * UPDATED: TASK-FE-020 - UUID type system migration
 * - emissionFactorId: z.number() → z.string()
 * - Validates UUID strings (not numbers)
 * - Prevents parseInt truncation at form validation layer
 *
 * UPDATED: TASK-FE-013 - Made emissionFactorId optional
 * - Allows null values when no emission factor is matched
 * - Enables progression through wizard even with unmatched components
 * - Users can manually select emission factors in BOM Editor
 *
 * UPDATED: BUG-001 Fix - Proper optional handling
 * - emissionFactorId is now truly optional (can be undefined)
 * - Empty string is rejected with validation message
 * - null is allowed for unmatched components
 */

import { z } from 'zod';

/**
 * Single BOM item validation schema
 *
 * UPDATED: emissionFactorId changed from number to string for UUID support
 * UPDATED: emissionFactorId is now optional (nullable and optional)
 * UPDATED: Empty string emissionFactorId is rejected with custom error
 */
export const bomItemSchema = z.object({
  id: z.string().min(1, 'Item ID is required'),

  name: z.string()
    .min(1, 'Component name is required')
    .max(100, 'Component name must be less than 100 characters'),

  quantity: z.number()
    .positive('Quantity must be greater than zero')
    .max(999999, 'Quantity cannot exceed 999,999'),

  unit: z.string()
    .min(1, 'Unit is required'),

  category: z.enum(['material', 'energy', 'transport', 'other'], {
    errorMap: () => ({ message: 'Please select a valid category' })
  }),

  // UPDATED: Made nullable AND optional with empty string rejection
  // Accepts string UUIDs like '471fe408a2604386bae572d9fc9a6b5c'
  // or null if no emission factor is matched or user hasn't selected one
  // or undefined if the field is not provided
  // Empty string is rejected with a validation error
  // This allows progression through wizard even with unmatched components
  emissionFactorId: z.string()
    .min(1, 'Please select an emission factor or leave empty')
    .nullable()
    .optional()
});

/**
 * BOM form data schema with array-level validation
 */
export const bomFormSchema = z.object({
  items: z.array(bomItemSchema)
    .min(1, 'BOM must have at least one component')
    .max(100, 'BOM cannot have more than 100 components')
    .refine(
      (items) => {
        // Check for duplicate names (case-insensitive)
        const names = items.map(item => item.name.toLowerCase().trim());
        return names.length === new Set(names).size;
      },
      {
        message: 'Component names must be unique'
      }
    )
});

/**
 * TypeScript type inferred from Zod schema
 */
export type BOMFormData = z.infer<typeof bomFormSchema>;

/**
 * TypeScript type for a single BOM item
 */
export type BOMItemFormData = z.infer<typeof bomItemSchema>;