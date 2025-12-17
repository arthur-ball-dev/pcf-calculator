/**
 * Classify Component Utility
 *
 * Classifies component names into emission categories based on naming patterns.
 * Used consistently across BreakdownTable, SankeyDiagram, and exports.
 */

export type EmissionCategory = 'materials' | 'energy' | 'transport' | 'other';

/**
 * Classify a component name into an emission category based on naming patterns.
 *
 * Categories:
 * - Energy: contains "electricity", "power", "energy", "kwh"
 * - Transport: contains "transport", "truck", "ship", "freight", "logistics"
 * - Other/Processing: contains "process", "coating", "treatment", "welding", "machining",
 *   "assembly", "packaging", "testing", "finishing", "curing", "molding", "casting"
 * - Materials: everything else (default)
 *
 * @param name - Component name to classify
 * @returns Emission category
 */
export function classifyComponent(name: string): EmissionCategory {
  const nameLower = name.toLowerCase();

  // Energy patterns
  if (
    nameLower.includes('electricity') ||
    nameLower.includes('power') ||
    nameLower.includes('energy') ||
    nameLower.includes('kwh')
  ) {
    return 'energy';
  }

  // Transport patterns
  if (
    nameLower.includes('transport') ||
    nameLower.includes('truck') ||
    nameLower.includes('ship') ||
    nameLower.includes('freight') ||
    nameLower.includes('logistics')
  ) {
    return 'transport';
  }

  // Processing/Other patterns
  if (
    nameLower.includes('process') ||
    nameLower.includes('coating') ||
    nameLower.includes('treatment') ||
    nameLower.includes('welding') ||
    nameLower.includes('machining') ||
    nameLower.includes('assembly') ||
    nameLower.includes('packaging') ||
    nameLower.includes('testing') ||
    nameLower.includes('finishing') ||
    nameLower.includes('curing') ||
    nameLower.includes('molding') ||
    nameLower.includes('casting') ||
    nameLower.includes('painting') ||
    nameLower.includes('cutting') ||
    nameLower.includes('stamping') ||
    nameLower.includes('pressing')
  ) {
    return 'other';
  }

  // Default to materials
  return 'materials';
}

/**
 * Format a category for display.
 * Converts internal category names to user-friendly labels.
 *
 * @param category - Internal category name
 * @returns Formatted category label
 */
export function formatCategoryLabel(category: string): string {
  if (!category) return '';
  if (category.toLowerCase() === 'other') return 'Processing/Other';
  return category.charAt(0).toUpperCase() + category.slice(1);
}
