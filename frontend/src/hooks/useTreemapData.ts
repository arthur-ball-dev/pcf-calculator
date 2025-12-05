/**
 * useTreemapData Hook
 *
 * Transforms calculation results into hierarchical treemap format
 * for emissions visualization. Supports GHG Protocol color assignment,
 * value aggregation, and detailed breakdown grouping.
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 */

import { useMemo } from 'react';
import type { Calculation, CalculationResult, EmissionBreakdown } from '@/types/store.types';

// ============================================================================
// Types
// ============================================================================

export interface TreemapNode {
  name: string;
  value?: number;
  color?: string;
  children?: TreemapNode[];
  metadata?: {
    percentage?: number;
    trend?: 'up' | 'down' | 'stable';
    dataQuality?: 'high' | 'medium' | 'low';
    category?: string;
    unit?: string;
  };
}

export interface UseTreemapDataOptions {
  /** Include percentage data in node metadata */
  includePercentage?: boolean;
  /** Use GHG Protocol scope colors */
  useScopeColors?: boolean;
  /** Threshold (percentage) below which items are aggregated into "Other" */
  aggregateThreshold?: number;
  /** Unit label for values */
  unit?: string;
}

// ============================================================================
// Constants
// ============================================================================

const SCOPE_COLORS = {
  Materials: '#51cf66', // Green for purchased goods (Scope 3)
  Energy: '#339af0',    // Blue for energy (Scope 2)
  Transport: '#fa5252', // Red for transport (Scope 3)
};

const CATEGORY_COLORS: Record<string, string> = {
  Steel: '#6c757d',
  Aluminum: '#868e96',
  Plastics: '#adb5bd',
  Electronics: '#ced4da',
  Electricity: '#4dabf7',
  'Natural Gas': '#74c0fc',
  'Road Transport': '#ff6b6b',
  'Sea Freight': '#ff8787',
};

const DEFAULT_COLORS = [
  '#228be6', '#fa5252', '#40c057', '#fab005',
  '#7950f2', '#e64980', '#15aabf', '#82c91e',
];

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if calculation has valid completed data
 */
function isValidCalculation(calculation: Calculation | CalculationResult | null | undefined): boolean {
  if (!calculation) return false;
  if (calculation.status !== 'completed') return false;
  return true;
}

/**
 * Get color for a category
 */
function getCategoryColor(category: string, index: number): string {
  // Check scope-level colors
  if (SCOPE_COLORS[category as keyof typeof SCOPE_COLORS]) {
    return SCOPE_COLORS[category as keyof typeof SCOPE_COLORS];
  }
  // Check category-level colors
  if (CATEGORY_COLORS[category]) {
    return CATEGORY_COLORS[category];
  }
  // Fall back to default colors
  return DEFAULT_COLORS[index % DEFAULT_COLORS.length];
}

/**
 * Group breakdown items by category type
 */
function groupBreakdownByCategory(breakdown: EmissionBreakdown[]): Record<string, EmissionBreakdown[]> {
  const groups: Record<string, EmissionBreakdown[]> = {
    Materials: [],
    Energy: [],
    Transport: [],
  };

  // Mapping of breakdown categories to scope categories
  const categoryMapping: Record<string, string> = {
    Steel: 'Materials',
    Aluminum: 'Materials',
    Plastics: 'Materials',
    Electronics: 'Materials',
    'Raw Materials': 'Materials',
    Packaging: 'Materials',
    Electricity: 'Energy',
    'Natural Gas': 'Energy',
    'Road Transport': 'Transport',
    'Sea Freight': 'Transport',
  };

  for (const item of breakdown) {
    const parentCategory = categoryMapping[item.category] || 'Materials';
    if (!groups[parentCategory]) {
      groups[parentCategory] = [];
    }
    groups[parentCategory].push(item);
  }

  return groups;
}

/**
 * Aggregate small items below threshold into "Other"
 */
