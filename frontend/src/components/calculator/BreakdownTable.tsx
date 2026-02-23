/**
 * BreakdownTable Component
 *
 * Emerald Night 5B category breakdown table with:
 * - Category name with colored dot indicator
 * - Horizontal bar chart (proportional width, category color)
 * - Amount and percentage columns
 * - Collapsible category rows showing individual items
 * - SourceBadge for data source attribution
 *
 * Design Source: frontend/prototypes/approach-5b-single-card/03-results.html
 *
 * The table uses the dark theme styling from the prototype:
 * - Subtle row hover backgrounds
 * - Colored dot indicators matching EMISSION_CATEGORY_COLORS
 * - Bar tracks with rounded fills
 * - Tabular numbers for alignment
 *
 * TASK-FE-009: Results Dashboard - Breakdown Table
 * TASK-FE-P8-003: Expandable items in detailed breakdown section
 * TASK-FE-P8-005: Integrate SourceBadge into Breakdown Table
 * Emerald Night 5B Rebuild: Simplified table matching prototype
 */

import React, { useState, useMemo } from 'react';
import { ChevronRight } from 'lucide-react';
import { EMISSION_CATEGORY_COLORS } from '../../constants/colors';
import { SourceBadge } from '@/components/attribution/SourceBadge';
import type { BreakdownByComponent } from '../../types/store.types';

/**
 * Individual item within a category
 */
interface BreakdownItem {
  name: string;
  co2e: number;
  quantity?: number;
  unit?: string;
  data_source?: string;
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
  breakdown?: BreakdownByComponent;
  itemSources?: Record<string, string>;
}

/**
 * Capitalize first letter of string
 */
function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Format a component name for display
 * Converts snake_case and kebab-case to Title Case
 */
