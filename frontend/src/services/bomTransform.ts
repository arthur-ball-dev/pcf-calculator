/**
 * BOM Transformation Service
 *
 * Transforms API BOM format to frontend BOM format with emission factor mapping.
 * Handles case-insensitive component name matching to emission factor IDs.
 *
 * Architecture:
 * 1. Build emission factor lookup map (activity_name -> EmissionFactorListItem)
 * 2. For each BOM item, match child_product_name to emission factor
 * 3. Infer category from emission factor or component name
 * 4. Transform to frontend BOMItem format with emissionFactorId
 *
 * UPDATED: TASK-FE-020 - UUID type system migration
 * - emissionFactorId: string (was number via parseInt)
 * - Preserves full UUID strings from emission factor IDs
 * - No type coercion or truncation
 */

import type {
  BOMItemResponse,
  EmissionFactorListItem,
} from '@/types/api.types';
import type { BOMItem, BOMItemCategory } from '@/types/store.types';

/**
 * Build emission factor lookup map for fast O(1) lookups
 *
 * Creates a Map with lowercase activity names as keys for case-insensitive matching.
 * If multiple emission factors have the same activity name, keeps the first one.
 *
 * @param emissionFactors - Array of emission factors from API
 * @returns Map of lowercase activity_name to EmissionFactorListItem
 */
export function buildEmissionFactorLookup(
  emissionFactors: EmissionFactorListItem[]
): Map<string, EmissionFactorListItem> {
  const lookup = new Map<string, EmissionFactorListItem>();

  for (const factor of emissionFactors) {
    // Normalize: lowercase, trim, replace spaces with underscores
    // This handles component names like "Plastic Abs" matching "plastic_abs"
    const key = factor.activity_name.toLowerCase().trim().replace(/\s+/g, '_');

    // Only add if not already present (keep first occurrence)
    if (!lookup.has(key)) {
      lookup.set(key, factor);
    }
  }

  return lookup;
}

/**
 * Infer BOM item category from emission factor or component name
 *
 * Priority:
 * 1. Use emission factor category if available (not implemented yet in backend)
 * 2. Infer from component name keywords
 * 3. Default to 'other'
 *
 * Keywords:
 * - energy: electricity, power, energy, kWh, MJ
 * - transport: truck, ship, freight, transport, tkm
 * - material: default for most components
 *
 * @param emissionFactor - Matched emission factor (or null if no match)
 * @param componentName - Component name from BOM
 * @returns BOMItemCategory
 */
export function inferCategory(
  emissionFactor: EmissionFactorListItem | null,
  componentName: string
): BOMItemCategory {
  // If emission factor has category field, use it (Phase 4 enhancement)
  // Note: Backend may not have this field yet, so it's optional
  // For now, we'll infer from component name

  const nameLower = componentName.toLowerCase();

  // Energy keywords
  if (
    nameLower.includes('electricity') ||
    nameLower.includes('power') ||
    nameLower.includes('energy') ||
    nameLower.includes('kwh') ||
    nameLower.includes('mj')
  ) {
    return 'energy';
  }

  // Transport keywords
  if (
    nameLower.includes('truck') ||
    nameLower.includes('ship') ||
    nameLower.includes('freight') ||
    nameLower.includes('transport') ||
    nameLower.includes('tkm')
  ) {
    return 'transport';
  }

  // If emission factor found, assume material (most common)
  if (emissionFactor) {
    return 'material';
  }

  // Default to 'other' for unknown components
  return 'other';
}

/**
 * Transform API BOM format to frontend BOM format
 *
 * Performs the following transformations:
 * 1. Map child_product_name to name
 * 2. Match component name to emission factor ID (case-insensitive)
 * 3. Infer category from emission factor or name
 * 4. Convert null notes to undefined
 * 5. Preserve original BOM item ID
 *
 * Handling missing emission factors:
 * - Sets emissionFactorId to null
 * - Logs warning to console
 * - Sets category to 'other'
 * - Allows user to manually select emission factor in BOM Editor
 *
 * UPDATED: TASK-FE-020 - UUID type system migration
 * - emissionFactorId preserved as string (no parseInt conversion)
 * - Handles full UUID strings from API (e.g., '471fe408a2604386bae572d9fc9a6b5c')
 * - No truncation or type coercion
 *
 * @param apiBOM - BOM array from API (ProductDetail.bill_of_materials)
 * @param emissionFactors - All emission factors from API
 * @returns Array of BOMItem with emissionFactorId mapped
 */
export function transformAPIBOMToFrontend(
  apiBOM: BOMItemResponse[],
  emissionFactors: EmissionFactorListItem[]
): BOMItem[] {
  // Build lookup map for O(1) matching
  const emissionFactorLookup = buildEmissionFactorLookup(emissionFactors);

  const transformed: BOMItem[] = [];

  for (const apiItem of apiBOM) {
    // Skip invalid items (empty name or zero quantity)
    if (!apiItem.child_product_name || !apiItem.child_product_name.trim()) {
      console.warn('Skipping BOM item with empty name:', apiItem);
      continue;
    }

    // Normalize component name: lowercase, trim, replace spaces with underscores
    // This handles component names like "Plastic Abs" matching "plastic_abs"
    const componentKey = apiItem.child_product_name.toLowerCase().trim().replace(/\s+/g, '_');
    const matchedFactor = emissionFactorLookup.get(componentKey);

    // Log warning if no emission factor found
    if (!matchedFactor) {
      console.warn(
        `No emission factor found for component: "${apiItem.child_product_name}". ` +
        'User will need to manually select emission factor in BOM Editor.'
      );
    }

    // Infer category
    const category = inferCategory(matchedFactor, apiItem.child_product_name);

    // UPDATED: Preserve emission factor ID as string (no parseInt)
    // Backend sends UUID strings like '471fe408a2604386bae572d9fc9a6b5c'
    // Previously: parseInt(matchedFactor.id, 10) truncated to 471
    // Now: Keep full UUID string
    const emissionFactorId = matchedFactor
      ? matchedFactor.id // Keep as string UUID
      : null;

    // Transform to frontend format
    const frontendItem: BOMItem = {
      id: apiItem.id,
      name: apiItem.child_product_name,
      quantity: apiItem.quantity,
      unit: apiItem.unit || '', // Handle null unit
      category,
      emissionFactorId, // String UUID or null
      notes: apiItem.notes || undefined, // Convert null to undefined
    };

    transformed.push(frontendItem);
  }

  return transformed;
}
