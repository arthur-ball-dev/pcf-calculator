/**
 * Color Constants for PCF Calculator
 *
 * ESG-Authority Color Palette
 * ==========================
 * Professionally restrained, high-contrast colors for carbon accounting.
 * Each color occupies distinct hue territory for Sankey diagrams.
 *
 * Design Philosophy:
 * - Instantly distinguishable in data visualizations
 * - Passes WCAG contrast ratios for text overlays
 * - Works in both light and potential dark mode
 * - Professional feel without garish saturation
 *
 * Reference: knowledge/frontend/VISUALIZATION_PATTERNS.md
 *
 * TASK-FE-007: Calculate Flow with Polling (Color System Alignment)
 * UI Redesign: ESG-Authority Palette Update
 */

/**
 * Emission category color mapping
 *
 * These colors are used for:
 * - Progress bars in ResultsDisplayContent
 * - Node colors in Sankey diagrams (TASK-FE-008)
 * - Category badges and indicators
 * - Treemap segments
 *
 * Hue Distribution (for visual separation):
 * - materials:   Navy      (220°) - foundational, solid
 * - energy:      Amber     (30°)  - warmth, power
 * - transport:   Teal      (175°) - movement, theme-aligned
 * - combustion:  Rose      (340°) - heat without garish red
 * - process:     Violet    (270°) - industrial, distinct
 * - other:       Slate     (215°) - neutral, recessive
 * - waste:       Stone     (30°)  - earthy, end-of-life
 * - total:       Slate-900 (215°) - anchoring, definitive
 */
export const EMISSION_CATEGORY_COLORS = {
  materials: '#1E3A5F',   // Deep navy - solid, foundational
  energy: '#B45309',      // Burnt amber - warmth, power
  transport: '#0F766E',   // Teal-700 - movement, aligned with theme
  combustion: '#9F1239',  // Rose-800 - heat without garish red
  process: '#5B21B6',     // Violet-800 - industrial, distinct
  other: '#64748B',       // Slate-500 - neutral, recessive
  waste: '#78716C',       // Stone-500 - earthy, end-of-life
  total: '#0F172A',       // Slate-900 - anchoring, definitive
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
