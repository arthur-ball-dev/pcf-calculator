/**
 * Visualization Components Index
 * TASK-FE-P7-013: Visualization Responsiveness
 * TASK-FE-P7-024: Bundle Optimization with Lazy Loading
 *
 * Exports all visualization components for use throughout the application.
 * Provides both eager and lazy-loaded versions of chart components for
 * optimal bundle splitting.
 */

import { lazy } from 'react';

// =============================================================================
// Eager Exports (for backward compatibility)
// =============================================================================

// Main chart components
export { default as SankeyDiagram } from './SankeyDiagram';
export type { SankeyNodeClickData } from './SankeyDiagram';

// Chart container components
export { ResponsiveChartContainer } from './ResponsiveChartContainer';
export { default as ResponsiveChartContainerDefault } from './ResponsiveChartContainer';

// Supporting components
export { default as SankeyTooltip } from './SankeyTooltip';
export { default as CategoryDrillDown } from './CategoryDrillDown';

// =============================================================================
// Lazy-Loaded Exports (for code splitting)
// =============================================================================

/**
 * Lazy-loaded SankeyDiagram component
 * Use with Suspense boundary for code splitting
 *
 * @example
 * import { LazySankeyDiagram } from '@/components/visualizations';
 *
 * <Suspense fallback={<ChartSkeleton />}>
 *   <LazySankeyDiagram calculation={calculation} />
 * </Suspense>
 */
export const LazySankeyDiagram = lazy(() =>
  import('./SankeyDiagram').then((module) => ({ default: module.default }))
);

/**
 * Lazy-loaded CategoryDrillDown component
 * Use with Suspense boundary for code splitting
 */
export const LazyCategoryDrillDown = lazy(() =>
  import('./CategoryDrillDown').then((module) => ({ default: module.default }))
);

/**
 * Lazy-loaded ResponsiveChartContainer component
 * Use with Suspense boundary for code splitting
 */
export const LazyResponsiveChartContainer = lazy(() =>
  import('./ResponsiveChartContainer').then((module) => ({
    default: module.ResponsiveChartContainer,
  }))
);

// =============================================================================
// Preload Functions (for eager loading on hover/focus)
// =============================================================================

/**
 * Preload the SankeyDiagram chunk
 * Call on hover or focus to improve perceived performance
 *
 * @example
 * <button onMouseEnter={preloadSankeyDiagram}>View Results</button>
 */
export function preloadSankeyDiagram(): void {
  import('./SankeyDiagram');
}

/**
 * Preload the CategoryDrillDown chunk
 */
export function preloadCategoryDrillDown(): void {
  import('./CategoryDrillDown');
}

/**
 * Preload all chart-related chunks
 * Useful for prefetching on route transitions
 */
export function preloadAllCharts(): void {
  preloadSankeyDiagram();
  preloadCategoryDrillDown();
}
