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
 * - Emerald Night 5B: pill-shaped quantity controls, category dot badges, per-row CO2e
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

import React, { useCallback, useMemo } from 'react';
import type { UseFormReturn, FieldArrayWithId, ControllerRenderProps } from 'react-hook-form';
import { Trash2, Minus, Plus } from 'lucide-react';
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
import type { EmissionFactor } from '@/hooks/useEmissionFactors';
import { classifyComponent } from '@/utils/classifyComponent';
import { EMISSION_CATEGORY_COLORS } from '@/constants/colors';
import { SourceBadge } from '@/components/attribution/SourceBadge';
import { emissionFactorsAPI } from '@/services/api/emissionFactors';
import type { BOMFormData } from '@/schemas/bomSchema';

/**
 * Available units for BOM items
 */
const UNITS = ['kg', 'g', 'L', 'mL', 'kWh', 'MJ', 'tkm', 'm', 'cm'] as const;

/**
 * Category display config with color dots
 * Maps form category values to display labels and color codes
 */
const CATEGORY_CONFIG: Record<string, { label: string; color: string; bgColor: string; borderColor: string }> = {
  material: {
    label: 'Materials',
    color: EMISSION_CATEGORY_COLORS.materials,
    bgColor: 'rgba(16, 185, 129, 0.18)',
    borderColor: 'rgba(16, 185, 129, 0.22)',
  },
  energy: {
    label: 'Energy',
    color: EMISSION_CATEGORY_COLORS.energy,
    bgColor: 'rgba(245, 158, 11, 0.18)',
    borderColor: 'rgba(245, 158, 11, 0.22)',
  },
  transport: {
    label: 'Transport',
    color: EMISSION_CATEGORY_COLORS.transport,
    bgColor: 'rgba(59, 130, 246, 0.18)',
    borderColor: 'rgba(59, 130, 246, 0.22)',
  },
  combustion: {
    label: 'Combustion',
    color: '#E91E63',
    bgColor: 'rgba(233, 30, 99, 0.18)',
    borderColor: 'rgba(233, 30, 99, 0.22)',
  },
  other: {
    label: 'Other',
    color: EMISSION_CATEGORY_COLORS.other,
    bgColor: 'rgba(148, 163, 184, 0.15)',
    borderColor: 'rgba(148, 163, 184, 0.18)',
  },
};

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
  /** Emission factors passed from parent (performance optimization) */
  emissionFactors?: EmissionFactor[];
  /** Whether emission factors are loading */
  isLoadingFactors?: boolean;
}

/**
 * Maximum number of emission factors to render in dropdown
 * This prevents rendering 300+ SelectItems which causes severe performance issues
 */
const MAX_DROPDOWN_ITEMS = 50;

