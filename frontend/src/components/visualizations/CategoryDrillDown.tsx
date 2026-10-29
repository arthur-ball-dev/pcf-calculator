/**
 * CategoryDrillDown Component
 *
 * Modal dialog showing breakdown of individual items within an emission category.
 * Used for drill-down functionality in the Carbon Flow Sankey visualization.
 *
 * Features:
 * - Lists all items in a category with CO2e values
 * - Shows percentage contribution of each item
 * - Sorted by CO2e value (highest first)
 * - Accessible dialog with proper ARIA attributes
 * - WCAG 2.1 AA compliant
 *
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization
 */

import { useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../ui/dialog';
import { EMISSION_CATEGORY_COLORS } from '../../constants/colors';

/**
 * Individual item in a category breakdown
 */
export interface CategoryItem {
  name: string;
  co2e: number;
}

/**
 * Props for CategoryDrillDown component
 */
export interface CategoryDrillDownProps {
  /** Category name (e.g., "Materials", "Energy", "Transport") */
  category: string;
  /** List of items in the category */
  items: CategoryItem[];
  /** Total CO2e for the category */
  total: number;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog should close */
  onClose: () => void;
}

/**
 * Format CO2e value for display
 *
 * @param value - CO2e value in kg
 * @returns Formatted string with 3 decimal places
 */
function formatCO2e(value: number): string {
  return value.toFixed(3);
}

/**
 * Calculate percentage of category total
 *
 * @param value - Item CO2e value
 * @param total - Category total CO2e
 * @returns Percentage string with 1 decimal place
 */
function calculatePercentage(value: number, total: number): string {
  if (total === 0) return '0.0';
  return ((value / total) * 100).toFixed(1);
}

/**
 * Get color for a category
 *
 * @param category - Category name
 * @returns Hex color code
 */
function getCategoryColor(category: string): string {
  const normalizedCategory = category.toLowerCase() as keyof typeof EMISSION_CATEGORY_COLORS;
  return EMISSION_CATEGORY_COLORS[normalizedCategory] || '#666666';
}

/**
 * CategoryDrillDown Component
 *
 * Displays a modal with detailed breakdown of items in an emission category.
 *
 * @param category - Name of the emission category
 * @param items - Array of items with name and co2e values
 * @param total - Total CO2e for the category
 * @param open - Whether the dialog is open
 * @param onClose - Callback when dialog should close
 */
export default function CategoryDrillDown({
  category,
  items,
  total,
  open,
  onClose,
}: CategoryDrillDownProps) {
  // Sort items by CO2e value (highest first)
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => b.co2e - a.co2e);
  }, [items]);

  const categoryColor = getCategoryColor(category);
  const hasItems = items.length > 0;

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-sm"
              style={{ backgroundColor: categoryColor }}
              aria-hidden="true"
            />
            {category} Breakdown
          </DialogTitle>
          <DialogDescription>
            Detailed breakdown of emissions in the {category.toLowerCase()} category
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4">
          {!hasItems ? (
            <div className="text-center text-muted-foreground py-8">
              No items in this category
            </div>
          ) : (
            <div className="space-y-2">
              {/* Item list */}
              {sortedItems.map((item, index) => (
                <div
                  key={`${item.name}-${index}`}
                  data-testid="category-item"
                  className="flex justify-between items-center py-2 px-3 rounded-md bg-muted/50 hover:bg-muted transition-colors"
                >
                  <span className="font-medium text-sm truncate max-w-[200px]">
                    {item.name}
                  </span>
                  <div className="flex items-center gap-3 text-sm tabular-nums">
                    <span className="text-muted-foreground">
                      {calculatePercentage(item.co2e, total)}%
                    </span>
                    <span className="font-medium">
                      {formatCO2e(item.co2e)} kg
                    </span>
                  </div>
                </div>
              ))}

              {/* Divider */}
              <div className="border-t my-3" />

              {/* Total */}
              <div className="flex justify-between items-center py-2 px-3 font-semibold">
                <span>Total</span>
                <span className="tabular-nums">
                  {formatCO2e(total)} kg CO<sub>2</sub>e
                </span>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
