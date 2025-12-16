/**
 * BreakdownTable Component
 *
 * Interactive table showing emissions breakdown by category with:
 * - Collapsible category sections with smooth animation
 * - Individual items within each category
 * - Sortable columns (CO2e, percentage)
 * - Progress bars showing percentage contribution
 * - WCAG 2.1 AA accessible
 *
 * TASK-FE-009: Results Dashboard - Breakdown Table
 * TASK-FE-P8-003: Expandable items in detailed breakdown section
 */

import React, { useState, useMemo } from 'react';
import { ChevronRight } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { EMISSION_CATEGORY_COLORS } from '../../constants/colors';
import type { BreakdownByComponent } from '../../types/store.types';

/**
 * Individual item within a category
 */
interface BreakdownItem {
  name: string;
  co2e: number;
  quantity?: number;
  unit?: string;
}

/**
 * Category with aggregated total and individual items
 */
interface CategoryBreakdown {
  category: string;
  total: number;
  percentage: number;
  items: BreakdownItem[];
}

interface BreakdownTableProps {
  totalCO2e: number;
  materialsCO2e?: number;
  energyCO2e?: number;
  transportCO2e?: number;
  /** Component-level breakdown (component_name -> co2e_kg) */
  breakdown?: BreakdownByComponent;
}

type SortField = 'category' | 'co2e' | 'percentage';
type SortDirection = 'asc' | 'desc';

/**
 * Capitalize first letter of string
 */
function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Classify a component name into a category based on naming patterns
 *
 * Categories:
 * - Energy: contains "electricity", "power", "energy", "kwh"
 * - Transport: contains "transport", "truck", "ship", "freight", "logistics"
 * - Materials: everything else (default)
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
 * BreakdownTable Component
 *
 * Displays emissions breakdown with collapsible categories and sorting.
 * Category rows expand to show individual component items.
 *
 * @param totalCO2e - Total CO2e for calculating percentages
 * @param materialsCO2e - Materials emissions
 * @param energyCO2e - Energy emissions
 * @param transportCO2e - Transport emissions
 * @param breakdown - Component-level breakdown map
 */
