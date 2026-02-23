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
 * - Emerald Night 5B glassmorphic design with category dots and quantity controls
 *
 * Uses:
 * - React Hook Form with useFieldArray
 * - Zod validation schema
 * - shadcn/ui components (Table, Input, Select, Button, Tooltip)
 * - useBreakpoints hook for responsive behavior
 * - @tanstack/react-virtual for list virtualization
 */

import React, { useEffect, useRef, useCallback, useState, useMemo } from 'react';
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
  TableCell,
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

  const watchedItems = form.watch('items');

  const totals = useMemo(() => {
    return watchedItems.reduce(
      (acc, item) => ({
        totalItems: acc.totalItems + 1,
        totalQuantity: acc.totalQuantity + (item.quantity || 0),
      }),
      { totalItems: 0, totalQuantity: 0 }
    );
  }, [watchedItems]);

  /**
   * Calculate estimated total CO2e from watched items and emission factors
   */
  const estimatedTotalCO2e = useMemo(() => {
    if (emissionFactors.length === 0) return null;
    let total = 0;
    let hasAnyFactor = false;
    for (const item of watchedItems) {
      if (item.emissionFactorId) {
        const factor = emissionFactors.find(f => f.id === item.emissionFactorId);
        if (factor) {
          hasAnyFactor = true;
          total += (item.quantity || 0) * factor.co2e_factor;
        }
      }
    }
    return hasAnyFactor ? total : null;
  }, [watchedItems, emissionFactors]);

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
    <TableHeader className="bg-white/[0.03]">
      <TableRow className="border-b border-white/[0.08] hover:bg-transparent">
        <TableHead className="w-[14%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)]">Component</TableHead>
        <TableHead className="w-[10%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)]">Category</TableHead>
        <TableHead className="w-[16%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)]">Quantity</TableHead>
        <TableHead className="w-[28%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)]">Emission Factor</TableHead>
        <TableHead className="w-[12%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)] text-right">CO&#8322;e</TableHead>
        <TableHead className="w-[10%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)] text-center">Source</TableHead>
        <TableHead className="w-[10%] text-[11px] font-semibold uppercase tracking-[0.06em] text-[var(--text-dim)] text-center">Actions</TableHead>
      </TableRow>
    </TableHeader>
  );

  /**
   * Render the totals row
   */
  const renderTotalsRow = () => {
    if (estimatedTotalCO2e === null) return null;
    return (
      <TableRow className="bg-emerald-500/[0.04] border-t border-emerald-500/[0.15] hover:bg-emerald-500/[0.06]">
        <TableCell className="py-2 px-3">
          <span className="font-heading font-bold text-[15px] text-[var(--text-primary)]">
            Total Estimated Carbon Footprint
          </span>
        </TableCell>
        <TableCell />
        <TableCell />
        <TableCell />
        <TableCell className="text-right py-2 px-3">
          <span className="font-heading text-lg font-bold tabular-nums text-emerald-400">
            {estimatedTotalCO2e.toFixed(2)} <span className="text-[13px] font-normal text-[var(--text-dim)]">kg CO&#8322;e</span>
          </span>
        </TableCell>
        <TableCell />
        <TableCell />
      </TableRow>
    );
  };

  const renderNonVirtualizedTable = () => (
    <div className="glass-card overflow-hidden animate-fadeInUp" data-tour="bom-table">
      {/* Card Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08]">
        <h2 className="font-heading text-base font-semibold text-[var(--text-primary)]">
          Bill of Materials
        </h2>
        <span className="text-[13px] text-[var(--text-dim)]">
          {fields.length} item{fields.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <Table className="w-full table-fixed">
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
            {renderTotalsRow()}
          </TableBody>
        </Table>
      </div>
    </div>
  );

  const renderVirtualizedTable = () => {
    const virtualItems = rowVirtualizer.getVirtualItems();
    return (
      <div className="glass-card overflow-hidden animate-fadeInUp" data-tour="bom-table">
        {/* Card Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08]">
          <h2 className="font-heading text-base font-semibold text-[var(--text-primary)]">
            Bill of Materials
          </h2>
          <span className="text-[13px] text-[var(--text-dim)]">
            {fields.length} item{fields.length !== 1 ? 's' : ''}
          </span>
        </div>

        <div className="overflow-x-auto">
          <Table className="w-full table-fixed">{renderTableHeader()}</Table>
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
                    <Table className="w-full table-fixed">
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
          {/* Totals row at the bottom of virtualized table */}
          {estimatedTotalCO2e !== null && (
            <Table className="w-full table-fixed">
              <TableBody>
                {renderTotalsRow()}
              </TableBody>
            </Table>
          )}
        </div>
      </div>
    );
  };

  return (
    <Form {...form}>
      <form className="space-y-6">
        {isMobile ? (
          <BOMCardList
            items={cardItems}
            onUpdate={handleCardUpdate}
            onRemove={handleCardRemove}
            isReadOnly={false}
            className="mt-4"
            emissionFactors={emissionFactors}
          />
        ) : (
          useVirtualization ? renderVirtualizedTable() : renderNonVirtualizedTable()
        )}

        {arrayLevelError && (
          <div className="text-sm text-destructive" role="alert">{arrayLevelError}</div>
        )}

        <div className="flex items-center justify-between gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={handleAddComponent}
            className="gap-2 border-white/[0.08] bg-white/[0.04] hover:bg-white/[0.06] hover:border-white/[0.14] text-[var(--text-muted)]"
          >
            <Plus className="w-4 h-4" />
            Add Component
          </Button>
          <div className="text-sm text-[var(--text-dim)]">
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
