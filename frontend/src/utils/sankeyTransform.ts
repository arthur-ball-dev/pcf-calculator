/**
 * Sankey Transform Utility
 *
 * Transforms calculation results to Nivo Sankey format.
 * Handles data transformation, color mapping, and metadata enrichment.
 * Supports drill-down expansion to show individual items within a category.
 *
 * TASK-FE-008: Nivo Sankey Implementation
 * TASK-FE-P8-002: In-chart drill-down expansion
 */

import { EMISSION_CATEGORY_COLORS } from '../constants/colors';
import type { Calculation, BreakdownByComponent } from '../types/store.types';

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

/**
 * Classify a component name into a category based on naming patterns
 *
 * @param name - Component name
 * @returns Category: 'materials' | 'energy' | 'transport'
 */
function classifyComponent(name: string): 'materials' | 'energy' | 'transport' {
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

  // Default to materials
  return 'materials';
}

/**
 * Transform calculation results to expanded Sankey format for drill-down view.
 * Shows individual items within a category flowing to total.
 *
 * @param calculation - Calculation result from backend
 * @param expandedCategory - The category to expand ('materials', 'energy', 'transport')
 * @returns Sankey data structure with individual items as nodes
 */
export function transformToExpandedSankeyData(
  calculation: Calculation | null,
  expandedCategory: string
): SankeyData {
  // Return empty data for invalid input
  if (!calculation || calculation.status !== 'completed' || !calculation.breakdown) {
    return { nodes: [], links: [] };
  }

  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];
  const breakdown = calculation.breakdown as BreakdownByComponent;

  // Get base color for the expanded category
  const categoryColor = getNodeColor(expandedCategory);

  // Filter items belonging to the expanded category
  const categoryItems: Array<{ name: string; co2e: number }> = [];

  Object.entries(breakdown).forEach(([componentName, co2e]) => {
    const componentCategory = classifyComponent(componentName);
    if (componentCategory === expandedCategory && co2e > 0) {
      categoryItems.push({ name: componentName, co2e });
    }
  });

  // Sort by CO2e value descending
  categoryItems.sort((a, b) => b.co2e - a.co2e);

  // Calculate total for the expanded category
  const categoryTotal = categoryItems.reduce((sum, item) => sum + item.co2e, 0);

  // Create nodes for each item
  categoryItems.forEach((item, index) => {
    // Use item name as ID (sanitized), with index suffix to ensure uniqueness
    const itemId = `${item.name.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${index}`;
    // Generate slightly different shade for each item
    const shade = 0.8 + (index * 0.03); // Vary from 80% to lighter

    nodes.push({
      id: itemId,
      label: item.name, // Display the actual item name
      nodeColor: adjustColorBrightness(categoryColor, shade),
      metadata: {
        co2e: item.co2e,
        unit: 'kg',
        category: expandedCategory,
      },
    });

    // Link from item to category subtotal
    links.push({
      source: itemId,
      target: 'category-total',
      value: item.co2e,
    });
  });

  // Add category subtotal node
  if (nodes.length > 0) {
    nodes.push({
      id: 'category-total',
      label: `${expandedCategory.charAt(0).toUpperCase() + expandedCategory.slice(1)} Total`,
      nodeColor: categoryColor,
      metadata: {
        co2e: categoryTotal,
        unit: 'kg',
        category: expandedCategory,
      },
    });
  }

  return { nodes, links };
}

/**
 * Adjust color brightness
 *
 * @param hexColor - Hex color string
 * @param factor - Brightness factor (1 = original, >1 = lighter, <1 = darker)
 * @returns Adjusted hex color
 */
function adjustColorBrightness(hexColor: string, factor: number): string {
  // Remove # if present
  const hex = hexColor.replace('#', '');

  // Parse RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Adjust brightness
  const newR = Math.min(255, Math.round(r * factor));
  const newG = Math.min(255, Math.round(g * factor));
  const newB = Math.min(255, Math.round(b * factor));

  // Convert back to hex
  return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
}
