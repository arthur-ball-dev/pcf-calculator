/**
 * BOMEditor Component
 *
 * Bill of Materials editor with dynamic field array management.
 * Features:
 * - Add/remove BOM items with minimum 1 item constraint
 * - Inline editing with field-level validation
 * - Real-time totals calculation
 * - Auto-save to Zustand store (debounced)
 * - Wizard step validation integration
 * - Keyboard navigation and accessibility
 * - Loading state display while BOM is being fetched (TASK-FE-019)
 *
 * Uses:
 * - React Hook Form with useFieldArray
 * - Zod validation schema
 * - shadcn/ui components (Table, Input, Select, Button, Tooltip)
 */

import React, { useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Form } from '@/components/ui/form';
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { bomFormSchema, type BOMFormData } from '@/schemas/bomSchema';
import BOMTableRow from './BOMTableRow';
import { generateId } from '@/lib/utils';
import type { BOMItem } from '@/types/store.types';

/**
 * Default values for new BOM item
 */
const DEFAULT_BOM_ITEM: Omit<BOMItem, 'id'> = {
  name: '',
  quantity: 1,
  unit: 'kg',
  category: 'material',
  emissionFactorId: null,
};

/**
 * Loading skeleton component for BOM Editor
 *
 * Displayed while product BOM is being fetched and transformed (TASK-FE-019)
 */
const BOMEditorSkeleton: React.FC = () => {
  return (
    <div className="space-y-4 animate-pulse" data-testid="bom-editor-skeleton">
      <div className="h-8 bg-muted rounded" />
      <div className="h-64 bg-muted rounded" />
    </div>
  );
};

/**
 * BOMEditor - Main component for editing Bill of Materials
 */
export default function BOMEditor() {
  const { bomItems, setBomItems, isLoadingBOM } = useCalculatorStore();
  const { markStepComplete, markStepIncomplete } = useWizardStore();

  // Initialize form with existing BOM items or one default item
  const form = useForm<BOMFormData>({
    resolver: zodResolver(bomFormSchema),
    defaultValues: {
      items: bomItems.length > 0 ? bomItems : [
        {
          id: generateId(),
          ...DEFAULT_BOM_ITEM,
        },
      ],
    },
    mode: 'onChange', // Validate on every change
  });

  // useFieldArray hook for dynamic rows
  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'items',
    keyName: 'fieldId', // Use custom key name to avoid conflicts with 'id' field
  });

  const { formState: { isValid, errors } } = form;

  // Reset form when BOM items change (e.g., after product selection loads BOM)
  useEffect(() => {
    if (bomItems.length > 0) {
      form.reset({
        items: bomItems,
      });
    }
  }, [bomItems, form]);

  // Update wizard step validation when form validity changes
  useEffect(() => {
    if (isValid) {
      markStepComplete('edit');
    } else {
      markStepIncomplete('edit');
    }
  }, [isValid, markStepComplete, markStepIncomplete]);

  // Sync form data to store on change (debounced for performance)
  useEffect(() => {
    const subscription = form.watch((data) => {
      if (data.items && isValid) {
        setBomItems(data.items as BOMItem[]);
      }
    });
    return () => subscription.unsubscribe();
  }, [form, setBomItems, isValid]);

  /**
   * Add new component row
   * Appends a new item with default values and focuses the name field
   */
  const handleAddComponent = () => {
    const newItem: BOMItem = {
      id: generateId(),
      ...DEFAULT_BOM_ITEM,
    };

    append(newItem);

    // Focus the name field of the newly added row
    setTimeout(() => {
      const newIndex = fields.length;
      const nameInput = document.getElementById(`items.${newIndex}.name`);
      nameInput?.focus();
    }, 0);
  };

  /**
   * Remove component row
   * Prevents removing the last item (minimum 1 constraint)
   */
  const handleRemoveComponent = (index: number) => {
    if (fields.length <= 1) {
      // Prevent removing the last item
      return;
    }
    remove(index);
  };

  /**
   * Calculate totals for display
   */
  const totals = form.watch('items').reduce(
    (acc, item) => {
      return {
        totalItems: acc.totalItems + 1,
        totalQuantity: acc.totalQuantity + (item.quantity || 0),
      };
    },
    { totalItems: 0, totalQuantity: 0 }
  );

  // Show loading skeleton while BOM is being fetched (TASK-FE-019)
  // Must be AFTER hooks are initialized to comply with React Rules of Hooks
  if (isLoadingBOM) {
    return <BOMEditorSkeleton />;
  }

  // Extract array-level error message (e.g., duplicate names)
  // Zod array refinements create errors at errors.items with message property
  const arrayLevelError = errors.items && !Array.isArray(errors.items)
    ? (errors.items as { message?: string }).message
    : null;

  return (
    <Form {...form}>
      <form className="space-y-6">
        {/* BOM Table */}
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[250px]">Component Name</TableHead>
                  <TableHead className="w-[120px]">Quantity</TableHead>
                  <TableHead className="w-[100px]">Unit</TableHead>
                  <TableHead className="w-[140px]">Category</TableHead>
                  <TableHead className="w-[250px]">Emission Factor</TableHead>
                  <TableHead className="w-[80px] text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {fields.map((field, index) => (
                  <BOMTableRow
                    key={field.fieldId}
                    field={field}
                    index={index}
                    form={form}
                    onRemove={() => handleRemoveComponent(index)}
                    canRemove={fields.length > 1}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Array-level validation errors (e.g., duplicate names) */}
        {arrayLevelError && (
          <div className="text-sm text-destructive" role="alert">
            {arrayLevelError}
          </div>
        )}

        {/* Add component button and totals */}
        <div className="flex items-center justify-between gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleAddComponent}
            className="gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Component
          </Button>

          <div className="text-sm text-muted-foreground">
            {totals.totalItems} component{totals.totalItems !== 1 ? 's' : ''} ·
            Total quantity: {totals.totalQuantity.toFixed(2)}
          </div>
        </div>

        {/* Validation summary */}
        {!isValid && Object.keys(errors).length > 0 && (
          <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
            <p className="text-sm font-medium text-destructive mb-2">
              Please fix the following errors:
            </p>
            <ul className="text-sm text-destructive list-disc list-inside space-y-1">
              {/* Array-level error */}
              {arrayLevelError && (
                <li>{arrayLevelError}</li>
              )}

              {/* Field-level errors */}
              {Array.isArray(errors.items) && errors.items.map((itemError, index) => {
                if (!itemError) return null;

                const errorMessages = Object.entries(itemError)
                  .filter(([key]) => key !== 'fieldId' && key !== 'id')
                  .map(([, error]) => (error as { message?: string })?.message)
                  .filter(Boolean);

                if (errorMessages.length === 0) return null;

                return (
                  <li key={index}>
                    Row {index + 1}: {errorMessages.join(', ')}
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </form>
    </Form>
  );
}