const BOMTableRow = React.memo(function BOMTableRow({
  index,
  form,
  onRemove,
  canRemove,
  isVirtualized = false,
  emissionFactors = [],
  isLoadingFactors = false,
}: BOMTableRowProps) {
  // Get currently selected emission factor ID
  const selectedFactorId = form.watch(`items.${index}.emissionFactorId`);
  // Watch quantity and category for reactive updates
  const watchedQuantity = form.watch(`items.${index}.quantity`);
  const watchedCategory = form.watch(`items.${index}.category`);

  // Limit emission factors to MAX_DROPDOWN_ITEMS for performance
  // Always include the currently selected factor if it exists
  const filteredFactors = useMemo(() => {
    if (emissionFactors.length <= MAX_DROPDOWN_ITEMS) {
      return emissionFactors;
    }

    // Take first MAX_DROPDOWN_ITEMS
    const limited = emissionFactors.slice(0, MAX_DROPDOWN_ITEMS);

    // If selected factor exists and isn't in the limited set, add it
    if (selectedFactorId) {
      const selectedInLimited = limited.some(f => f.id === selectedFactorId);
      if (!selectedInLimited) {
        const selectedFactor = emissionFactors.find(f => f.id === selectedFactorId);
        if (selectedFactor) {
          limited.unshift(selectedFactor); // Add at beginning
        }
      }
    }

    return limited;
  }, [emissionFactors, selectedFactorId]);

  /**
   * Calculate per-row CO2e estimate
   */
  const rowCO2e = useMemo(() => {
    if (!selectedFactorId) return null;
    const factor = emissionFactors.find(f => f.id === selectedFactorId);
    if (!factor) return null;
    const qty = watchedQuantity || 0;
    return qty * factor.co2e_factor;
  }, [selectedFactorId, watchedQuantity, emissionFactors]);

  /**
   * Get the category config for the current row
   */
  const categoryConfig = useMemo(() => {
    return CATEGORY_CONFIG[watchedCategory] || CATEGORY_CONFIG.other;
  }, [watchedCategory]);

  /**
   * Handle name field changes with auto-classification, auto-EF suggestion, and validation
   */
  const handleNameChange = useCallback(
    (
      e: React.ChangeEvent<HTMLInputElement>,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.name`>['onChange']
    ) => {
      fieldOnChange(e);
      const newName = e.target.value;
      if (newName) {
        const classifiedCategory = classifyComponent(newName);
        const formCategory = classifiedCategory === 'materials' ? 'material' : classifiedCategory;
        form.setValue(`items.${index}.category`, formCategory);

        if (newName.length >= 3) {
          const currentUnit = form.getValues(`items.${index}.unit`) || 'kg';
          emissionFactorsAPI.suggest(newName, currentUnit).then((suggestedFactor) => {
            if (suggestedFactor) {
              const currentFactorId = form.getValues(`items.${index}.emissionFactorId`);
              if (!currentFactorId) {
                form.setValue(`items.${index}.emissionFactorId`, suggestedFactor.id);
              }
            }
          }).catch(() => {
            // Silently ignore suggestion errors
          });
        }
      }
      queueMicrotask(() => {
        form.trigger(`items.${index}.name`).then(() => {
          form.trigger('items');
        });
      });
    },
    [form, index]
  );

  /**
   * Handle quantity field changes with validation
   */
  const handleQuantityChange = useCallback(
    (
      e: React.ChangeEvent<HTMLInputElement>,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.quantity`>['onChange']
    ) => {
      const value = e.target.valueAsNumber;
      fieldOnChange(value);
      queueMicrotask(() => {
        form.trigger(`items.${index}.quantity`);
      });
    },
    [form, index]
  );

  /**
   * Handle quantity increment/decrement via pill buttons
   */
  const handleQuantityStep = useCallback(
    (delta: number) => {
      const currentValue = form.getValues(`items.${index}.quantity`) || 0;
      const newValue = Math.max(0.01, currentValue + delta);
      const rounded = Math.round(newValue * 100) / 100;
      form.setValue(`items.${index}.quantity`, rounded, { shouldValidate: true, shouldDirty: true });
    },
    [form, index]
  );

  /**
   * Handle emission factor selection changes
   */
  const handleEmissionFactorChange = useCallback(
    (
      value: string,
      fieldOnChange: ControllerRenderProps<BOMFormData, `items.${number}.emissionFactorId`>['onChange']
    ) => {
      fieldOnChange(value || null);
    },
    []
  );

  /**
   * Handle delete confirmation action
   */
  const handleDeleteConfirm = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
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
      <TableCell className="py-2 px-3">
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
                  className="w-full bg-white/[0.04] border-white/[0.08] text-[var(--text-primary)] placeholder:text-[var(--text-dim)] focus:border-emerald-500/50 focus:ring-emerald-500/20"
                  aria-label="Component name"
                  onChange={(e) => handleNameChange(e, field.onChange)}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
      </TableCell>

      {/* Category with colored dot badge */}
      <TableCell className="py-2 px-3">
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-[13px] font-semibold tracking-[0.02em] whitespace-nowrap"
          style={{
            background: categoryConfig.bgColor,
            color: categoryConfig.color,
            border: `1px solid ${categoryConfig.borderColor}`,
          }}
        >
          <span
            className="w-[7px] h-[7px] rounded-full flex-shrink-0"
            style={{ background: categoryConfig.color }}
          />
          {categoryConfig.label}
        </span>
      </TableCell>

      {/* Quantity - Pill-shaped controls */}
      <TableCell className="py-2 px-3">
        <FormField
          control={form.control}
          name={`items.${index}.quantity`}
          render={({ field }) => (
            <FormItem>
              <div className="flex items-center gap-2">
                {/* Pill quantity control */}
                <div className="inline-flex items-center bg-white/[0.04] border border-white/[0.08] rounded-lg overflow-hidden">
                  <button
                    type="button"
                    className="w-[30px] h-[30px] flex items-center justify-center text-[var(--text-muted)] hover:bg-white/[0.06] hover:text-[var(--text-primary)] transition-colors"
                    onClick={() => handleQuantityStep(-1)}
                    aria-label="Decrease quantity"
                    data-testid="qty-decrease"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <FormControl>
                    <input
                      {...field}
                      type="number"
                      data-testid="bom-item-quantity"
                      step="0.01"
                      min="0"
                      onChange={(e) => handleQuantityChange(e, field.onChange)}
                      onBlur={field.onBlur}
                      className="w-14 h-[30px] text-center text-sm font-medium tabular-nums text-[var(--text-primary)] bg-transparent border-x border-white/[0.08] outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                      aria-label="Quantity"
                    />
                  </FormControl>
                  <button
                    type="button"
                    className="w-[30px] h-[30px] flex items-center justify-center text-[var(--text-muted)] hover:bg-white/[0.06] hover:text-[var(--text-primary)] transition-colors"
                    onClick={() => handleQuantityStep(1)}
                    aria-label="Increase quantity"
                    data-testid="qty-increase"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
                {/* Unit selector */}
                <FormField
                  control={form.control}
                  name={`items.${index}.unit`}
                  render={({ field: unitField }) => (
                    <Select onValueChange={unitField.onChange} value={unitField.value}>
                      <SelectTrigger className="w-[70px] h-[30px] text-[13px] text-[var(--text-dim)] bg-transparent border-white/[0.08]" aria-label="Unit">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {UNITS.map((unit) => (
                          <SelectItem key={unit} value={unit}>
                            {unit}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <FormMessage />
            </FormItem>
          )}
        />
      </TableCell>

      {/* Emission Factor */}
      <TableCell className="py-2 px-3">
        <FormField
          control={form.control}
          name={`items.${index}.emissionFactorId`}
          render={({ field }) => {
            const selectValue = field.value ?? '';

            return (
              <FormItem>
                <Select
                  onValueChange={(value) => handleEmissionFactorChange(value, field.onChange)}
                  value={selectValue}
                  disabled={isLoadingFactors || filteredFactors.length === 0}
                >
                  <FormControl>
                    <SelectTrigger className="w-full bg-white/[0.04] border-white/[0.08] text-[var(--text-primary)] truncate" aria-label="Emission factor">
                      <SelectValue placeholder="Select factor" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {filteredFactors.map((factor) => (
                      <SelectItem key={factor.id} value={factor.id}>
                        {factor.activity_name} ({factor.co2e_factor} kg CO&#8322;e/{factor.unit})
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

      {/* Per-row CO2e estimate */}
      <TableCell className="py-2 px-3 text-right">
        {rowCO2e !== null ? (
          <span className="text-sm font-semibold tabular-nums text-[var(--text-primary)]">
            {rowCO2e.toFixed(2)} <span className="text-[13px] font-normal text-[var(--text-dim)]">kg CO&#8322;e</span>
          </span>
        ) : (
          <span className="text-sm text-[var(--text-dim)]">&mdash;</span>
        )}
      </TableCell>

      {/* Source */}
      <TableCell className="py-2 px-3 text-center">
        {(() => {
          const selectedFactor = emissionFactors.find((f) => f.id === selectedFactorId);
          return selectedFactor && selectedFactor.data_source ? (
            <SourceBadge
              sourceCode={selectedFactor.data_source}
              className="text-[14px]"
            />
          ) : (
            <span className="text-sm text-[var(--text-dim)]">&mdash;</span>
          );
        })()}
      </TableCell>

      {/* Actions */}
      <TableCell className="text-center py-2 px-3">
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

  if (isVirtualized) {
    return renderCells();
  }

  return (
    <TableRow className="border-b border-white/[0.04] transition-colors hover:bg-white/[0.025]">
      {renderCells()}
    </TableRow>
  );
});

BOMTableRow.displayName = 'BOMTableRow';

export default BOMTableRow;
