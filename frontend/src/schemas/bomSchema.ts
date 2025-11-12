/**
 * BOM Validation Schema
 *
 * Zod schema for validating Bill of Materials (BOM) forms.
 * Implements field-level and array-level validation including:
 * - Required fields (name, quantity, unit, category, emission factor)
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
 */

import { z } from 'zod';

/**
 * Single BOM item validation schema
 *
 * UPDATED: emissionFactorId changed from number to string for UUID support
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

  // UPDATED: number → string for UUID support
  // Accepts string UUIDs like '471fe408a2604386bae572d9fc9a6b5c'
  // or null if user hasn't selected an emission factor yet
  emissionFactorId: z.string()
    .min(1, 'Please select an emission factor')
    .nullable()
    .refine(val => val !== null, {
      message: 'Please select an emission factor'
    })
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