export default function BreakdownTable({
  totalCO2e,
  materialsCO2e = 0,
  energyCO2e = 0,
  transportCO2e = 0,
  breakdown,
}: BreakdownTableProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('co2e');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Build breakdown data with items categorized from component breakdown
  const breakdownData: CategoryBreakdown[] = useMemo(() => {
    // Initialize categories with their totals
    const categoriesMap: Record<string, CategoryBreakdown> = {
      materials: {
        category: 'materials',
        total: materialsCO2e,
        percentage: totalCO2e > 0 ? (materialsCO2e / totalCO2e) * 100 : 0,
        items: [],
      },
      energy: {
        category: 'energy',
        total: energyCO2e,
        percentage: totalCO2e > 0 ? (energyCO2e / totalCO2e) * 100 : 0,
        items: [],
      },
      transport: {
        category: 'transport',
        total: transportCO2e,
        percentage: totalCO2e > 0 ? (transportCO2e / totalCO2e) * 100 : 0,
        items: [],
      },
    };

    // If breakdown data is available, categorize individual items
    if (breakdown && Object.keys(breakdown).length > 0) {
      Object.entries(breakdown).forEach(([componentName, co2e]) => {
        const category = classifyComponent(componentName);
        categoriesMap[category].items.push({
          name: componentName,
          co2e: co2e,
        });
      });

      // Sort items within each category by CO2e (descending)
      Object.values(categoriesMap).forEach((cat) => {
        cat.items.sort((a, b) => b.co2e - a.co2e);
      });
    }

    // Return only categories with non-zero totals
    return Object.values(categoriesMap).filter((cat) => cat.total > 0);
  }, [totalCO2e, materialsCO2e, energyCO2e, transportCO2e, breakdown]);

  // Sort breakdown data
  const sortedBreakdown = useMemo(() => {
    const sorted = [...breakdownData];

    sorted.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'co2e':
          comparison = a.total - b.total;
          break;
        case 'percentage':
          comparison = a.percentage - b.percentage;
          break;
      }

      return sortDirection === 'desc' ? -comparison : comparison;
    });

    return sorted;
  }, [breakdownData, sortField, sortDirection]);

  /**
   * Toggle category expansion
   */
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  /**
   * Handle column header click for sorting
   */
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction
      setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
    } else {
      // New field, default to descending
      setSortField(field);
      setSortDirection('desc');
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[40%]">
            <button
              onClick={() => handleSort('category')}
              className="font-medium hover:underline focus:outline-none focus:underline"
              aria-label="Sort by category"
            >
              Category
            </button>
          </TableHead>
          <TableHead className="w-[25%]">
            <button
              onClick={() => handleSort('co2e')}
              className="font-medium hover:underline focus:outline-none focus:underline"
              aria-label="Sort by CO2e"
            >
              CO2e (kg)
            </button>
          </TableHead>
          <TableHead className="w-[35%]">
            <button
              onClick={() => handleSort('percentage')}
              className="font-medium hover:underline focus:outline-none focus:underline"
              aria-label="Sort by percentage"
            >
              Percentage
            </button>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedBreakdown.map((item) => {
          const isExpanded = expandedCategories.has(item.category);
          const hasItems = item.items.length > 0;
          const categoryColor =
            EMISSION_CATEGORY_COLORS[item.category as keyof typeof EMISSION_CATEGORY_COLORS] ||
            '#666666';

          return (
            <React.Fragment key={item.category}>
              {/* Category row */}
              <TableRow
                className={hasItems ? 'cursor-pointer hover:bg-muted/50' : ''}
                data-testid={`category-row-${item.category}`}
                onClick={() => hasItems && toggleCategory(item.category)}
              >
                <TableCell>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      hasItems && toggleCategory(item.category);
                    }}
                    aria-expanded={isExpanded}
                    aria-controls={`${item.category}-items`}
                    className={`flex items-center gap-2 w-full text-left ${
                      hasItems
                        ? 'hover:underline focus:outline-none focus:underline'
                        : 'cursor-default'
                    }`}
                    disabled={!hasItems}
                    data-testid={`expand-${item.category}`}
                  >
                    <ChevronRight
                      className={`h-4 w-4 transition-transform duration-200 ${
                        isExpanded ? 'rotate-90' : ''
                      } ${!hasItems ? 'opacity-30' : ''}`}
                      aria-hidden="true"
                    />
                    <div
                      className="w-3 h-3 rounded-sm flex-shrink-0"
                      style={{ backgroundColor: categoryColor }}
                      aria-hidden="true"
                    />
                    <span className="font-medium">{capitalize(item.category)}</span>
                    {hasItems && (
                      <span className="text-xs text-muted-foreground ml-1">
                        ({item.items.length} {item.items.length === 1 ? 'item' : 'items'})
                      </span>
                    )}
                  </button>
                </TableCell>
                <TableCell>
                  <span className="tabular-nums font-medium">{item.total.toFixed(2)}</span>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <span className="tabular-nums w-12">{item.percentage.toFixed(1)}%</span>
                    <div
                      className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-[200px]"
                      role="progressbar"
                      aria-valuenow={item.percentage}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${item.category} contributes ${item.percentage.toFixed(1)}% of total emissions`}
                    >
                      <div
                        className="h-full transition-all duration-300"
                        style={{
                          width: `${item.percentage}%`,
                          backgroundColor: categoryColor,
                        }}
                        aria-hidden="true"
                      />
                    </div>
                  </div>
                </TableCell>
              </TableRow>

              {/* Expanded items - render when expanded */}
              {isExpanded && item.items.map((subItem, index) => {
                const itemPercentage =
                  totalCO2e > 0 ? (subItem.co2e / totalCO2e) * 100 : 0;

                return (
                  <TableRow
                    key={`${item.category}-${subItem.name}-${index}`}
                    className="bg-muted/30 animate-in fade-in-0 slide-in-from-top-1 duration-200"
                    data-testid={`item-row-${subItem.name}`}
                  >
                    <TableCell className="pl-10">
                      <span className="text-sm text-muted-foreground">
                        {subItem.name}
                        {subItem.quantity !== undefined && subItem.unit && (
                          <span className="ml-2 text-xs">
                            ({subItem.quantity} {subItem.unit})
                          </span>
                        )}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="tabular-nums text-sm text-muted-foreground">
                        {subItem.co2e.toFixed(3)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="tabular-nums w-12 text-sm text-muted-foreground">
                          {itemPercentage.toFixed(1)}%
                        </span>
                        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden max-w-[200px]">
                          <div
                            className="h-full transition-all duration-300 opacity-60"
                            style={{
                              width: `${itemPercentage}%`,
                              backgroundColor: categoryColor,
                            }}
                            aria-hidden="true"
                          />
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </React.Fragment>
          );
        })}
      </TableBody>
    </Table>
  );
}
