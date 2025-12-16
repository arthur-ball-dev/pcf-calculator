/**
 * useUndoRedoKeyboard Hook
 *
 * Provides keyboard shortcuts for undo/redo functionality.
 * Shortcuts:
 * - Ctrl+Z / Cmd+Z: Undo
 * - Ctrl+Shift+Z / Cmd+Shift+Z: Redo
 * - Ctrl+Y / Cmd+Y: Redo (Windows alternative)
 *
 * Features:
 * - Shortcuts disabled when input/textarea/contentEditable focused
 * - Cleanup on unmount
 * - Configurable enable/disable
 *
 * TASK-FE-P5-003
 */

import { useEffect, useCallback } from 'react';
import { useCalculatorStore } from '@/store/calculatorStore';

// ============================================================================
// Types
// ============================================================================

interface UseUndoRedoKeyboardOptions {
  enabled?: boolean;
}

interface UseUndoRedoKeyboardReturn {
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if an element is an editable input that should capture undo/redo
 */
function isEditableElement(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) {
    return false;
  }

  // Check tag names for form inputs
  const tagName = target.tagName.toLowerCase();
  if (tagName === 'input' || tagName === 'textarea' || tagName === 'select') {
    return true;
  }

  // Check contentEditable - use multiple methods for robustness
  // 1. Check the isContentEditable boolean getter (standard)
  if (target.isContentEditable === true) {
    return true;
  }

  // 2. Check the contentEditable property directly (string value)
  // This handles JSDOM where isContentEditable might not work as expected
  const contentEditableProp = target.contentEditable;
  if (contentEditableProp === 'true') {
    return true;
  }

  // 3. Fallback: check the attribute
  const contentEditableAttr = target.getAttribute('contenteditable');
  if (contentEditableAttr === 'true' || contentEditableAttr === '') {
    return true;
  }

  return false;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useUndoRedoKeyboard(
  options: UseUndoRedoKeyboardOptions = {}
): UseUndoRedoKeyboardReturn {
  const { enabled = true } = options;

  // Get store actions and state selectors
  const undo = useCalculatorStore((state) => state.undo);
  const redo = useCalculatorStore((state) => state.redo);
  const canUndo = useCalculatorStore((state) => state.canUndo);
  const canRedo = useCalculatorStore((state) => state.canRedo);

  /**
   * Handle keyboard events for undo/redo
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Check for modifier key (Ctrl or Cmd)
      const hasModifier = event.ctrlKey || event.metaKey;
      if (!hasModifier) {
        return;
      }

      // Skip if focused on editable element (let browser handle native undo)
      if (isEditableElement(event.target)) {
        return;
      }

      const key = event.key.toLowerCase();

      // Redo: Ctrl+Shift+Z / Cmd+Shift+Z OR Ctrl+Y / Cmd+Y
      if ((key === 'z' && event.shiftKey) || key === 'y') {
        event.preventDefault();
        if (canRedo()) {
          redo();
        }
        return;
      }

      // Undo: Ctrl+Z / Cmd+Z (without Shift)
      if (key === 'z' && !event.shiftKey) {
        event.preventDefault();
        if (canUndo()) {
          undo();
        }
        return;
      }
    },
    [undo, redo, canUndo, canRedo]
  );

  /**
   * Register/unregister keyboard event listener
   */
  useEffect(() => {
    if (!enabled) {
      return;
    }

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, handleKeyDown]);

  return {
    undo,
    redo,
    canUndo,
    canRedo,
  };
}
