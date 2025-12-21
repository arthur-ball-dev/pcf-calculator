/**
 * BOMCardList Component
 *
 * Mobile-optimized card list for BOM items.
 * TASK-FE-P7-010: Mobile BOM Card View
 *
 * Features:
 * - Card-based layout for better mobile readability
 * - Touch-friendly buttons (>= 44x44px)
 * - Inline quantity editing
 * - Confirmation dialog for item removal
 * - Category badges with color coding
 * - Empty state messaging
 * - Read-only mode support
 *
 * Uses:
 * - shadcn/ui Card, Button, Input, Badge, AlertDialog
 * - Lucide icons (Pencil, Trash2, Check, X)
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
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
import { Pencil, Trash2, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BOMItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: 'material' | 'energy' | 'transport' | 'other';
  emissionFactorId?: string | null;
}

interface BOMCardListProps {
  items: BOMItem[];
  onUpdate: (id: string, updates: Partial<BOMItem>) => void;
  onRemove: (id: string) => void;
  isReadOnly?: boolean;
  className?: string;
}

/**
 * Category color mapping for visual differentiation
 */
const categoryColors: Record<BOMItem['category'], string> = {
  material: 'bg-blue-100 text-blue-800',
  energy: 'bg-yellow-100 text-yellow-800',
  transport: 'bg-green-100 text-green-800',
  other: 'bg-gray-100 text-gray-800',
};

/**
 * Mobile-optimized card list for BOM items.
 * Provides larger touch targets and better readability on small screens.
 */
export function BOMCardList({
  items,
  onUpdate,
  onRemove,
  isReadOnly = false,
  className,
}: BOMCardListProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  /**
   * Start editing a card's quantity
   */
  const handleStartEdit = (item: BOMItem) => {
    // If another card is being edited, switch to the new one
    setEditingId(item.id);
    setEditValue(item.quantity.toString());
  };

  /**
   * Save the edited quantity
   */
  const handleSaveEdit = (id: string) => {
    const quantity = parseFloat(editValue);
    if (!isNaN(quantity) && quantity > 0) {
      onUpdate(id, { quantity });
    }
    setEditingId(null);
    setEditValue('');
  };

  /**
   * Cancel editing without saving
   */
  const handleCancelEdit = () => {
    setEditingId(null);
    setEditValue('');
  };

  // Empty state
  if (items.length === 0) {
    return (
      <div className={cn('text-center py-8 text-muted-foreground', className)}>
        <p className="text-lg mb-2">No components added yet</p>
        <p className="text-sm">Add components to your Bill of Materials to continue</p>
      </div>
    );
  }

  return (
    <div className={cn('space-y-3', className)}>
      {items.map((item) => (
        <Card key={item.id} className="overflow-hidden" data-testid={`bom-card-${item.id}`}>
          <CardHeader className="pb-2 px-4 pt-4">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-base truncate">{item.name}</h3>
                <Badge
                  variant="secondary"
                  className={cn('mt-1', categoryColors[item.category])}
                >
                  {item.category}
                </Badge>
              </div>
              {!isReadOnly && (
                <div className="flex gap-1 flex-shrink-0">
                  {editingId === item.id ? (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleSaveEdit(item.id)}
                        className="h-11 w-11"
                        data-testid={`save-btn-${item.id}`}
                        aria-label="Save quantity"
                      >
                        <Check className="h-5 w-5 text-green-600" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={handleCancelEdit}
                        className="h-11 w-11"
                        data-testid={`cancel-btn-${item.id}`}
                        aria-label="Cancel edit"
                      >
                        <X className="h-5 w-5 text-red-600" />
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleStartEdit(item)}
                        className="h-11 w-11"
                        data-testid={`edit-btn-${item.id}`}
                        aria-label={`Edit ${item.name} quantity`}
                      >
                        <Pencil className="h-5 w-5" />
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-11 w-11 text-destructive hover:text-destructive"
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
                    </>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-0 px-4 pb-4">
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Quantity:</span>
              {editingId === item.id ? (
                <Input
                  type="number"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-24 h-10"
                  min="0"
                  step="any"
                  autoFocus
                  data-testid={`quantity-input-${item.id}`}
                  aria-label="Quantity"
                />
              ) : (
                <span className="font-mono font-medium text-lg">
                  {item.quantity.toLocaleString()}
                </span>
              )}
              <span className="text-sm text-muted-foreground">{item.unit}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default BOMCardList;
