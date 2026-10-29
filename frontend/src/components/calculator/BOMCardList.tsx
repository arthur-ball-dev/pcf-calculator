/**
 * BOMCardList Component
 *
 * Mobile-optimized card list for BOM items.
 * TASK-FE-P7-010: Mobile BOM Card View
 * TASK-FE-P8-005: Integrate SourceBadge for data source attribution
 * Emerald Night 5B: Glassmorphic dark cards, pill quantity controls, category dots
 *
 * Features:
 * - Card-based layout for better mobile readability
 * - Touch-friendly buttons (>= 44x44px)
 * - Pill-shaped quantity controls (- | value | +)
 * - Confirmation dialog for item removal
 * - Category badges with colored dots
 * - Empty state messaging
 * - Read-only mode support
 * - SourceBadge for data source attribution (EPA, DEFRA, PROXY)
 * - Per-card CO2e estimate display
 *
 * Uses:
 * - shadcn/ui Card, Button, Input, Badge, AlertDialog
 * - Lucide icons (Trash2, Minus, Plus)
 * - SourceBadge component for data source attribution
 * - EMISSION_CATEGORY_COLORS for category dot colors
 */

import { useState, useMemo, useCallback } from 'react';
import { Button } from '@/components/ui/button';
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
import { Trash2, Minus, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SourceBadge } from '@/components/attribution/SourceBadge';
import { EMISSION_CATEGORY_COLORS } from '@/constants/colors';
import type { EmissionFactor } from '@/hooks/useEmissionFactors';

interface BOMItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: 'material' | 'energy' | 'transport' | 'combustion' | 'other';
  emissionFactorId?: string | null;
  /** TASK-FE-P8-005: Data source code for SourceBadge (EPA, DEFRA, PROXY) */
  data_source?: string;
}

interface BOMCardListProps {
  items: BOMItem[];
  onUpdate: (id: string, updates: Partial<BOMItem>) => void;
  onRemove: (id: string) => void;
  isReadOnly?: boolean;
  className?: string;
  /** Emission factors for calculating per-card CO2e */
  emissionFactors?: EmissionFactor[];
}

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
 * Mobile-optimized card list for BOM items.
 * Provides larger touch targets and better readability on small screens.
 * Styled with Emerald Night 5B glassmorphic dark theme.
 */
