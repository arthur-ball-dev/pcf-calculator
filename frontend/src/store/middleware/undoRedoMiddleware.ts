/**
 * Undo/Redo Middleware for Zustand
 *
 * Implements undo/redo functionality using Immer patches.
 * Features:
 * - undo() reverts to previous state
 * - redo() restores undone state
 * - canUndo()/canRedo() boundary conditions
 * - History limited to configurable entries (default 50)
 * - clearHistory() empties past and future
 * - getHistoryLength() returns counts
 * - Debouncing: rapid changes batched into single history entry
 *
 * TASK-FE-P5-003
 */

import { StateCreator, StoreMutatorIdentifier } from 'zustand';
import { enablePatches, produceWithPatches, applyPatches, Patch } from 'immer';

// Enable Immer patches globally
enablePatches();

// ============================================================================
// Types
// ============================================================================

interface HistoryEntry {
  patches: Patch[];
  inversePatches: Patch[];
}

interface HistoryState {
  past: HistoryEntry[];
  future: HistoryEntry[];
}

export interface UndoRedoActions {
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  clearHistory: () => void;
  getHistoryLength: () => { past: number; future: number };
}

interface UndoRedoOptions {
  limit?: number;
  debounceMs?: number;
}

// Middleware type declaration
type UndoRedoMiddleware = <
  T extends object,
  Mps extends [StoreMutatorIdentifier, unknown][] = [],
  Mcs extends [StoreMutatorIdentifier, unknown][] = []
>(
  config: StateCreator<T, Mps, Mcs>,
  options?: UndoRedoOptions
) => StateCreator<T & UndoRedoActions, Mps, Mcs>;

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_HISTORY_LIMIT = 50;
const DEFAULT_DEBOUNCE_MS = 500;

// ============================================================================
// Helper: Extract data-only state (exclude functions)
// ============================================================================

function extractDataState<T extends object>(state: T): Partial<T> {
  const dataState: Partial<T> = {};
  for (const key of Object.keys(state) as (keyof T)[]) {
    if (typeof state[key] !== 'function') {
      dataState[key] = state[key];
    }
  }
  return dataState;
}

// ============================================================================
// Middleware Implementation
// ============================================================================

