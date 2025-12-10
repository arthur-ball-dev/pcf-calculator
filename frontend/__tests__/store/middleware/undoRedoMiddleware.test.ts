/**
 * Undo/Redo Middleware Tests
 *
 * Comprehensive test suite for the Immer patch-based undo/redo middleware.
 * Tests cover:
 * - undo() reverts to previous state
 * - redo() restores undone state
 * - canUndo()/canRedo() boundary conditions
 * - History limited to 50 entries (oldest removed when exceeded)
 * - clearHistory() empties past and future
 * - getHistoryLength() returns correct counts
 * - New actions clear future history
 * - Debouncing: rapid changes batched into single history entry
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 * TASK-FE-P5-003
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { create } from 'zustand';
import { undoRedo, type UndoRedoActions } from '@/store/middleware/undoRedoMiddleware';

// ============================================================================
// Test Store Setup
// ============================================================================

interface TestState {
  counter: number;
  items: string[];
  data: { name: string; value: number };
  // Actions
  increment: () => void;
  decrement: () => void;
  setCounter: (value: number) => void;
  addItem: (item: string) => void;
  removeItem: (index: number) => void;
  updateData: (updates: Partial<TestState['data']>) => void;
}

type TestStore = TestState & UndoRedoActions;

// Factory to create fresh store for each test
function createTestStore(options?: { limit?: number; debounceMs?: number }) {
  return create<TestStore>()(
    undoRedo(
      (set) => ({
        counter: 0,
        items: [],
        data: { name: '', value: 0 },

        increment: () => set((state) => { state.counter += 1; }),
        decrement: () => set((state) => { state.counter -= 1; }),
        setCounter: (value) => set((state) => { state.counter = value; }),
        addItem: (item) => set((state) => { state.items.push(item); }),
        removeItem: (index) => set((state) => { state.items.splice(index, 1); }),
        updateData: (updates) => set((state) => { Object.assign(state.data, updates); }),
      }),
      options
    )
  );
}

describe('UndoRedoMiddleware', () => {
  let store: ReturnType<typeof createTestStore>;

  beforeEach(() => {
    vi.useFakeTimers();
    store = createTestStore();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ============================================================================
  // Basic Undo Functionality
  // ============================================================================

  describe('undo()', () => {
    test('reverts single state change', () => {
      // Initial state
      expect(store.getState().counter).toBe(0);

      // Make a change
      store.getState().increment();
      vi.advanceTimersByTime(500); // Wait for debounce

      expect(store.getState().counter).toBe(1);

      // Undo
      store.getState().undo();
      expect(store.getState().counter).toBe(0);
    });

    test('reverts to each previous state sequentially', () => {
      // Make multiple changes with debounce delay between
      store.getState().setCounter(10);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(20);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(30);
      vi.advanceTimersByTime(600);

      expect(store.getState().counter).toBe(30);

      // Undo each change
      store.getState().undo();
      expect(store.getState().counter).toBe(20);

      store.getState().undo();
      expect(store.getState().counter).toBe(10);

      store.getState().undo();
      expect(store.getState().counter).toBe(0);
    });

    test('does nothing when history is empty', () => {
      expect(store.getState().counter).toBe(0);

      // Undo with no history
      store.getState().undo();

      expect(store.getState().counter).toBe(0);
    });

    test('reverts array mutations correctly', () => {
      store.getState().addItem('item1');
      vi.advanceTimersByTime(600);

      store.getState().addItem('item2');
      vi.advanceTimersByTime(600);

      expect(store.getState().items).toEqual(['item1', 'item2']);

      store.getState().undo();
      expect(store.getState().items).toEqual(['item1']);

      store.getState().undo();
      expect(store.getState().items).toEqual([]);
    });

    test('reverts object mutations correctly', () => {
      store.getState().updateData({ name: 'test', value: 100 });
      vi.advanceTimersByTime(600);

      expect(store.getState().data).toEqual({ name: 'test', value: 100 });

      store.getState().undo();
      expect(store.getState().data).toEqual({ name: '', value: 0 });
    });
  });

  // ============================================================================
  // Basic Redo Functionality
  // ============================================================================

  describe('redo()', () => {
    test('restores undone state change', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      expect(store.getState().counter).toBe(1);

      // Undo then redo
      store.getState().undo();
      expect(store.getState().counter).toBe(0);

      store.getState().redo();
      expect(store.getState().counter).toBe(1);
    });

    test('restores multiple undone states sequentially', () => {
      store.getState().setCounter(10);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(20);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(30);
      vi.advanceTimersByTime(600);

      // Undo all
      store.getState().undo();
      store.getState().undo();
      store.getState().undo();
      expect(store.getState().counter).toBe(0);

      // Redo each
      store.getState().redo();
      expect(store.getState().counter).toBe(10);

      store.getState().redo();
      expect(store.getState().counter).toBe(20);

      store.getState().redo();
      expect(store.getState().counter).toBe(30);
    });

    test('does nothing when future is empty', () => {
      store.getState().setCounter(10);
      vi.advanceTimersByTime(600);

      expect(store.getState().counter).toBe(10);

      // Redo with no future
      store.getState().redo();
      expect(store.getState().counter).toBe(10);
    });

    test('restores array mutations correctly', () => {
      store.getState().addItem('item1');
      vi.advanceTimersByTime(600);

      store.getState().addItem('item2');
      vi.advanceTimersByTime(600);

      // Undo both
      store.getState().undo();
      store.getState().undo();
      expect(store.getState().items).toEqual([]);

      // Redo both
      store.getState().redo();
      expect(store.getState().items).toEqual(['item1']);

      store.getState().redo();
      expect(store.getState().items).toEqual(['item1', 'item2']);
    });
  });

  // ============================================================================
  // canUndo() / canRedo() Boundary Conditions
  // ============================================================================

  describe('canUndo()', () => {
    test('returns false when no history exists', () => {
      expect(store.getState().canUndo()).toBe(false);
    });

    test('returns true when history exists', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      expect(store.getState().canUndo()).toBe(true);
    });

    test('returns false after undoing all history', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().undo();

      expect(store.getState().canUndo()).toBe(false);
    });

    test('returns true when pending (debounced) changes exist', () => {
      store.getState().increment();
      // Don't advance timer - changes are pending

      expect(store.getState().canUndo()).toBe(true);
    });
  });

  describe('canRedo()', () => {
    test('returns false when no future exists', () => {
      expect(store.getState().canRedo()).toBe(false);
    });

    test('returns true after undo', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().undo();

      expect(store.getState().canRedo()).toBe(true);
    });

    test('returns false after redoing all future', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().undo();
      store.getState().redo();

      expect(store.getState().canRedo()).toBe(false);
    });
  });

  // ============================================================================
  // History Limit (50 entries max)
  // ============================================================================

  describe('history limit', () => {
    test('limits history to 50 entries', () => {
      const limitedStore = createTestStore({ limit: 50 });

      // Perform 60 distinct changes
      for (let i = 1; i <= 60; i++) {
        limitedStore.getState().setCounter(i);
        vi.advanceTimersByTime(600); // Ensure each is a separate history entry
      }

      expect(limitedStore.getState().counter).toBe(60);

      // History should be limited to 50
      const { past } = limitedStore.getState().getHistoryLength();
      expect(past).toBe(50);
    });

    test('removes oldest entries when limit exceeded', () => {
      const limitedStore = createTestStore({ limit: 50 });

      // Perform 55 distinct changes
      for (let i = 1; i <= 55; i++) {
        limitedStore.getState().setCounter(i);
        vi.advanceTimersByTime(600);
      }

      // Undo all 50 available
      for (let i = 0; i < 50; i++) {
        limitedStore.getState().undo();
      }

      // Cannot undo further (first 5 states lost)
      expect(limitedStore.getState().canUndo()).toBe(false);

      // Should be at state 5 (oldest preserved)
      expect(limitedStore.getState().counter).toBe(5);
    });

    test('respects custom limit option', () => {
      const customStore = createTestStore({ limit: 10 });

      // Perform 15 changes
      for (let i = 1; i <= 15; i++) {
        customStore.getState().setCounter(i);
        vi.advanceTimersByTime(600);
      }

      const { past } = customStore.getState().getHistoryLength();
      expect(past).toBe(10);
    });
  });

  // ============================================================================
  // clearHistory()
  // ============================================================================

  describe('clearHistory()', () => {
    test('empties past history', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().increment();
      vi.advanceTimersByTime(600);

      expect(store.getState().getHistoryLength().past).toBeGreaterThan(0);

      store.getState().clearHistory();

      expect(store.getState().getHistoryLength().past).toBe(0);
    });

    test('empties future history', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().undo();
      expect(store.getState().getHistoryLength().future).toBeGreaterThan(0);

      store.getState().clearHistory();

      expect(store.getState().getHistoryLength().future).toBe(0);
    });

    test('preserves current state', () => {
      store.getState().setCounter(42);
      vi.advanceTimersByTime(600);

      store.getState().clearHistory();

      expect(store.getState().counter).toBe(42);
    });

    test('canUndo returns false after clear', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().clearHistory();

      expect(store.getState().canUndo()).toBe(false);
    });

    test('canRedo returns false after clear', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().undo();
      store.getState().clearHistory();

      expect(store.getState().canRedo()).toBe(false);
    });

    test('clears pending debounced changes', () => {
      store.getState().increment();
      // Don't advance timer - changes are pending

      store.getState().clearHistory();

      // Pending changes should be discarded from history
      expect(store.getState().getHistoryLength().past).toBe(0);
    });
  });

  // ============================================================================
  // getHistoryLength()
  // ============================================================================

  describe('getHistoryLength()', () => {
    test('returns zero for both when no history', () => {
      const { past, future } = store.getState().getHistoryLength();
      expect(past).toBe(0);
      expect(future).toBe(0);
    });

    test('returns correct past count', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().increment();
      vi.advanceTimersByTime(600);

      expect(store.getState().getHistoryLength().past).toBe(3);
    });

    test('returns correct future count after undo', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().increment();
      vi.advanceTimersByTime(600);

      store.getState().undo();
      store.getState().undo();

      expect(store.getState().getHistoryLength().future).toBe(2);
    });

    test('counts pending changes as 1 in past', () => {
      store.getState().increment();
      // Don't advance timer - changes pending

      // Pending changes should count as 1 entry
      expect(store.getState().getHistoryLength().past).toBe(1);
    });
  });

  // ============================================================================
  // New Actions Clear Future History
  // ============================================================================

  describe('new actions clear future', () => {
    test('clears future when new action performed after undo', () => {
      store.getState().setCounter(10);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(20);
      vi.advanceTimersByTime(600);

      // Undo once
      store.getState().undo();
      expect(store.getState().counter).toBe(10);
      expect(store.getState().canRedo()).toBe(true);

      // Perform new action
      store.getState().setCounter(30);
      vi.advanceTimersByTime(600);

      // Future should be cleared
      expect(store.getState().canRedo()).toBe(false);
      expect(store.getState().getHistoryLength().future).toBe(0);
    });

    test('maintains history consistency after branch', () => {
      store.getState().setCounter(10);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(20);
      vi.advanceTimersByTime(600);

      // Undo to 10
      store.getState().undo();

      // Branch with new action
      store.getState().setCounter(15);
      vi.advanceTimersByTime(600);

      // Should be able to undo to 10, then to 0
      store.getState().undo();
      expect(store.getState().counter).toBe(10);

      store.getState().undo();
      expect(store.getState().counter).toBe(0);
    });
  });

  // ============================================================================
  // Debouncing (500ms default)
  // ============================================================================

  describe('debouncing', () => {
    test('batches rapid changes into single history entry', () => {
      // Rapid changes within debounce window
      store.getState().increment();
      vi.advanceTimersByTime(100);

      store.getState().increment();
      vi.advanceTimersByTime(100);

      store.getState().increment();
      vi.advanceTimersByTime(100);

      store.getState().increment();
      vi.advanceTimersByTime(100);

      store.getState().increment();

      // Still within debounce window, no flush yet
      expect(store.getState().counter).toBe(5);

      // Advance past debounce threshold
      vi.advanceTimersByTime(500);

      // Should be single history entry
      expect(store.getState().getHistoryLength().past).toBe(1);

      // Single undo reverts all 5 increments
      store.getState().undo();
      expect(store.getState().counter).toBe(0);
    });

    test('creates separate entries for changes after debounce window', () => {
      store.getState().increment();
      vi.advanceTimersByTime(600); // Past debounce

      store.getState().increment();
      vi.advanceTimersByTime(600); // Past debounce

      expect(store.getState().getHistoryLength().past).toBe(2);
    });

    test('flushes pending changes before undo', () => {
      store.getState().setCounter(10);
      // Don't advance timer - changes pending

      // Undo should flush first, then undo
      store.getState().undo();

      // Should be back to 0
      expect(store.getState().counter).toBe(0);
    });

    test('handles mixed rapid and spaced changes correctly', () => {
      // First batch of rapid changes
      store.getState().increment();
      vi.advanceTimersByTime(100);
      store.getState().increment();
      vi.advanceTimersByTime(600); // Flush (past debounce)

      // Second batch of rapid changes
      store.getState().increment();
      vi.advanceTimersByTime(100);
      store.getState().increment();
      vi.advanceTimersByTime(600); // Flush

      expect(store.getState().counter).toBe(4);
      expect(store.getState().getHistoryLength().past).toBe(2);

      // Undo reverts second batch
      store.getState().undo();
      expect(store.getState().counter).toBe(2);

      // Undo reverts first batch
      store.getState().undo();
      expect(store.getState().counter).toBe(0);
    });

    test('respects custom debounce time option', () => {
      const customStore = createTestStore({ debounceMs: 1000 });

      customStore.getState().increment();
      vi.advanceTimersByTime(500); // Within custom debounce

      customStore.getState().increment();
      vi.advanceTimersByTime(500); // Still within

      customStore.getState().increment();
      vi.advanceTimersByTime(1000); // Past custom debounce

      // All 3 should be single entry
      expect(customStore.getState().getHistoryLength().past).toBe(1);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('edge cases', () => {
    test('handles undo/redo interleaving correctly', () => {
      store.getState().setCounter(10);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(20);
      vi.advanceTimersByTime(600);

      store.getState().setCounter(30);
      vi.advanceTimersByTime(600);

      // Interleave undo/redo
      store.getState().undo(); // 20
      store.getState().redo(); // 30
      store.getState().undo(); // 20
      store.getState().undo(); // 10
      store.getState().redo(); // 20

      expect(store.getState().counter).toBe(20);
    });

    test('handles empty state transitions', () => {
      store.getState().addItem('item1');
      vi.advanceTimersByTime(600);

      store.getState().removeItem(0);
      vi.advanceTimersByTime(600);

      expect(store.getState().items).toEqual([]);

      store.getState().undo();
      expect(store.getState().items).toEqual(['item1']);
    });

    test('maintains state immutability', () => {
      const initialItems = store.getState().items;

      store.getState().addItem('item1');
      vi.advanceTimersByTime(600);

      // Original reference should be unchanged
      expect(initialItems).toEqual([]);
      expect(store.getState().items).toEqual(['item1']);
    });

    test('works with complex nested state changes', () => {
      store.getState().updateData({ name: 'test1', value: 100 });
      vi.advanceTimersByTime(600);

      store.getState().updateData({ name: 'test2' });
      vi.advanceTimersByTime(600);

      expect(store.getState().data).toEqual({ name: 'test2', value: 100 });

      store.getState().undo();
      expect(store.getState().data).toEqual({ name: 'test1', value: 100 });
    });
  });
});
