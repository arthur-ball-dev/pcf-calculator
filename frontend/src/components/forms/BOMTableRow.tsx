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
 * - React.memo for performance optimization (prevents re-renders when sibling rows change)
 * - Support for virtualized rendering (TASK-FE-P8-007)
 *
 * Props:
 * - field: Field object from useFieldArray (properly typed)
 * - index: Row index
 * - form: React Hook Form instance
 * - onRemove: Callback for delete action
 * - canRemove: Whether delete is allowed (based on minimum constraint)
 * - isVirtualized: Whether this row is being rendered in a virtualized context
 *
 * TASK-FE-P7-026: Eliminated TypeScript any usages - field is now properly typed
 * TASK-FE-P8-005: Added React.memo wrapper to prevent unnecessary re-renders
 * TASK-FE-P8-006: Extracted inline handlers to useCallback for stable references
 * TASK-FE-P8-007: Added isVirtualized prop for virtualized list rendering
 */

import React, { useCallback } from 'react';
import type { UseFormReturn, FieldArrayWithId, ControllerRenderProps } from 'react-hook-form';
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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { TableCell, TableRow } from '@/components/ui/table';
import { useEmissionFactors } from '@/hooks/useEmissionFactors';
import { classifyComponent } from '@/utils/classifyComponent';
import { SourceBadge } from '@/components/attribution/SourceBadge';
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
  { value: 'other', label: 'Processing/Other' },
] as const;

/**
 * Type for field from useFieldArray<BOMFormData, 'items'>
 * This is the properly typed field object returned by useFieldArray
 */
type BOMFieldArrayItem = FieldArrayWithId<BOMFormData, 'items', 'id'>;

interface BOMTableRowProps {
  /** Field object from useFieldArray - properly typed for BOMFormData */
  field: BOMFieldArrayItem;
  /** Row index */
  index: number;
  /** React Hook Form instance */
  form: UseFormReturn<BOMFormData>;
  /** Callback for delete action */
  onRemove: () => void;
  /** Whether delete is allowed (based on minimum constraint) */
  canRemove: boolean;
  /** Whether this row is being rendered in a virtualized context (TASK-FE-P8-007) */
  isVirtualized?: boolean;
}

/**
 * BOMTableRow - Editable table row for a single BOM item
 *
 * Wrapped with React.memo to prevent unnecessary re-renders when sibling rows change.
 * This is a critical performance optimization for large BOMs.
 *
 * Note: The form object from React Hook Form maintains stable reference identity,
 * so passing it as a prop doesn't cause unnecessary re-renders.
 * The index and canRemove props are primitives and also don't cause issues.
 * The onRemove callback should ideally be memoized in the parent component.
 *
 * TASK-FE-P8-006: All inline handlers are now extracted to useCallback hooks
 * with proper dependency arrays [form, index] to prevent stale closures
 * and maintain stable function references for React.memo optimization.
 *
 * When isVirtualized is true, the component renders only the cell contents
 * (without the <tr> wrapper) since the parent handles the row element positioning.
 */
