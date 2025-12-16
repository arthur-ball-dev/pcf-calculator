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

import type { StateCreator, StoreMutatorIdentifier } from 'zustand';
import { enablePatches, produceWithPatches, applyPatches } from 'immer';
import type { Patch } from 'immer';

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

// Simplified middleware type that works with Zustand's type system
type UndoRedoMiddleware = <
  T extends object,
  Mps extends [StoreMutatorIdentifier, unknown][] = [],
  Mcs extends [StoreMutatorIdentifier, unknown][] = []
>(
  config: StateCreator<T, Mps, Mcs>,
  options?: UndoRedoOptions
) => StateCreator<T & UndoRedoActions, Mps, Mcs>;

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

  // Type-safe getter that works with extended state
  const getState = () => get() as unknown;

  /**
   * Flush any pending (debounced) changes to history
   */
  const flushPendingChanges = () => {
    if (hasPendingChanges && batchStartState !== null) {
      const currentState = getState();
      const currentDataState = extractDataState(currentState as object);

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

  // Type-safe setter
  const setState = (partial: unknown, replace?: boolean) => {
    (set as (partial: unknown, replace?: boolean) => void)(partial, replace);
  };

  /**
   * Wrapped set function that tracks changes and supports Immer-style mutations
   * Accepts both standard Zustand partial updates and Immer-style void-returning mutations
   */
  const trackedSet: typeof set = ((
    partial: unknown,
    replace?: boolean
  ) => {
    // Skip tracking during undo/redo operations
    if (isUndoRedoOperation) {
      return setState(partial, replace);
    }

    const currentState = getState();

    // Capture data-only state before batch if this is the first change in a batch
    if (!hasPendingChanges) {
      batchStartState = cloneDataState(currentState as object);
      hasPendingChanges = true;
    }

    // Handle function updaters (Immer-style mutations)
    if (typeof partial === 'function') {
      try {
        const [nextState] = produceWithPatches(
          currentState as object,
          partial as (draft: object) => void
        );

        // Reset debounce timer
        if (debounceTimer) {
          clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(flushPendingChanges, debounceMs);

        return setState(nextState, replace);
      } catch {
        // If Immer fails, fall back to direct set
        return setState(partial, replace);
      }
    } else {
      // Direct partial object update
      try {
        const [nextState] = produceWithPatches(
          currentState as object,
          (draft) => {
            Object.assign(draft, partial);
          }
        );

        // Reset debounce timer
        if (debounceTimer) {
          clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(flushPendingChanges, debounceMs);

        return setState(nextState, replace);
      } catch {
        return setState(partial, replace);
      }
    }
  }) as typeof set;

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

      const currentState = getState();
      const currentDataState = extractDataState(currentState as object);

      // Apply inverse patches to revert (on data-only state)
      const newDataState = applyPatches(currentDataState, lastEntry.inversePatches);

      // Move to future for redo
      history.future.unshift({
        patches: lastEntry.inversePatches,
        inversePatches: lastEntry.patches,
      });

      // Apply without tracking - use partial update (not replace!)
      isUndoRedoOperation = true;
      setState(newDataState, false);
      isUndoRedoOperation = false;
    },

    /**
     * Redo an undone change
     */
    redo: () => {
      const nextEntry = history.future.shift();
      if (!nextEntry) return;

      const currentState = getState();
      const currentDataState = extractDataState(currentState as object);

      // Apply the inverse patches (which are actually the forward patches)
      const newDataState = applyPatches(currentDataState, nextEntry.inversePatches);

      // Move back to past
      history.past.push({
        patches: nextEntry.inversePatches,
        inversePatches: nextEntry.patches,
      });

      // Apply without tracking - use partial update (not replace!)
      isUndoRedoOperation = true;
      setState(newDataState, false);
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

  // Create inner config with the tracked set function
  // Cast to work around Zustand's complex middleware type system
  type InnerSet = Parameters<typeof config>[0];
  type InnerGet = Parameters<typeof config>[1];
  type InnerApi = Parameters<typeof config>[2];

  const innerConfig = config(
    trackedSet as unknown as InnerSet,
    get as unknown as InnerGet,
    api as unknown as InnerApi
  );

  return {
    ...innerConfig,
    ...undoRedoActions,
  };
};
