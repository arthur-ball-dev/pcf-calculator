/**
 * BOMTableRow Component
 *
 * Individual row component for BOM table with inline editing.
 * Features:
 * - Inline form fields for all BOM properties
 * - Field-level validation with error display
 * - Emission factor selection without category filtering
 * - Delete button with tooltip (disabled when minimum constraint active)
 * - Accessibility with ARIA labels
 *
 * Props:
 * - field: Field object from useFieldArray
 * - index: Row index
 * - form: React Hook Form instance
 * - onRemove: Callback for delete action
 * - canRemove: Whether delete is allowed (based on minimum constraint)
 */

import type { UseFormReturn } from 'react-hook-form';
import { Trash2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from '@/components/ui/form';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { TableCell, TableRow } from '@/components/ui/table';
import { useEmissionFactors } from '@/hooks/useEmissionFactors';
import type { BOMFormData } from '@/schemas/bomSchema';

/**
 * Available units for BOM items
 */
const UNITS = ['kg', 'g', 'L', 'mL', 'kWh', 'MJ', 'tkm', 'm', 'cm'] as const;

/**
 * Available categories for BOM items
 */
const CATEGORIES = [
  { value: 'material', label: 'Material' },
  { value: 'energy', label: 'Energy' },
  { value: 'transport', label: 'Transport' },
  { value: 'other', label: 'Other' },
] as const;

interface BOMTableRowProps {
  field: any; // Field from useFieldArray
  index: number;
  form: UseFormReturn<BOMFormData>;
  onRemove: () => void;
  canRemove: boolean;
}

/**
 * BOMTableRow - Editable table row for a single BOM item
 */
export default function BOMTableRow({
  index,
  form,
  onRemove,
  canRemove,
}: BOMTableRowProps) {
  const { data: emissionFactors, isLoading: isLoadingFactors } = useEmissionFactors();

  // Show all emission factors - no category filtering
  // This ensures pre-selected emission factors always appear in the dropdown
  const filteredFactors = emissionFactors || [];

  return (
    <TableRow>
      {/* Component Name */}
      <TableCell>
        <FormField
          control={form.control}
          name={`items.${index}.name`}
          render={({ field }) => (
            <FormItem>
              <FormControl>
                <Input
                  {...field}
                  id={`items.${index}.name`}
                  placeholder="e.g., Cotton, Electricity"
                  className="min-w-[200px]"
                  aria-label="Component name"
                  onChange={(e) => {
                    field.onChange(e);
                    // Trigger validation for this field AND array-level validation
                    // Array-level validation includes duplicate name checking
                    // Use queueMicrotask to ensure field value is set before validation
                    queueMicrotask(() => {
                      form.trigger(`items.${index}.name`).then(() => {
                        // Also trigger items array validation for duplicate check
                        form.trigger('items');
                      });
                    });
                  }}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </TableCell>

      {/* Quantity */}
      <TableCell>
        <FormField
          control={form.control}
          name={`items.${index}.quantity`}
          render={({ field }) => (
            <FormItem>
              <FormControl>
                <Input
                  {...field}
                  type="number"
                  data-testid="bom-item-quantity"
                  step="0.01"
                  min="0"
                  onChange={(e) => {
                    // Use valueAsNumber for proper HTML5 number input handling
                    // Allow NaN to pass through - this preserves "-" while typing
                    // Zod validation will catch invalid values
                    // Totals calculation handles NaN gracefully with || 0
                    const value = e.target.valueAsNumber;
                    field.onChange(value);
                    // Manually trigger validation for array fields
                    // This is required because mode: 'onChange' doesn't always
                    // trigger validation for nested array fields automatically
                    // Use queueMicrotask to ensure field value is set before validation
                    queueMicrotask(() => {
                      form.trigger(`items.${index}.quantity`);
                    });
                  }}
                  onBlur={field.onBlur}
                  className="w-24"
                  aria-label="Quantity"
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </TableCell>

      {/* Unit */}
      <TableCell>
        <FormField
          control={form.control}
          name={`items.${index}.unit`}
          render={({ field }) => (
            <FormItem>
              <Select onValueChange={field.onChange} value={field.value}>
                <FormControl>
                  <SelectTrigger className="w-24" aria-label="Unit">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {UNITS.map((unit) => (
                    <SelectItem key={unit} value={unit}>
                      {unit}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      </TableCell>

      {/* Category */}
      <TableCell>
        <FormField
          control={form.control}
          name={`items.${index}.category`}
          render={({ field }) => (
            <FormItem>
              <Select
                onValueChange={(value) => {
                  field.onChange(value);
                  // Reset emission factor when category changes
                  form.setValue(`items.${index}.emissionFactorId`, null);
                }}
                value={field.value}
              >
                <FormControl>
                  <SelectTrigger className="w-32" aria-label="Category">
                    <SelectValue />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  {CATEGORIES.map((category) => (
                    <SelectItem key={category.value} value={category.value}>
                      {category.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
      </TableCell>

      {/* Emission Factor */}
      <TableCell>
        <FormField
          control={form.control}
          name={`items.${index}.emissionFactorId`}
          render={({ field }) => {
            // Convert null/undefined to empty string for Select component
            // Select component requires string value, not null
            const selectValue = field.value ?? '';

            return (
              <FormItem>
                <Select
                  onValueChange={(value) => {
                    // Store as string (UUID) or null for empty selection
                    field.onChange(value || null);
                  }}
                  value={selectValue}
                  disabled={isLoadingFactors || filteredFactors.length === 0}
                >
                  <FormControl>
                    <SelectTrigger className="min-w-[200px]" aria-label="Emission factor">
                      <SelectValue placeholder="Select factor" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {filteredFactors.map((factor) => (
                      <SelectItem key={factor.id} value={factor.id}>
                        {factor.activity_name} ({factor.co2e_factor} kg CO₂e/{factor.unit})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            );
          }}
        />
      </TableCell>

      {/* Actions */}
      <TableCell className="text-right">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={onRemove}
                  disabled={!canRemove}
                  className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  aria-label="Delete component"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </span>
            </TooltipTrigger>
            {!canRemove && (
              <TooltipContent>
                <p>Cannot remove the last component</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
      </TableCell>
    </TableRow>
  );
}