export function BOMCardList({
  items,
  onUpdate,
  onRemove,
  isReadOnly = false,
  className,
  emissionFactors = [],
}: BOMCardListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  /**
   * Start editing a card's quantity
   */
  const handleStartEdit = useCallback((item: BOMItem) => {
    setEditingId(item.id);
    setEditValue(item.quantity.toString());
  }, []);

  /**
   * Save the edited quantity
   */
  const handleSaveEdit = useCallback((id: string) => {
    const quantity = parseFloat(editValue);
    if (!isNaN(quantity) && quantity > 0) {
      onUpdate(id, { quantity });
    }
    setEditingId(null);
    setEditValue('');
  }, [editValue, onUpdate]);

  /**
   * Cancel editing without saving
   */
  const handleCancelEdit = useCallback(() => {
    setEditingId(null);
    setEditValue('');
  }, []);

  /**
   * Handle quantity step via pill buttons
   */
  const handleQuantityStep = useCallback((item: BOMItem, delta: number) => {
    const newValue = Math.max(0.01, item.quantity + delta);
    const rounded = Math.round(newValue * 100) / 100;
    onUpdate(item.id, { quantity: rounded });
  }, [onUpdate]);

  /**
   * Calculate CO2e for a single item
   */
  const getItemCO2e = useCallback((item: BOMItem): number | null => {
    if (!item.emissionFactorId || emissionFactors.length === 0) return null;
    const factor = emissionFactors.find(f => f.id === item.emissionFactorId);
    if (!factor) return null;
    return item.quantity * factor.co2e_factor;
  }, [emissionFactors]);

  /**
   * Calculate total CO2e across all items
   */
  const totalCO2e = useMemo(() => {
    let total = 0;
    let hasAny = false;
    for (const item of items) {
      const co2e = getItemCO2e(item);
      if (co2e !== null) {
        hasAny = true;
        total += co2e;
      }
    }
    return hasAny ? total : null;
  }, [items, getItemCO2e]);

  // Empty state
  if (items.length === 0) {
    return (
      <div className={cn('text-center py-8 text-[var(--text-muted)]', className)}>
        <p className="text-lg mb-2">No components added yet</p>
        <p className="text-sm text-[var(--text-dim)]">Add components to your Bill of Materials to continue</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)} data-tour="bom-table">
      {/* Card header */}
      <div className="flex items-center justify-between px-1">
        <h2 className="font-heading text-base font-semibold text-[var(--text-primary)]">
          Bill of Materials
        </h2>
        <span className="text-[13px] text-[var(--text-dim)]">
          {items.length} item{items.length !== 1 ? 's' : ''}
        </span>
      </div>

      {items.map((item) => {
        const catConfig = CATEGORY_CONFIG[item.category] || CATEGORY_CONFIG.other;
        const itemCO2e = getItemCO2e(item);
        const isEditing = editingId === item.id;

        return (
          <div
            key={item.id}
            className="glass-card overflow-hidden"
            data-testid={`bom-card-${item.id}`}
          >
            {/* Card Header - Name, category, and actions */}
            <div className="px-4 pt-4 pb-2">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-base text-[var(--text-primary)] truncate">
                    {item.name || 'Unnamed Component'}
                  </h3>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    {/* Category badge with colored dot */}
                    <span
                      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[12px] font-semibold tracking-[0.02em] whitespace-nowrap"
                      style={{
                        background: catConfig.bgColor,
                        color: catConfig.color,
                        border: `1px solid ${catConfig.borderColor}`,
                      }}
                    >
                      <span
                        className="w-[6px] h-[6px] rounded-full flex-shrink-0"
                        style={{ background: catConfig.color }}
                      />
                      {catConfig.label}
                    </span>
                    {/* Source badge */}
                    {item.data_source && item.data_source.trim() !== '' && (
                      <SourceBadge sourceCode={item.data_source} />
                    )}
                  </div>
                </div>
                {/* Delete button */}
                {!isReadOnly && (
                  <div className="flex-shrink-0">
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-11 w-11 text-destructive hover:text-destructive hover:bg-destructive/10"
                          data-testid={`remove-btn-${item.id}`}
                          aria-label={`Remove ${item.name}`}
                        >
                          <Trash2 className="h-5 w-5" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Remove Component</AlertDialogTitle>
                          <AlertDialogDescription>
                            Are you sure you want to remove "{item.name}" from the Bill of Materials?
                            This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() => onRemove(item.id)}
                            data-testid="confirm-remove-btn"
                          >
                            Remove
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                )}
              </div>
            </div>

            {/* Card Body - Quantity controls and CO2e */}
            <div className="px-4 pb-4">
              <div className="flex items-center justify-between gap-3">
                {/* Quantity section */}
                <div className="flex items-center gap-2">
                  <span className="text-[13px] text-[var(--text-dim)]">Qty:</span>
                  {isReadOnly ? (
                    <span className="font-mono font-medium text-base tabular-nums text-[var(--text-primary)]">
                      {item.quantity.toLocaleString()} {item.unit}
                    </span>
                  ) : isEditing ? (
                    <div className="flex items-center gap-1.5">
                      <input
                        type="number"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-20 h-[34px] text-center text-sm font-medium tabular-nums text-[var(--text-primary)] bg-white/[0.06] border border-emerald-500/50 rounded-lg outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        min="0"
                        step="any"
                        autoFocus
                        data-testid={`quantity-input-${item.id}`}
                        aria-label="Quantity"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(item.id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                      />
                      <span className="text-[13px] text-[var(--text-dim)]">{item.unit}</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleSaveEdit(item.id)}
                        className="h-9 w-9 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                        data-testid={`save-btn-${item.id}`}
                        aria-label="Save quantity"
                      >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleCancelEdit}
                        className="h-9 w-9 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/[0.06]"
                        data-testid={`cancel-btn-${item.id}`}
                        aria-label="Cancel edit"
                      >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      {/* Pill quantity control */}
                      <div className="inline-flex items-center bg-white/[0.04] border border-white/[0.08] rounded-lg overflow-hidden">
                        <button
                          type="button"
                          className="w-[34px] h-[34px] flex items-center justify-center text-[var(--text-muted)] hover:bg-white/[0.06] hover:text-[var(--text-primary)] transition-colors touch-target"
                          onClick={() => handleQuantityStep(item, -1)}
                          aria-label="Decrease quantity"
                        >
                          <Minus className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          className="min-w-[56px] h-[34px] px-2 text-center text-sm font-medium tabular-nums text-[var(--text-primary)] bg-transparent border-x border-white/[0.08] hover:bg-white/[0.04] transition-colors"
                          onClick={() => handleStartEdit(item)}
                          data-testid={`edit-btn-${item.id}`}
                          aria-label={`Edit ${item.name} quantity`}
                        >
                          {item.quantity.toLocaleString()}
                        </button>
                        <button
                          type="button"
                          className="w-[34px] h-[34px] flex items-center justify-center text-[var(--text-muted)] hover:bg-white/[0.06] hover:text-[var(--text-primary)] transition-colors touch-target"
                          onClick={() => handleQuantityStep(item, 1)}
                          aria-label="Increase quantity"
                        >
                          <Plus className="w-4 h-4" />
                        </button>
                      </div>
                      <span className="text-[13px] text-[var(--text-dim)]">{item.unit}</span>
                    </div>
                  )}
                </div>

                {/* Per-card CO2e */}
                {itemCO2e !== null && (
                  <div className="text-right flex-shrink-0">
                    <span className="text-sm font-semibold tabular-nums text-[var(--text-primary)]">
                      {itemCO2e.toFixed(2)}
                    </span>
                    <span className="text-[11px] text-[var(--text-dim)] ml-1">kg CO&#8322;e</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}

      {/* Total CO2e footer */}
      {totalCO2e !== null && (
        <div className="glass-card px-4 py-3 bg-emerald-500/[0.04] border-emerald-500/[0.15]">
          <div className="flex items-center justify-between">
            <span className="font-heading font-bold text-[14px] text-[var(--text-primary)]">
              Total Estimated CO&#8322;e
            </span>
            <span className="font-heading text-base font-bold tabular-nums text-emerald-400">
              {totalCO2e.toFixed(2)} <span className="text-[12px] font-normal text-[var(--text-dim)]">kg CO&#8322;e</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default BOMCardList;
