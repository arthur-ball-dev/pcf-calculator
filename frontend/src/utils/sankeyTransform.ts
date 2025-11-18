/**
 * Sankey Transform Utility
 *
 * Transforms calculation results to Nivo Sankey format.
 * Handles data transformation, color mapping, and metadata enrichment.
 *
 * TASK-FE-008: Nivo Sankey Implementation
 */

import { EMISSION_CATEGORY_COLORS } from '../constants/colors';
import type { Calculation } from '../types/store.types';

/**
 * Sankey node interface matching Nivo requirements
 */
export interface SankeyNode {
  id: string;
  label: string;
  nodeColor?: string;
  metadata?: {
    co2e: number;
    unit: string;
    category: string;
  };
}

/**
 * Sankey link interface matching Nivo requirements
 */
export interface SankeyLink {
  source: string;
  target: string;
  value: number;
  color?: string;
}

/**
 * Sankey data structure for Nivo ResponsiveSankey
 */
export interface SankeyData {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

/**
 * Category mapping for emission breakdown
 */
type EmissionCategory = 'materials' | 'energy' | 'transport' | 'process' | 'waste' | 'total';

/**
 * Get color for a specific category
 *
 * @param category - Emission category
 * @returns Hex color code
 */
export function getNodeColor(category: string): string {
  const categoryKey = category as keyof typeof EMISSION_CATEGORY_COLORS;
  return EMISSION_CATEGORY_COLORS[categoryKey] || '#cccccc';
}

/**
 * Extract category from emission value field name
 *
 * @param valueName - Field name like 'materials_co2e'
 * @returns Category name or null
 */
export function getCategoryFromValue(valueName: string): string | null {
  const match = valueName.match(/^(\w+)_co2e$/);
  return match ? match[1] : null;
}

/**
 * Transform calculation results to Sankey diagram format
 *
 * Creates nodes for each emission category and links to total.
 * Excludes categories with zero emissions.
 *
 * @param calculation - Calculation result from backend
 * @returns Sankey data structure with nodes and links
 */
export function transformToSankeyData(calculation: Calculation | null): SankeyData {
  // Return empty data for invalid input
  if (!calculation || calculation.status !== 'completed') {
    return { nodes: [], links: [] };
  }

  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];

  // Check if we have breakdown data
  const hasBreakdown =
    calculation.materials_co2e !== undefined ||
    calculation.energy_co2e !== undefined ||
    calculation.transport_co2e !== undefined;

  if (!hasBreakdown) {
    return { nodes: [], links: [] };
  }

  // Define category mappings
  const categories: Array<{
    id: EmissionCategory;
    label: string;
    value: number | undefined;
  }> = [
    {
      id: 'materials',
      label: 'Materials',
      value: calculation.materials_co2e,
    },
    {
      id: 'energy',
      label: 'Energy',
      value: calculation.energy_co2e,
    },
    {
      id: 'transport',
      label: 'Transport',
      value: calculation.transport_co2e,
    },
  ];

  // Create nodes for non-zero categories
  categories.forEach((category) => {
    if (category.value && category.value > 0) {
      nodes.push({
        id: category.id,
        label: category.label,
        nodeColor: getNodeColor(category.id),
        metadata: {
          co2e: category.value,
          unit: 'kg',
          category: category.id,
        },
      });

      // Create link from category to total
      links.push({
        source: category.id,
        target: 'total',
        value: category.value,
        color: `${getNodeColor(category.id)}99`, // Add transparency
      });
    }
  });

  // Add total node if we have any categories
  if (nodes.length > 0 && calculation.total_co2e_kg) {
    nodes.push({
      id: 'total',
      label: 'Total PCF',
      nodeColor: getNodeColor('total'),
      metadata: {
        co2e: calculation.total_co2e_kg,
        unit: 'kg',
        category: 'total',
      },
    });
  }

  return { nodes, links };
}
