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
 * - Progressive rendering to prevent UI blocking (Performance optimization)
 *
 * Uses:
 * - React Hook Form with useFieldArray
 * - Zod validation schema
 * - shadcn/ui components (Table, Input, Select, Button, Tooltip)
 * - useBreakpoints hook for responsive behavior
 * - @tanstack/react-virtual for list virtualization
 */

import React, { useEffect, useRef, useCallback, useState } from 'react';
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
import { useEmissionFactors, type EmissionFactor } from '@/hooks/useEmissionFactors';
import { generateId } from '@/lib/utils';
import { classifyComponent } from '@/utils/classifyComponent';
import type { BOMItem } from '@/types/store.types';

/**
 * Configuration for virtualization
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
 */
function classifyBOMItems(items: BOMItem[]): BOMItem[] {
  return items.map((item) => {
    const classified = classifyComponent(item.name);
    const formCategory = classified === 'materials' ? 'material' : classified;
    return { ...item, category: formCategory };
  });
}

/**
 * Loading skeleton component for BOM Editor
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
 * Props for the inner form component
 */
interface BOMEditorFormProps {
  emissionFactors: EmissionFactor[];
  isLoadingFactors: boolean;
}

/**
 * Inner form component - contains all the heavy form logic
 * Separated to allow progressive rendering without violating React's rules of hooks
 */
