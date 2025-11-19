/**
 * BreakdownTable Component
 *
 * Interactive table showing emissions breakdown by category with:
 * - Collapsible category sections
 * - Sortable columns (CO2e, percentage)
 * - Progress bars showing percentage contribution
 * - WCAG 2.1 AA accessible
 *
 * TASK-FE-009: Results Dashboard - Breakdown Table
 */

import { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { EMISSION_CATEGORY_COLORS } from '../../constants/colors';

interface CategoryBreakdown {
  category: string;
  total: number;
  percentage: number;
}

interface BreakdownTableProps {
  totalCO2e: number;
  materialsCO2e?: number;
  energyCO2e?: number;
  transportCO2e?: number;
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
 * BreakdownTable Component
 *
 * Displays emissions breakdown with collapsible categories and sorting.
 *
 * @param totalCO2e - Total CO2e for calculating percentages
 * @param materialsCO2e - Materials emissions
 * @param energyCO2e - Energy emissions
 * @param transportCO2e - Transport emissions
 */
export default function BreakdownTable({
  totalCO2e,
  materialsCO2e = 0,
  energyCO2e = 0,
  transportCO2e = 0,
}: BreakdownTableProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<SortField>('category');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // Build breakdown data
  const breakdown: CategoryBreakdown[] = useMemo(() => {
    const categories = [
      { category: 'materials', total: materialsCO2e },
      { category: 'energy', total: energyCO2e },
      { category: 'transport', total: transportCO2e },
    ];

    return categories
      .filter((cat) => cat.total > 0)
      .map((cat) => ({
        ...cat,
        percentage: (cat.total / totalCO2e) * 100,
      }));
  }, [totalCO2e, materialsCO2e, energyCO2e, transportCO2e]);

  // Sort breakdown data
  const sortedBreakdown = useMemo(() => {
    const sorted = [...breakdown];

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
  }, [breakdown, sortField, sortDirection]);

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
          <TableHead>
            <button
              onClick={() => handleSort('category')}
              className="font-medium hover:underline focus:outline-none focus:underline"
            >
              Category
            </button>
          </TableHead>
          <TableHead>
            <button
              onClick={() => handleSort('co2e')}
              className="font-medium hover:underline focus:outline-none focus:underline"
            >
              CO₂e (kg)
            </button>
          </TableHead>
          <TableHead>
            <button
              onClick={() => handleSort('percentage')}
              className="font-medium hover:underline focus:outline-none focus:underline"
            >
              Percentage
            </button>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedBreakdown.map((item) => {
          const isExpanded = expandedCategories.has(item.category);
          const categoryColor =
            EMISSION_CATEGORY_COLORS[item.category as keyof typeof EMISSION_CATEGORY_COLORS] ||
            '#666666';

          return (
            <TableRow key={item.category}>
              <TableCell>
                <button
                  onClick={() => toggleCategory(item.category)}
                  aria-expanded={isExpanded}
                  className="flex items-center gap-2 hover:underline focus:outline-none focus:underline"
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <div
                    className="w-3 h-3 rounded-sm"
                    style={{ backgroundColor: categoryColor }}
                    aria-hidden="true"
                  />
                  <span className="font-medium">{capitalize(item.category)}</span>
                </button>
              </TableCell>
              <TableCell>
                <span className="tabular-nums">{item.total.toFixed(2)}</span>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <span className="tabular-nums w-12">{item.percentage.toFixed(1)}%</span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-[200px]">
                    <div
                      className="h-full transition-all"
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
          );
        })}
      </TableBody>
    </Table>
  );
}
