/**
 * Color Constants for PCF Calculator
 *
 * Centralized color definitions aligned with VISUALIZATION_PATTERNS.md
 * to ensure consistency across components and Sankey diagrams.
 *
 * Reference: knowledge/frontend/VISUALIZATION_PATTERNS.md (lines 86-95)
 *
 * TASK-FE-007: Calculate Flow with Polling (Color System Alignment)
 */

/**
 * Emission category color mapping
 *
 * These colors are used for:
 * - Progress bars in ResultsDisplayContent
 * - Node colors in Sankey diagrams (TASK-FE-008)
 * - Category badges and indicators
 */
export const EMISSION_CATEGORY_COLORS = {
  materials: '#2196F3', // Blue - Raw materials
  energy: '#FFC107', // Amber - Energy consumption
  transport: '#4CAF50', // Green - Transportation
  process: '#9C27B0', // Purple - Manufacturing processes
  waste: '#757575', // Gray - Waste/end-of-life
  total: '#003f7f', // Navy - Final product
} as const;

/**
 * Type-safe accessor for emission category colors
 */
export type EmissionCategory = keyof typeof EMISSION_CATEGORY_COLORS;

/**
 * Get color for a specific emission category
 *
 * @param category - The emission category
 * @returns Hex color code
 */
export function getEmissionCategoryColor(category: EmissionCategory): string {
  return EMISSION_CATEGORY_COLORS[category];
}