const BOMEditorForm: React.FC<BOMEditorFormProps> = ({ emissionFactors, isLoadingFactors }) => {
  const { bomItems, setBomItems } = useCalculatorStore();
  const { markStepComplete, markStepIncomplete } = useWizardStore();
  const { isMobile } = useBreakpoints();

  const parentRef = useRef<HTMLDivElement>(null);
  const lastBomItemsRef = useRef<string>('');

  const form = useForm<BOMFormData>({
    resolver: zodResolver(bomFormSchema),
    defaultValues: {
      items: bomItems.length > 0
        ? classifyBOMItems(JSON.parse(JSON.stringify(bomItems)))
        : [{ id: generateId(), ...DEFAULT_BOM_ITEM }],
    },
    mode: 'onChange',
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'items',
    keyName: 'fieldId',
  });

  const { formState: { isValid, errors } } = form;
  const useVirtualization = fields.length >= VIRTUALIZATION_THRESHOLD;

  const rowVirtualizer = useVirtualizer({
    count: fields.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: OVERSCAN,
  });

  useEffect(() => {
    const currentBomJson = JSON.stringify(bomItems);
    if (currentBomJson === lastBomItemsRef.current) return;
    if (bomItems.length > 0) {
      const classifiedItems = classifyBOMItems(JSON.parse(currentBomJson));
      lastBomItemsRef.current = JSON.stringify(classifiedItems);
      form.reset({ items: classifiedItems });
    }
  }, [bomItems, form]);

  useEffect(() => {
    if (isValid) {
      markStepComplete('edit');
    } else {
      markStepIncomplete('edit');
    }
  }, [isValid, markStepComplete, markStepIncomplete]);

  useEffect(() => {
    const subscription = form.watch((data) => {
      if (data.items && isValid) {
        lastBomItemsRef.current = JSON.stringify(data.items);
        setBomItems(data.items as BOMItem[]);
      }
    });
    return () => subscription.unsubscribe();
  }, [form, setBomItems, isValid]);

  const handleAddComponent = () => {
    const newItem: BOMItem = { id: generateId(), ...DEFAULT_BOM_ITEM };
    append(newItem);
    setTimeout(() => {
      const newIndex = fields.length;
      document.getElementById(`items.${newIndex}.name`)?.focus();
    }, 0);
  };

  const handleRemoveComponent = (index: number) => {
    if (fields.length <= 1) return;
    remove(index);
  };

  const handleCardUpdate = useCallback((id: string, updates: Partial<BOMItem>) => {
    const itemIndex = fields.findIndex((field) => field.id === id);
    if (itemIndex !== -1 && updates.quantity !== undefined) {
      const fieldPath = `items.${itemIndex}.quantity` as FieldPath<BOMFormData>;
      form.setValue(fieldPath, updates.quantity, { shouldValidate: true, shouldDirty: true });
    }
  }, [fields, form]);

  const handleCardRemove = useCallback((id: string) => {
    const itemIndex = fields.findIndex((field) => field.id === id);
    if (itemIndex !== -1 && fields.length > 1) {
      remove(itemIndex);
    }
  }, [fields, remove]);

  const totals = form.watch('items').reduce(
    (acc, item) => ({
      totalItems: acc.totalItems + 1,
      totalQuantity: acc.totalQuantity + (item.quantity || 0),
    }),
    { totalItems: 0, totalQuantity: 0 }
  );

  const arrayLevelError = errors.items && !Array.isArray(errors.items)
    ? (errors.items as { message?: string }).message
    : null;

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

  const renderTableHeader = () => (
    <TableHeader>
      <TableRow>
        <TableHead className="min-w-[150px]">Component Name</TableHead>
        <TableHead className="min-w-[80px]">Quantity</TableHead>
        <TableHead className="min-w-[70px]">Unit</TableHead>
        <TableHead className="min-w-[100px]">Category</TableHead>
        <TableHead className="min-w-[180px]">Emission Factor</TableHead>
        <TableHead className="min-w-[60px]">Source</TableHead>
        <TableHead className="min-w-[50px] text-right">Actions</TableHead>
      </TableRow>
    </TableHeader>
  );

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
                emissionFactors={emissionFactors}
                isLoadingFactors={isLoadingFactors}
              />
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );

  const renderVirtualizedTable = () => {
    const virtualItems = rowVirtualizer.getVirtualItems();
    return (
      <div className="border rounded-lg overflow-hidden" data-tour="bom-table">
        <div className="overflow-x-auto">
          <Table>{renderTableHeader()}</Table>
          <div
            ref={parentRef}
            data-testid="bom-virtual-scroll-container"
            className="overflow-y-auto"
            style={{ height: `${CONTAINER_HEIGHT}px` }}
          >
            <div style={{ height: `${rowVirtualizer.getTotalSize()}px`, width: '100%', position: 'relative' }}>
              {virtualItems.map((virtualRow) => {
                const field = fields[virtualRow.index];
                return (
                  <div
                    key={field.fieldId}
                    data-testid="bom-virtual-row"
                    className="absolute w-full"
                    style={{ top: 0, left: 0, height: `${virtualRow.size}px`, transform: `translateY(${virtualRow.start}px)` }}
                  >
                    <Table>
                      <TableBody>
                        <BOMTableRow
                          field={field}
                          index={virtualRow.index}
                          form={form}
                          onRemove={() => handleRemoveComponent(virtualRow.index)}
                          canRemove={fields.length > 1}
                          emissionFactors={emissionFactors}
                          isLoadingFactors={isLoadingFactors}
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
        {isMobile ? (
          <BOMCardList items={cardItems} onUpdate={handleCardUpdate} onRemove={handleCardRemove} isReadOnly={false} className="mt-4" />
        ) : (
          useVirtualization ? renderVirtualizedTable() : renderNonVirtualizedTable()
        )}

        {arrayLevelError && (
          <div className="text-sm text-destructive" role="alert">{arrayLevelError}</div>
        )}

        <div className="flex items-center justify-between gap-4">
          <Button type="button" variant="outline" onClick={handleAddComponent} className="gap-2">
            <Plus className="w-4 h-4" />
            Add Component
          </Button>
          <div className="text-sm text-muted-foreground">
            {totals.totalItems} component{totals.totalItems !== 1 ? 's' : ''} · Total quantity: {totals.totalQuantity.toFixed(2)}
          </div>
        </div>

        {!isValid && Object.keys(errors).length > 0 && (
          <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
            <p className="text-sm font-medium text-destructive mb-2">Please fix the following errors:</p>
            <ul className="text-sm text-destructive list-disc list-inside space-y-1">
              {arrayLevelError && <li>{arrayLevelError}</li>}
              {Array.isArray(errors.items) && errors.items.map((itemError, index) => {
                if (!itemError) return null;
                const errorMessages = Object.entries(itemError)
                  .filter(([key]) => key !== 'fieldId' && key !== 'id')
                  .map(([, error]) => (error as { message?: string })?.message)
                  .filter(Boolean);
                if (errorMessages.length === 0) return null;
                return <li key={index}>Row {index + 1}: {errorMessages.join(', ')}</li>;
              })}
            </ul>
          </div>
        )}
      </form>
    </Form>
  );
};

/**
 * BOMEditor - Main wrapper component
 * Handles progressive rendering to prevent UI blocking
 */
export default function BOMEditor() {
  const { isLoadingBOM } = useCalculatorStore();
  const { data: emissionFactors = [], isLoading: isLoadingFactors } = useEmissionFactors();

  // Progressive rendering: defer heavy form rendering to allow loading indicator to paint
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Double rAF ensures browser has painted before we start heavy rendering
    let cancelled = false;
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (!cancelled) setIsReady(true);
      });
    });
    return () => { cancelled = true; };
  }, []);

  // Show skeleton until ready
  if (!isReady || isLoadingBOM) {
    return <BOMEditorSkeleton />;
  }

  return <BOMEditorForm emissionFactors={emissionFactors} isLoadingFactors={isLoadingFactors} />;
}