export const undoRedo: UndoRedoMiddleware = (config, options = {}) => (set, get, api) => {
  const { limit = DEFAULT_HISTORY_LIMIT, debounceMs = DEFAULT_DEBOUNCE_MS } = options;

  // History storage
  const history: HistoryState = {
    past: [],
    future: [],
  };

  // Debounce state - store the state BEFORE the batch started
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  let batchStartState: object | null = null; // Data-only state before batch started
  let hasPendingChanges = false;

  // Flag to prevent recording during undo/redo operations
  let isUndoRedoOperation = false;

  /**
   * Flush any pending (debounced) changes to history
   */
  const flushPendingChanges = () => {
    if (hasPendingChanges && batchStartState !== null) {
      const currentState = get();
      const currentDataState = extractDataState(currentState);

      // Create patches from batchStartState to currentDataState
      try {
        const [, patches, inversePatches] = produceWithPatches(
          batchStartState,
          (draft) => {
            Object.assign(draft, currentDataState);
          }
        );

        if (patches.length > 0) {
          history.past.push({
            patches,
            inversePatches,
          });

          // Enforce history limit by removing oldest entries
          while (history.past.length > limit) {
            history.past.shift();
          }

          // Clear future on new action (branching timeline)
          history.future = [];
        }
      } catch {
        // If patch creation fails, skip this history entry
      }
    }

    // Reset batch state
    batchStartState = null;
    hasPendingChanges = false;

    // Clear timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
  };

  /**
   * Deep clone state for capturing batch start (data only)
   */
  const cloneDataState = <T extends object>(state: T): object => {
    const dataState = extractDataState(state);
    return JSON.parse(JSON.stringify(dataState));
  };

  /**
   * Wrapped set function that tracks changes
   */
  const trackedSet: typeof set = (partial, replace) => {
    // Skip tracking during undo/redo operations
    if (isUndoRedoOperation) {
      // @ts-expect-error - Zustand type complexity
      return set(partial, replace);
    }

    const currentState = get();

    // Capture data-only state before batch if this is the first change in a batch
    if (!hasPendingChanges) {
      batchStartState = cloneDataState(currentState);
      hasPendingChanges = true;
    }

    // Handle function updaters (Immer-style mutations)
    if (typeof partial === 'function') {
      try {
        const [nextState] = produceWithPatches(
          currentState,
          partial as (draft: typeof currentState) => void
        );

        // Reset debounce timer
        if (debounceTimer) {
          clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(flushPendingChanges, debounceMs);

        // @ts-expect-error - Zustand type complexity
        return set(nextState, replace);
      } catch {
        // If Immer fails, fall back to direct set
        // @ts-expect-error - Zustand type complexity
        return set(partial, replace);
      }
    } else {
      // Direct partial object update
      try {
        const [nextState] = produceWithPatches(
          currentState,
          (draft) => {
            Object.assign(draft, partial);
          }
        );

        // Reset debounce timer
        if (debounceTimer) {
          clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(flushPendingChanges, debounceMs);

        // @ts-expect-error - Zustand type complexity
        return set(nextState, replace);
      } catch {
        // @ts-expect-error - Zustand type complexity
        return set(partial, replace);
      }
    }
  };

  // ============================================================================
  // Undo/Redo Actions
  // ============================================================================

  const undoRedoActions: UndoRedoActions = {
    /**
     * Undo the last change
     */
    undo: () => {
      // Flush any pending changes first
      flushPendingChanges();

      const lastEntry = history.past.pop();
      if (!lastEntry) return;

      const currentState = get();
      const currentDataState = extractDataState(currentState);

      // Apply inverse patches to revert (on data-only state)
      const newDataState = applyPatches(currentDataState, lastEntry.inversePatches);

      // Move to future for redo
      history.future.unshift({
        patches: lastEntry.inversePatches,
        inversePatches: lastEntry.patches,
      });

      // Apply without tracking - use partial update (not replace!)
      isUndoRedoOperation = true;
      // @ts-expect-error - Zustand type complexity
      set(newDataState, false); // false = merge, not replace
      isUndoRedoOperation = false;
    },

    /**
     * Redo an undone change
     */
    redo: () => {
      const nextEntry = history.future.shift();
      if (!nextEntry) return;

      const currentState = get();
      const currentDataState = extractDataState(currentState);

      // Apply the inverse patches (which are actually the forward patches)
      const newDataState = applyPatches(currentDataState, nextEntry.inversePatches);

      // Move back to past
      history.past.push({
        patches: nextEntry.inversePatches,
        inversePatches: nextEntry.patches,
      });

      // Apply without tracking - use partial update (not replace!)
      isUndoRedoOperation = true;
      // @ts-expect-error - Zustand type complexity
      set(newDataState, false); // false = merge, not replace
      isUndoRedoOperation = false;
    },

    /**
     * Check if undo is available
     */
    canUndo: () => {
      return history.past.length > 0 || hasPendingChanges;
    },

    /**
     * Check if redo is available
     */
    canRedo: () => {
      return history.future.length > 0;
    },

    /**
     * Clear all history (past and future)
     */
    clearHistory: () => {
      history.past = [];
      history.future = [];
      batchStartState = null;
      hasPendingChanges = false;
      if (debounceTimer) {
        clearTimeout(debounceTimer);
        debounceTimer = null;
      }
    },

    /**
     * Get current history length
     */
    getHistoryLength: () => ({
      past: history.past.length + (hasPendingChanges ? 1 : 0),
      future: history.future.length,
    }),
  };

  // ============================================================================
  // Return Combined State
  // ============================================================================

  return {
    ...config(trackedSet, get, api),
    ...undoRedoActions,
  };
};
