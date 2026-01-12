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
 * - Responsive view switching: card view on mobile, table on desktop (TASK-FE-P7-010)
 * - List virtualization for large BOM lists (20+ items) (TASK-FE-P8-007)
 *
 * Uses:
 * - React Hook Form with useFieldArray
 * - Zod validation schema
 * - shadcn/ui components (Table, Input, Select, Button, Tooltip)
 * - useBreakpoints hook for responsive behavior
 * - @tanstack/react-virtual for list virtualization
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { useForm, useFieldArray, type FieldPath } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useVirtualizer } from '@tanstack/react-virtual';
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
import { BOMCardList } from '@/components/calculator/BOMCardList';
import { useBreakpoints } from '@/hooks/useBreakpoints';
import { generateId } from '@/lib/utils';
import { classifyComponent } from '@/utils/classifyComponent';
import type { BOMItem } from '@/types/store.types';

/**
 * Configuration for virtualization
 * VIRTUALIZATION_THRESHOLD: Number of items above which virtualization kicks in
 * ROW_HEIGHT: Estimated height of each row in pixels
 * OVERSCAN: Number of extra rows to render above/below viewport for smooth scrolling
 * CONTAINER_HEIGHT: Fixed height for the virtualized scroll container
 */
const VIRTUALIZATION_THRESHOLD = 20;
const ROW_HEIGHT = 64;
const OVERSCAN = 5;
const CONTAINER_HEIGHT = 400;

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
 * Auto-classify BOM items based on component name
 * Maps classification results to form category values
 */
