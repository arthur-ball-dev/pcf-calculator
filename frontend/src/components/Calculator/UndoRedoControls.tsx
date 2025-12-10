/**
 * UndoRedoControls Component
 *
 * Toolbar component for undo/redo functionality.
 * Features:
 * - Undo button with Ctrl+Z shortcut hint
 * - Redo button with Ctrl+Shift+Z shortcut hint
 * - Buttons disabled when action not available
 * - Tooltips showing keyboard shortcuts and history count
 * - Full accessibility support (ARIA labels, keyboard navigation)
 * - Configurable size and variant via shadcn/ui Button
 *
 * TASK-FE-P5-003
 */

import React, { useState } from 'react';
import { Undo2, Redo2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCalculatorStore } from '@/store/calculatorStore';

// ============================================================================
// Types
// ============================================================================

interface UndoRedoControlsProps {
  className?: string;
  size?: 'sm' | 'default' | 'lg' | 'icon' | 'icon-sm' | 'icon-lg';
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  showHistoryCount?: boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format history count text with proper pluralization
 */
function formatHistoryCount(count: number): string {
  if (count === 0) return '';
  if (count === 1) return '1 change';
  return `${count} changes`;
}

// ============================================================================
// Simple Tooltip Component (avoids Radix duplication issues)
// ============================================================================

interface SimpleTooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
}

function SimpleTooltip({ content, children }: SimpleTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 overflow-hidden rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground whitespace-nowrap"
        >
          {content}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Component Implementation
// ============================================================================

export function UndoRedoControls({
  className,
  size = 'sm',
  variant = 'ghost',
  showHistoryCount = true,
}: UndoRedoControlsProps) {
  // Get store actions and state
  const undo = useCalculatorStore((state) => state.undo);
  const redo = useCalculatorStore((state) => state.redo);
  const canUndo = useCalculatorStore((state) => state.canUndo);
  const canRedo = useCalculatorStore((state) => state.canRedo);
  const getHistoryLength = useCalculatorStore((state) => state.getHistoryLength);

  // Get current history counts (safely handle undefined/null)
  const historyLength = getHistoryLength?.() ?? { past: 0, future: 0 };
  const pastCount = historyLength?.past ?? 0;
  const futureCount = historyLength?.future ?? 0;

  // Evaluate button states
  const isUndoDisabled = !canUndo();
  const isRedoDisabled = !canRedo();

  // Build tooltip content
  const undoTooltipContent = (
    <>
      <span>Undo (Ctrl+Z)</span>
      {showHistoryCount && pastCount > 0 && (
        <span className="text-xs text-muted-foreground block">{formatHistoryCount(pastCount)}</span>
      )}
    </>
  );

  const redoTooltipContent = (
    <>
      <span>Redo (Ctrl+Shift+Z)</span>
      {showHistoryCount && futureCount > 0 && (
        <span className="text-xs text-muted-foreground block">{formatHistoryCount(futureCount)}</span>
      )}
    </>
  );

  return (
    <div
      className={`flex items-center gap-1 ${className || ''}`}
      data-testid="undo-redo-toolbar"
      role="group"
      aria-label="Undo and Redo controls"
    >
      {/* Undo Button */}
      <SimpleTooltip content={undoTooltipContent}>
        <Button
          variant={variant}
          size={size}
          onClick={undo}
          disabled={isUndoDisabled}
          data-testid="undo-button"
          aria-label="Undo"
        >
          <Undo2 className="h-4 w-4" />
        </Button>
      </SimpleTooltip>

      {/* Redo Button */}
      <SimpleTooltip content={redoTooltipContent}>
        <Button
          variant={variant}
          size={size}
          onClick={redo}
          disabled={isRedoDisabled}
          data-testid="redo-button"
          aria-label="Redo"
        >
          <Redo2 className="h-4 w-4" />
        </Button>
      </SimpleTooltip>
    </div>
  );
}