function formatComponentName(name: string): string {
  return name
    .replace(/[_-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

/**
 * Classify a component name into a category
 */
function classifyComponent(name: string): 'materials' | 'energy' | 'transport' | 'other' {
  const nameLower = name.toLowerCase();

  if (
    nameLower.includes('electricity') ||
    nameLower.includes('power') ||
    nameLower.includes('energy') ||
    nameLower.includes('kwh')
  ) {
    return 'energy';
  }

  if (
    nameLower.includes('transport') ||
    nameLower.includes('truck') ||
    nameLower.includes('ship') ||
    nameLower.includes('freight') ||
    nameLower.includes('logistics')
  ) {
    return 'transport';
  }

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

  return 'materials';
}

/**
 * Format number for display with locale thousand separators
 */
function formatAmount(value: number): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * BreakdownTable Component
 *
 * Displays emissions breakdown per category with horizontal bar charts,
 * matching the Emerald Night 5B prototype design.
 */
export default function BreakdownTable({
  totalCO2e,
  materialsCO2e = 0,
  energyCO2e = 0,
  transportCO2e = 0,
  breakdown,
  itemSources,
}: BreakdownTableProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Build breakdown data with items categorized from component breakdown
  const breakdownData: CategoryBreakdown[] = useMemo(() => {
    const categoriesMap: Record<string, CategoryBreakdown> = {
      materials: { category: 'materials', total: 0, percentage: 0, items: [] },
      energy: { category: 'energy', total: 0, percentage: 0, items: [] },
      transport: { category: 'transport', total: 0, percentage: 0, items: [] },
      other: { category: 'other', total: 0, percentage: 0, items: [] },
    };

    if (breakdown && Object.keys(breakdown).length > 0) {
      Object.entries(breakdown).forEach(([componentName, co2e]) => {
        const category = classifyComponent(componentName);
        const dataSource = itemSources?.[componentName];
        categoriesMap[category].items.push({
          name: componentName,
          co2e: co2e,
          data_source: dataSource,
        });
      });

      Object.values(categoriesMap).forEach((cat) => {
        cat.total = cat.items.reduce((sum, item) => sum + item.co2e, 0);
        cat.percentage = totalCO2e > 0 ? (cat.total / totalCO2e) * 100 : 0;
        cat.items.sort((a, b) => b.co2e - a.co2e);
      });
    } else {
      categoriesMap.materials.total = materialsCO2e;
      categoriesMap.materials.percentage = totalCO2e > 0 ? (materialsCO2e / totalCO2e) * 100 : 0;
      categoriesMap.energy.total = energyCO2e;
      categoriesMap.energy.percentage = totalCO2e > 0 ? (energyCO2e / totalCO2e) * 100 : 0;
      categoriesMap.transport.total = transportCO2e;
      categoriesMap.transport.percentage = totalCO2e > 0 ? (transportCO2e / totalCO2e) * 100 : 0;
    }

    return Object.values(categoriesMap)
      .filter((cat) => cat.total > 0)
      .sort((a, b) => b.total - a.total);
  }, [totalCO2e, materialsCO2e, energyCO2e, transportCO2e, breakdown, itemSources]);

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

  return (
    <table className="w-full border-collapse" data-testid="breakdown-table">
      <thead>
        <tr>
          <th className="px-6 py-3 text-left text-[0.6875rem] font-semibold text-[var(--text-dim)] uppercase tracking-[0.06em] border-b border-[var(--card-border)]">
            Category
          </th>
          <th className="px-6 py-3 text-left text-[0.6875rem] font-semibold text-[var(--text-dim)] uppercase tracking-[0.06em] border-b border-[var(--card-border)]">
            Amount
          </th>
          <th className="px-6 py-3 text-left text-[0.6875rem] font-semibold text-[var(--text-dim)] uppercase tracking-[0.06em] border-b border-[var(--card-border)]">
            Percentage
          </th>
          <th className="px-6 py-3 text-left text-[0.6875rem] font-semibold text-[var(--text-dim)] uppercase tracking-[0.06em] border-b border-[var(--card-border)] min-w-[200px] max-[768px]:min-w-[120px]">
            Distribution
          </th>
        </tr>
      </thead>
      <tbody>
        {breakdownData.map((item) => {
          const isExpanded = expandedCategories.has(item.category);
          const hasItems = item.items.length > 0;
          const categoryColor =
            EMISSION_CATEGORY_COLORS[item.category as keyof typeof EMISSION_CATEGORY_COLORS] ||
            '#666666';

          return (
            <React.Fragment key={item.category}>
              {/* Category row */}
              <tr
                className={`transition-colors duration-150 ${
                  hasItems ? 'cursor-pointer' : ''
                } hover:bg-white/[0.025]`}
                data-testid={`category-row-${item.category}`}
                onClick={() => hasItems && toggleCategory(item.category)}
              >
                <td className="px-6 py-4 text-[0.9375rem] text-[var(--text-primary)] border-b border-white/[0.04] align-middle">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      hasItems && toggleCategory(item.category);
                    }}
                    aria-expanded={isExpanded}
                    aria-controls={`${item.category}-items`}
                    className={`flex items-center gap-2.5 w-full text-left font-semibold ${
                      hasItems
                        ? 'hover:underline focus:outline-none focus:underline'
                        : 'cursor-default'
                    }`}
                    disabled={!hasItems}
                    data-testid={`expand-${item.category}`}
                  >
                    {hasItems && (
                      <ChevronRight
                        className={`h-4 w-4 transition-transform duration-200 flex-shrink-0 ${
                          isExpanded ? 'rotate-90' : ''
                        }`}
                        aria-hidden="true"
                      />
                    )}
                    <span
                      className="w-2.5 h-2.5 rounded-[3px] flex-shrink-0"
                      style={{ backgroundColor: categoryColor }}
                      aria-hidden="true"
                    />
                    {capitalize(item.category)}
                  </button>
                </td>
                <td className="px-6 py-4 text-[0.9375rem] text-[var(--text-primary)] font-semibold tabular-nums border-b border-white/[0.04] align-middle">
                  {formatAmount(item.total)}{' '}
                  <span className="text-[var(--text-dim)] font-normal text-[0.8125rem]">
                    kg CO<sub>2</sub>e
                  </span>
                </td>
                <td className="px-6 py-4 tabular-nums text-[var(--text-muted)] border-b border-white/[0.04] align-middle">
                  {item.percentage.toFixed(1)}%
                </td>
                <td className="px-6 py-4 border-b border-white/[0.04] align-middle min-w-[200px] max-[768px]:min-w-[120px]">
                  <div
                    className="w-full h-2.5 bg-white/[0.06] rounded-full overflow-hidden"
                    role="progressbar"
                    aria-valuenow={item.percentage}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`${item.category} contributes ${item.percentage.toFixed(1)}% of total emissions`}
                  >
                    <div
                      className="h-full rounded-full transition-all duration-600"
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: categoryColor,
                      }}
                      aria-hidden="true"
                    />
                  </div>
                </td>
              </tr>

              {/* Expanded items */}
              {isExpanded && item.items.map((subItem, index) => {
                const itemPercentage =
                  totalCO2e > 0 ? (subItem.co2e / totalCO2e) * 100 : 0;

                return (
                  <tr
                    key={`${item.category}-${subItem.name}-${index}`}
                    className="bg-white/[0.015] animate-in fade-in-0 slide-in-from-top-1 duration-200"
                    data-testid={`item-row-${subItem.name}`}
                  >
                    <td className="px-6 py-3 pl-14 text-sm text-[var(--text-muted)] border-b border-white/[0.04]">
                      <span>
                        {formatComponentName(subItem.name)}
                        {subItem.quantity !== undefined && subItem.unit && (
                          <span className="ml-2 text-xs text-[var(--text-dim)]">
                            ({subItem.quantity} {subItem.unit})
                          </span>
                        )}
                        {subItem.data_source && (
                          <SourceBadge sourceCode={subItem.data_source} className="ml-2" />
                        )}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-sm tabular-nums text-[var(--text-muted)] border-b border-white/[0.04]">
                      {subItem.co2e.toFixed(3)}
                    </td>
                    <td className="px-6 py-3 text-sm tabular-nums text-[var(--text-dim)] border-b border-white/[0.04]">
                      {itemPercentage.toFixed(1)}%
                    </td>
                    <td className="px-6 py-3 border-b border-white/[0.04] min-w-[200px] max-[768px]:min-w-[120px]">
                      <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full opacity-60"
                          style={{
                            width: `${itemPercentage}%`,
                            backgroundColor: categoryColor,
                          }}
                          aria-hidden="true"
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </React.Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