function classifyBOMItems(items: BOMItem[]): BOMItem[] {
  return items.map((item) => {
    const classified = classifyComponent(item.name);
    // Map 'materials' to 'material' for form value
    const formCategory = classified === 'materials' ? 'material' : classified;
    return {
      ...item,
      category: formCategory,
    };
  });
}

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
  const { isMobile } = useBreakpoints();

  // Ref for the virtualized scroll container
  const parentRef = useRef<HTMLDivElement>(null);

  // Track the last bomItems JSON to detect external vs local changes
  // This prevents circular updates: form -> store -> form.reset
  const lastBomItemsRef = useRef<string>('');

  // Initialize form with existing BOM items or one default item
  // Deep copy bomItems to avoid mutating frozen Zustand state
  // Auto-classify categories based on component names
  const form = useForm<BOMFormData>({
    resolver: zodResolver(bomFormSchema),
    defaultValues: {
      items: bomItems.length > 0
        ? classifyBOMItems(JSON.parse(JSON.stringify(bomItems)))
        : [
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

  // Determine if virtualization should be used based on item count
  const useVirtualization = fields.length >= VIRTUALIZATION_THRESHOLD;

  // Initialize virtualizer for large lists
  const rowVirtualizer = useVirtualizer({
    count: fields.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: OVERSCAN,
  });

  // Reset form when BOM items change EXTERNALLY (e.g., after product selection loads BOM)
  // Skip reset if the change came from our own form (prevents circular updates)
  // Auto-classify categories based on component names
  useEffect(() => {
    const currentBomJson = JSON.stringify(bomItems);

    // Skip if this change came from our form's sync to store
    if (currentBomJson === lastBomItemsRef.current) {
      return;
    }

    // Only reset if we have items and it's an external change
    if (bomItems.length > 0) {
      const classifiedItems = classifyBOMItems(JSON.parse(currentBomJson));
      lastBomItemsRef.current = JSON.stringify(classifiedItems);
      form.reset({
        items: classifiedItems,
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

  // Sync form data to store on change
  useEffect(() => {
    const subscription = form.watch((data) => {
      if (data.items && isValid) {
        // Store the JSON so we can detect this update in the reset effect
        lastBomItemsRef.current = JSON.stringify(data.items);
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
   * Handle update from card view
   * Updates a BOM item's properties via the form
   */
  const handleCardUpdate = useCallback((id: string, updates: Partial<BOMItem>) => {
    const itemIndex = fields.findIndex((field) => field.id === id);
    if (itemIndex !== -1) {
      // Update quantity field specifically (the main use case for card view)
      if (updates.quantity !== undefined) {
        const fieldPath = `items.${itemIndex}.quantity` as FieldPath<BOMFormData>;
        form.setValue(fieldPath, updates.quantity, {
          shouldValidate: true,
          shouldDirty: true,
        });
      }
    }
  }, [fields, form]);

  /**
   * Handle remove from card view
   * Removes a BOM item by its ID
   */
  const handleCardRemove = useCallback((id: string) => {
    const itemIndex = fields.findIndex((field) => field.id === id);
    if (itemIndex !== -1 && fields.length > 1) {
      remove(itemIndex);
    }
  }, [fields, remove]);

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

  // Convert form fields to BOMItem array for card view
  const cardItems: BOMItem[] = fields.map((field, index) => {
    const values = form.getValues(`items.${index}`);
    return {
      id: field.id,
      name: values.name || '',
      quantity: values.quantity || 0,
      unit: values.unit || 'kg',
      category: (values.category || 'material') as BOMItem['category'],
      emissionFactorId: values.emissionFactorId || null,
    };
  });

  /**
   * Render the table header (shared between virtualized and non-virtualized views)
   */
  const renderTableHeader = () => (
    <TableHeader>
      <TableRow>
        <TableHead className="min-w-[200px]">Component Name</TableHead>
        <TableHead className="min-w-[100px]">Quantity</TableHead>
        <TableHead className="min-w-[80px]">Unit</TableHead>
        <TableHead className="min-w-[120px]">Category</TableHead>
        <TableHead className="min-w-[250px]">Emission Factor</TableHead>
        <TableHead className="min-w-[80px]">Source</TableHead>
        <TableHead className="min-w-[60px] text-right">Actions</TableHead>
      </TableRow>
    </TableHeader>
  );

  /**
   * Render non-virtualized table body (for small lists)
   */
  const renderNonVirtualizedTable = () => (
    <div className="border rounded-lg overflow-hidden" data-tour="bom-table">
      <div className="overflow-x-auto">
        <Table>
          {renderTableHeader()}
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
  );

  /**
   * Render virtualized table body (for large lists - TASK-FE-P8-007)
   * Uses @tanstack/react-virtual for efficient rendering of only visible rows
   *
   * Note: We use a standard Table for the header and a separate scrollable
   * container for the virtualized body to ensure proper header alignment.
   */
  const renderVirtualizedTable = () => {
    const virtualItems = rowVirtualizer.getVirtualItems();

    return (
      <div className="border rounded-lg overflow-hidden" data-tour="bom-table">
        <div className="overflow-x-auto">
          {/* Fixed header table */}
          <Table>
            {renderTableHeader()}
          </Table>

          {/* Virtualized scroll container */}
          <div
            ref={parentRef}
            data-testid="bom-virtual-scroll-container"
            className="overflow-y-auto"
            style={{ height: `${CONTAINER_HEIGHT}px` }}
          >
            {/* Inner container that sets the total scrollable height */}
            <div
              style={{
                height: `${rowVirtualizer.getTotalSize()}px`,
                width: '100%',
                position: 'relative',
              }}
            >
              {/* Render only visible rows using absolute positioning */}
              {virtualItems.map((virtualRow) => {
                const field = fields[virtualRow.index];
                return (
                  <div
                    key={field.fieldId}
                    data-testid="bom-virtual-row"
                    className="absolute w-full"
                    style={{
                      top: 0,
                      left: 0,
                      height: `${virtualRow.size}px`,
                      transform: `translateY(${virtualRow.start}px)`,
                    }}
                  >
                    <Table>
                      <TableBody>
                        <BOMTableRow
                          field={field}
                          index={virtualRow.index}
                          form={form}
                          onRemove={() => handleRemoveComponent(virtualRow.index)}
                          canRemove={fields.length > 1}
                        />
                      </TableBody>
                    </Table>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Form {...form}>
      <form className="space-y-6">
        {/* Responsive BOM View: Card on mobile, Table on desktop */}
        {isMobile ? (
          /* Mobile Card View (TASK-FE-P7-010) */
          <BOMCardList
            items={cardItems}
            onUpdate={handleCardUpdate}
            onRemove={handleCardRemove}
            isReadOnly={false}
            className="mt-4"
          />
        ) : (
          /* Desktop Table View - Use virtualization for large lists */
          useVirtualization ? renderVirtualizedTable() : renderNonVirtualizedTable()
        )}

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
