/**
 * Color Constants for PCF Calculator
 *
 * Carbon Command Color Palette (Emerald Night)
 * =============================================
 * High-contrast colors optimized for dark backgrounds.
 * Each color occupies distinct hue territory for Sankey diagrams.
 *
 * Design Philosophy:
 * - Instantly distinguishable in data visualizations on dark backgrounds
 * - Matches the Emerald Night prototype Sankey diagram colors
 * - Works at varying opacities for glassmorphic surfaces
 * - Professional feel with vibrant accents
 */

/**
 * Emission category color mapping (Carbon Command palette)
 *
 * These colors are used for:
 * - Progress bars in ResultsDisplayContent
 * - Node colors in Sankey diagrams
 * - Category badges and indicators
 * - Breakdown table bar charts
 *
 * Hue Distribution:
 * - materials:   Blue      (207°) - foundational, dominant category
 * - energy:      Amber     (36°)  - warmth, power
 * - transport:   Green     (122°) - movement, nature
 * - combustion:  Rose      (340°) - heat
 * - process:     Purple    (291°) - industrial, distinct
 * - other:       Blue-Gray (200°) - neutral, recessive
 * - waste:       Stone     (30°)  - earthy, end-of-life
 * - total:       Light     (0°)   - anchoring summary node
 */
export const EMISSION_CATEGORY_COLORS = {
  materials: '#2196F3',   // Blue - foundational, dominant
  energy: '#FF9800',      // Amber - warmth, power
  transport: '#4CAF50',   // Green - movement, nature
  combustion: '#E91E63',  // Pink - heat
  process: '#9C27B0',     // Purple - industrial, distinct
  other: '#78909C',       // Blue-gray - neutral, recessive
  waste: '#795548',       // Brown - earthy, end-of-life
  total: '#E8EAED',       // Light gray - summary node on dark bg
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

/**
 * CSS variable references for use in styled components
 * These map to the --chart-N variables defined in index.css
 */
export const CHART_CSS_VARIABLES = {
  primary: 'hsl(var(--chart-1))',
  secondary: 'hsl(var(--chart-2))',
  tertiary: 'hsl(var(--chart-3))',
  quaternary: 'hsl(var(--chart-4))',
  quinary: 'hsl(var(--chart-5))',
} as const;