function aggregateSmallItems(
  items: EmissionBreakdown[],
  threshold: number,
  total: number
): EmissionBreakdown[] {
  const largeItems: EmissionBreakdown[] = [];
  let smallTotal = 0;

  for (const item of items) {
    const percentage = (item.co2e / total) * 100;
    if (percentage >= threshold) {
      largeItems.push(item);
    } else {
      smallTotal += item.co2e;
    }
  }

  if (smallTotal > 0) {
    largeItems.push({
      category: 'Other',
      co2e: smallTotal,
      percentage: (smallTotal / total) * 100,
    });
  }

  return largeItems;
}

// ============================================================================
// Hook
// ============================================================================

export function useTreemapData(
  calculation: Calculation | CalculationResult | null | undefined,
  options: UseTreemapDataOptions = {}
): TreemapNode {
  const {
    includePercentage = false,
    useScopeColors = false,
    aggregateThreshold = 0,
    unit = 'kg CO2e',
  } = options;

  return useMemo(() => {
    // Return empty root node for invalid calculations
    if (!isValidCalculation(calculation)) {
      return {
        name: 'Total Emissions',
        children: [],
        metadata: { unit },
      };
    }

    const calc = calculation!;
    const totalCo2e = calc.total_co2e_kg || 0;

    // Check for detailed breakdown data
    const hasBreakdown = 'breakdown' in calc && Array.isArray(calc.breakdown) && calc.breakdown.length > 0;

    if (hasBreakdown) {
      // Process detailed breakdown
      const result = calc as CalculationResult;
      const groups = groupBreakdownByCategory(result.breakdown);

      const children: TreemapNode[] = [];

      for (const [categoryName, items] of Object.entries(groups)) {
        // Skip empty categories
        if (items.length === 0) continue;

        // Aggregate small items if threshold is set
        const processedItems = aggregateThreshold > 0
          ? aggregateSmallItems(items, aggregateThreshold, totalCo2e)
          : items;

        const categoryTotal = processedItems.reduce((sum, item) => sum + item.co2e, 0);

        // Skip categories with zero total
        if (categoryTotal === 0) continue;

        const categoryChildren: TreemapNode[] = processedItems.map((item, index) => ({
          name: item.category,
          value: item.co2e,
          color: getCategoryColor(item.category, index),
          metadata: includePercentage
            ? {
                percentage: item.percentage,
                category: categoryName,
              }
            : { category: categoryName },
        }));

        children.push({
          name: categoryName,
          color: SCOPE_COLORS[categoryName as keyof typeof SCOPE_COLORS] || getCategoryColor(categoryName, 0),
          children: categoryChildren,
          metadata: includePercentage
            ? {
                percentage: (categoryTotal / totalCo2e) * 100,
              }
            : undefined,
        });
      }

      return {
        name: 'Total Emissions',
        children,
        metadata: { unit },
      };
    }

    // Process basic calculation data (materials, energy, transport)
    const children: TreemapNode[] = [];

    if (calc.materials_co2e && calc.materials_co2e > 0) {
      children.push({
        name: 'Materials',
        value: calc.materials_co2e,
        color: useScopeColors ? SCOPE_COLORS.Materials : getCategoryColor('Materials', 0),
        metadata: includePercentage
          ? { percentage: (calc.materials_co2e / totalCo2e) * 100 }
          : undefined,
      });
    }

    if (calc.energy_co2e && calc.energy_co2e > 0) {
      children.push({
        name: 'Energy',
        value: calc.energy_co2e,
        color: useScopeColors ? SCOPE_COLORS.Energy : getCategoryColor('Energy', 1),
        metadata: includePercentage
          ? { percentage: (calc.energy_co2e / totalCo2e) * 100 }
          : undefined,
      });
    }

    if (calc.transport_co2e && calc.transport_co2e > 0) {
      children.push({
        name: 'Transport',
        value: calc.transport_co2e,
        color: useScopeColors ? SCOPE_COLORS.Transport : getCategoryColor('Transport', 2),
        metadata: includePercentage
          ? { percentage: (calc.transport_co2e / totalCo2e) * 100 }
          : undefined,
      });
    }

    return {
      name: 'Total Emissions',
      children,
      metadata: { unit },
    };
  }, [calculation, includePercentage, useScopeColors, aggregateThreshold, unit]);
}

export default useTreemapData;