const BOMTableRow = React.memo(function BOMTableRow({
  index,
  form,
  onRemove,
  canRemove,
  isVirtualized = false,
}: BOMTableRowProps) {
  const { data: emissionFactors, isLoading: isLoadingFactors } = useEmissionFactors();

  // Show all emission factors - no category filtering
  // This ensures pre-selected emission factors always appear in the dropdown
  const filteredFactors = emissionFactors || [];

  /**
   * Handle name field changes with auto-classification and validation
   * TASK-FE-P8-006: Extracted from inline handler to useCallback
   */
  const handleNameChange = useCallback(
    (
      e: React.ChangeEvent<HTMLInputElement>,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.name`>['onChange']
    ) => {
      fieldOnChange(e);
      // Auto-classify the category based on component name
      const newName = e.target.value;
      if (newName) {
        const classifiedCategory = classifyComponent(newName);
        // Map 'materials' to 'material' for form value
        const formCategory = classifiedCategory === 'materials' ? 'material' : classifiedCategory;
        form.setValue(`items.${index}.category`, formCategory);
      }
      // Trigger validation for this field AND array-level validation
      // Array-level validation includes duplicate name checking
      // Use queueMicrotask to ensure field value is set before validation
      queueMicrotask(() => {
        form.trigger(`items.${index}.name`).then(() => {
          // Also trigger items array validation for duplicate check
          form.trigger('items');
        });
      });
    },
    [form, index]
  );

  /**
   * Handle quantity field changes with validation
   * TASK-FE-P8-006: Extracted from inline handler to useCallback
   */
  const handleQuantityChange = useCallback(
    (
      e: React.ChangeEvent<HTMLInputElement>,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.quantity`>['onChange']
    ) => {
      // Use valueAsNumber for proper HTML5 number input handling
      // Allow NaN to pass through - this preserves "-" while typing
      // Zod validation will catch invalid values
      // Totals calculation handles NaN gracefully with || 0
      const value = e.target.valueAsNumber;
      fieldOnChange(value);
      // Manually trigger validation for array fields
      // This is required because mode: 'onChange' doesn't always
      // trigger validation for nested array fields automatically
      // Use queueMicrotask to ensure field value is set before validation
      queueMicrotask(() => {
        form.trigger(`items.${index}.quantity`);
      });
    },
    [form, index]
  );

  /**
   * Handle category changes and reset emission factor
   * TASK-FE-P8-006: Extracted from inline handler to useCallback
   */
  const handleCategoryChange = useCallback(
    (
      value: string,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.category`>['onChange']
    ) => {
      fieldOnChange(value);
      // Reset emission factor when category changes
      form.setValue(`items.${index}.emissionFactorId`, null);
    },
    [form, index]
  );

  /**
   * Handle emission factor selection changes
   * TASK-FE-P8-006: Extracted from inline handler to useCallback
   */
  const handleEmissionFactorChange = useCallback(
    (
      value: string,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.emissionFactorId`>['onChange']
    ) => {
      // Store as string (UUID) or null for empty selection
      fieldOnChange(value || null);
    },
    []
  );

  /**
   * Handle delete confirmation action
   * TASK-FE-P8-006: Extracted from inline handler to useCallback
   */
  const handleDeleteConfirm = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      // Delay removal to allow dialog to close first
      setTimeout(() => onRemove(), 0);
    },
    [onRemove]
  );

  /**
   * Render the cell contents (shared between virtualized and non-virtualized rendering)
   */
  const renderCells = () => (
    <>
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
                  onChange={(e) => handleNameChange(e, field.onChange)}
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
                  onChange={(e) => handleQuantityChange(e, field.onChange)}
                  onBlur={field.onBlur}
                  className="w-28"
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
                  <SelectTrigger className="w-[70px]" aria-label="Unit">
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
                onValueChange={(value) => handleCategoryChange(value, field.onChange)}
                value={field.value}
              >
                <FormControl>
                  <SelectTrigger className="w-40" aria-label="Category">
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
                  onValueChange={(value) => handleEmissionFactorChange(value, field.onChange)}
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

      {/* Source - Display data source of selected emission factor with link to attribution */}
      <TableCell>
        {(() => {
          const selectedFactorId = form.watch(`items.${index}.emissionFactorId`);
          const selectedFactor = filteredFactors.find((f) => f.id === selectedFactorId);
          return selectedFactor && selectedFactor.data_source ? (
            <SourceBadge
              sourceCode={selectedFactor.data_source}
              className="text-sm"
            />
          ) : (
            <span className="text-sm text-muted-foreground/50">—</span>
          );
        })()}
      </TableCell>

      {/* Actions */}
      <TableCell className="text-right">
        {canRemove ? (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
                aria-label="Delete component"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Component</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete "{form.watch(`items.${index}.name`) || 'this component'}"?
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDeleteConfirm}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        ) : (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    disabled
                    className="text-muted-foreground"
                    aria-label="Delete component"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                <p>Cannot remove the last component</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </TableCell>
    </>
  );

  // When virtualized, return only the cells (parent provides the <tr>)
  // When not virtualized, wrap in TableRow
  if (isVirtualized) {
    return renderCells();
  }

  return (
    <TableRow>
      {renderCells()}
    </TableRow>
  );
});

// Set display name for debugging in React DevTools
BOMTableRow.displayName = 'BOMTableRow';

export default BOMTableRow;
