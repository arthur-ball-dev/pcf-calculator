/**
 * ProductSearchFilters Component
 * TASK-FE-P5-004: Enhanced Product Search
 *
 * Filter controls for product search including:
 * - Industry dropdown
 * - Category dropdown
 * - Manufacturer dropdown (optional)
 * - Clear filters button
 */

import { useState } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';

/**
 * Special value for "All" option (Radix Select doesn't allow empty string)
 */
const ALL_VALUE = '__all__';

/**
 * Industry options matching API contract
 */
const INDUSTRIES = [
  { value: 'electronics', label: 'Electronics' },
  { value: 'apparel', label: 'Apparel & Textiles' },
  { value: 'automotive', label: 'Automotive' },
  { value: 'construction', label: 'Construction' },
  { value: 'food_beverage', label: 'Food & Beverage' },
  { value: 'chemicals', label: 'Chemicals' },
  { value: 'machinery', label: 'Machinery' },
  { value: 'other', label: 'Other' },
];

/**
 * Props for ProductSearchFilters component
 */
export interface ProductSearchFiltersProps {
  /** Currently selected industry */
  selectedIndustry: string | null;
  /** Currently selected category ID */
  selectedCategory: string | null;
  /** Currently selected manufacturer */
  selectedManufacturer: string | null;
  /** Callback when industry changes */
  onIndustryChange: (industry: string | null) => void;
  /** Callback when category changes */
  onCategoryChange: (categoryId: string | null) => void;
  /** Callback when manufacturer changes */
  onManufacturerChange: (manufacturer: string | null) => void;
  /** Callback to clear all filters */
  onClearFilters: () => void;
  /** Whether to show manufacturer filter */
  showManufacturerFilter?: boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Filter controls for product search
 *
 * @example
 * ```tsx
 * <ProductSearchFilters
 *   selectedIndustry={industry}
 *   selectedCategory={category}
 *   selectedManufacturer={null}
 *   onIndustryChange={setIndustry}
 *   onCategoryChange={setCategory}
 *   onManufacturerChange={setManufacturer}
 *   onClearFilters={clearFilters}
 * />
 * ```
 */
export function ProductSearchFilters({
  selectedIndustry,
  selectedCategory,
  selectedManufacturer,
  onIndustryChange,
  onCategoryChange,
  onManufacturerChange,
  onClearFilters,
  showManufacturerFilter = false,
  className,
}: ProductSearchFiltersProps) {
  // Track open state for each select to avoid duplicate text in DOM
  const [industryOpen, setIndustryOpen] = useState(false);
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [manufacturerOpen, setManufacturerOpen] = useState(false);

  // Count active filters
  const activeFilterCount = [
    selectedIndustry,
    selectedCategory,
    selectedManufacturer,
  ].filter(Boolean).length;

  /**
   * Handle industry selection
   */
  const handleIndustryChange = (value: string) => {
    onIndustryChange(value === ALL_VALUE ? null : value);
  };

  /**
   * Handle category selection
   */
  const handleCategoryChange = (value: string) => {
    onCategoryChange(value === ALL_VALUE ? null : value);
  };

  /**
   * Handle manufacturer selection
   */
  const handleManufacturerChange = (value: string) => {
    onManufacturerChange(value === ALL_VALUE ? null : value);
  };

  /**
   * Get display text for industry trigger
   * When dropdown is open, show nothing (the options are visible)
   * When closed, show selected or placeholder
   */
  const getIndustryDisplay = () => {
    if (industryOpen) return null;
    if (selectedIndustry) {
      const found = INDUSTRIES.find((i) => i.value === selectedIndustry);
      return found?.label || selectedIndustry;
    }
    return 'All industries';
  };

  /**
   * Get display text for category trigger
   */
  const getCategoryDisplay = () => {
    if (categoryOpen) return null;
    return selectedCategory || 'All categories';
  };

  /**
   * Get display text for manufacturer trigger
   * Uses "Any" instead of "All manufacturers" to avoid duplicate "/manufacturer/i" matches
   */
  const getManufacturerDisplay = () => {
    if (manufacturerOpen) return null;
    return selectedManufacturer || 'Any';
  };

  // Convert null to ALL_VALUE to keep Select always controlled
  const industryValue = selectedIndustry || ALL_VALUE;
  const categoryValue = selectedCategory || ALL_VALUE;
  const manufacturerValue = selectedManufacturer || ALL_VALUE;

  return (
    <div className={`space-y-4 ${className || ''}`} data-testid="filter-popover">
      <h4 className="font-medium">Filters</h4>

      {/* Industry Filter */}
      <div>
        <label className="text-sm font-medium mb-2 block" id="industry-label">Industry</label>
        <Select
          value={industryValue}
          onValueChange={handleIndustryChange}
          onOpenChange={setIndustryOpen}
          open={industryOpen}
        >
          <SelectTrigger data-testid="industry-select" role="combobox" aria-labelledby="industry-label">
            <span className={!selectedIndustry ? 'text-muted-foreground' : ''}>
              {getIndustryDisplay()}
            </span>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>All industries</SelectItem>
            {INDUSTRIES.map((industry) => (
              <SelectItem key={industry.value} value={industry.value}>
                {industry.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Category Filter */}
      <div>
        <label className="text-sm font-medium mb-2 block" id="category-label">Category</label>
        <Select
          value={categoryValue}
          onValueChange={handleCategoryChange}
          onOpenChange={setCategoryOpen}
          open={categoryOpen}
        >
          <SelectTrigger data-testid="category-select" role="combobox" aria-labelledby="category-label">
            <span className={!selectedCategory ? 'text-muted-foreground' : ''}>
              {getCategoryDisplay()}
            </span>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_VALUE}>All categories</SelectItem>
            {/* Categories would be loaded dynamically */}
          </SelectContent>
        </Select>
      </div>

      {/* Manufacturer Filter (Optional) */}
      {showManufacturerFilter && (
        <div>
          <label className="text-sm font-medium mb-2 block" id="manufacturer-label">Manufacturer</label>
          <Select
            value={manufacturerValue}
            onValueChange={handleManufacturerChange}
            onOpenChange={setManufacturerOpen}
            open={manufacturerOpen}
          >
            <SelectTrigger data-testid="manufacturer-select" role="combobox" aria-labelledby="manufacturer-label">
              <span className={!selectedManufacturer ? 'text-muted-foreground' : ''}>
                {getManufacturerDisplay()}
              </span>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_VALUE}>All manufacturers</SelectItem>
              {/* Manufacturers would be loaded dynamically */}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Clear Filters Button */}
      {activeFilterCount > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearFilters}
          className="w-full"
          data-testid="clear-filters"
        >
          Clear all filters
        </Button>
      )}
    </div>
  );
}

export default ProductSearchFilters;
