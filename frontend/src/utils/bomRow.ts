/**
 * BOM row helpers shared by the desktop row and the mobile card (#195, TASK-FE-P9-006)
 */
import type { BOMItem, BOMItemCategory } from '@/types/store.types';
import { classifyComponent, type EmissionCategory } from '@/utils/classifyComponent';
import { convertQuantity } from '@/utils/units';

/** The category a component name suggests, as a BOM row category */
export function categoryForName(name: string): BOMItemCategory {
  const classified = classifyComponent(name);
  return classified === 'materials' ? 'material' : classified;
}

/**
 * A row's category after a rename: re-derived from the new name while the category is still
 * the one the old name suggested, kept when the user chose another.
 */
export function categoryAfterRename(
  previousName: string,
  nextName: string,
  currentCategory: BOMItemCategory,
): BOMItemCategory {
  return currentCategory === categoryForName(previousName) ? categoryForName(nextName) : currentCategory;
}

/** kg CO2e for a row: quantity converted to the factor's unit, times the factor; null if unknown */
export function rowCO2e(
  quantity: number | undefined,
  unit: string | undefined,
  factor: { co2e_factor: number; unit: string } | undefined,
): number | null {
  if (!factor) return null;
  const converted = convertQuantity(quantity || 0, unit || factor.unit, factor.unit);
  return converted === null ? null : converted * factor.co2e_factor;
}

/** A BOM row category as the results and exports name it ('material' -> 'materials') */
export function resultCategory(category: string): EmissionCategory {
  return (category === 'material' ? 'materials' : category) as EmissionCategory;
}

const normalizeName = (name: string): string => name.toLowerCase().replace(/[\s_-]+/g, '');

/**
 * Category of a result component by its BOM row (exact name, then ignoring case, spaces,
 * underscores and dashes); undefined when no row has that name, so callers can fall back to
 * classifying the name.
 */
export function categoryLookup(bomItems: BOMItem[]): (componentName: string) => EmissionCategory | undefined {
  const exact = new Map(bomItems.map((item) => [item.name, item.category]));
  const loose = new Map(bomItems.map((item) => [normalizeName(item.name), item.category]));
  return (componentName) => {
    const category = exact.get(componentName) ?? loose.get(normalizeName(componentName));
    return category ? resultCategory(category) : undefined;
  };
}
