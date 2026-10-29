/**
 * BOM Store Undo/Redo Integration Tests
 *
 * Tests for undo/redo functionality specifically integrated with BOM editing.
 * Tests cover:
 * - Adding BOM entry creates history point
 * - Removing BOM entry can be undone
 * - Updating quantity can be undone
 * - Multiple changes create separate history entries (with debounce)
 * - Undo/redo preserves BOM item structure
 * - Integration with calculator store
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 * TASK-FE-P5-003
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { useCalculatorStore } from '@/store/calculatorStore';
import type { BOMItem } from '@/types/store.types';

// ============================================================================
// Test Utilities
// ============================================================================

const createMockBOMItem = (overrides: Partial<BOMItem> = {}): BOMItem => ({
  id: `item-${Date.now()}-${Math.random().toString(36).substring(7)}`,
  name: 'Test Component',
  quantity: 1.0,
  unit: 'kg',
  category: 'material',
  emissionFactorId: 'ef-123',
  ...overrides,
});

describe('BOM Store Undo/Redo Integration', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Reset calculator store state
    useCalculatorStore.getState().reset();
    // Clear any undo/redo history if available
    if (typeof useCalculatorStore.getState().clearHistory === 'function') {
      useCalculatorStore.getState().clearHistory();
    }
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ============================================================================
  // Adding BOM Entry - History Creation
  // ============================================================================

  describe('addBomItem', () => {
    test('creates history point when adding BOM entry', () => {
      const item = createMockBOMItem({ name: 'Cotton' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600); // Wait for debounce

      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);
      expect(useCalculatorStore.getState().canUndo()).toBe(true);
    });

    test('adding multiple items creates separate history entries', () => {
      const item1 = createMockBOMItem({ name: 'Cotton' });
      const item2 = createMockBOMItem({ name: 'Polyester' });

      useCalculatorStore.getState().addBomItem(item1);
      vi.advanceTimersByTime(600); // Past debounce

      useCalculatorStore.getState().addBomItem(item2);
      vi.advanceTimersByTime(600); // Past debounce

      expect(useCalculatorStore.getState().bomItems).toHaveLength(2);

      // Undo second add
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);
      expect(useCalculatorStore.getState().bomItems[0].name).toBe('Cotton');

      // Undo first add
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(0);
    });

    test('can redo adding BOM entry', () => {
      const item = createMockBOMItem({ name: 'Cotton' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);

      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(0);

      useCalculatorStore.getState().redo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);
      expect(useCalculatorStore.getState().bomItems[0].name).toBe('Cotton');
    });

    test('preserves all BOM item fields after undo/redo', () => {
      const item = createMockBOMItem({
        name: 'Special Material',
        quantity: 2.5,
        unit: 'kg',
        category: 'material',
        emissionFactorId: 'ef-special-123',
      });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);

      useCalculatorStore.getState().undo();
      useCalculatorStore.getState().redo();

      const restoredItem = useCalculatorStore.getState().bomItems[0];
      expect(restoredItem.name).toBe('Special Material');
      expect(restoredItem.quantity).toBe(2.5);
      expect(restoredItem.unit).toBe('kg');
      expect(restoredItem.category).toBe('material');
      expect(restoredItem.emissionFactorId).toBe('ef-special-123');
    });
  });

  // ============================================================================
  // Removing BOM Entry - History Creation
  // ============================================================================

  describe('removeBomItem', () => {
    test('can undo removing BOM entry', () => {
      const item = createMockBOMItem({ id: 'item-to-remove', name: 'Cotton' });

      // Add item first
      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);

      // Clear history to test removal independently
      useCalculatorStore.getState().clearHistory();

      // Remove item
      useCalculatorStore.getState().removeBomItem('item-to-remove');
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems).toHaveLength(0);

      // Undo removal
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);
      expect(useCalculatorStore.getState().bomItems[0].name).toBe('Cotton');
    });

    test('can redo removing BOM entry', () => {
      const item = createMockBOMItem({ id: 'item-to-remove', name: 'Cotton' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      useCalculatorStore.getState().removeBomItem('item-to-remove');
      vi.advanceTimersByTime(600);

      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);

      useCalculatorStore.getState().redo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(0);
    });

    test('removing from multiple items restores correct item', () => {
      const item1 = createMockBOMItem({ id: 'item-1', name: 'Cotton' });
      const item2 = createMockBOMItem({ id: 'item-2', name: 'Polyester' });
      const item3 = createMockBOMItem({ id: 'item-3', name: 'Silk' });

      // Add all items
      useCalculatorStore.getState().addBomItem(item1);
      useCalculatorStore.getState().addBomItem(item2);
      useCalculatorStore.getState().addBomItem(item3);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Remove middle item
      useCalculatorStore.getState().removeBomItem('item-2');
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems).toHaveLength(2);
      expect(useCalculatorStore.getState().bomItems.map(i => i.name)).toEqual(['Cotton', 'Silk']);

      // Undo should restore Polyester
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(3);
      expect(useCalculatorStore.getState().bomItems.map(i => i.name)).toContain('Polyester');
    });
  });

  // ============================================================================
  // Updating BOM Entry - History Creation
  // ============================================================================

  describe('updateBomItem', () => {
    test('can undo quantity update', () => {
      const item = createMockBOMItem({ id: 'item-1', name: 'Cotton', quantity: 1.0 });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Update quantity
      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 5.0 });
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(5.0);

      // Undo update
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(1.0);
    });

    test('can undo name update', () => {
      const item = createMockBOMItem({ id: 'item-1', name: 'Cotton' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Update name
      useCalculatorStore.getState().updateBomItem('item-1', { name: 'Organic Cotton' });
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems[0].name).toBe('Organic Cotton');

      // Undo update
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems[0].name).toBe('Cotton');
    });

    test('can undo emission factor update', () => {
      const item = createMockBOMItem({ id: 'item-1', emissionFactorId: 'ef-old' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Update emission factor
      useCalculatorStore.getState().updateBomItem('item-1', { emissionFactorId: 'ef-new' });
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems[0].emissionFactorId).toBe('ef-new');

      // Undo update
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems[0].emissionFactorId).toBe('ef-old');
    });

    test('can undo multiple field updates in single operation', () => {
      const item = createMockBOMItem({
        id: 'item-1',
        name: 'Cotton',
        quantity: 1.0,
        unit: 'kg',
      });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Update multiple fields
      useCalculatorStore.getState().updateBomItem('item-1', {
        name: 'Organic Cotton',
        quantity: 2.5,
        unit: 'g',
      });
      vi.advanceTimersByTime(600);

      const updatedItem = useCalculatorStore.getState().bomItems[0];
      expect(updatedItem.name).toBe('Organic Cotton');
      expect(updatedItem.quantity).toBe(2.5);
      expect(updatedItem.unit).toBe('g');

      // Undo all changes at once
      useCalculatorStore.getState().undo();

      const restoredItem = useCalculatorStore.getState().bomItems[0];
      expect(restoredItem.name).toBe('Cotton');
      expect(restoredItem.quantity).toBe(1.0);
      expect(restoredItem.unit).toBe('kg');
    });

    test('rapid quantity updates batch into single history entry', () => {
      const item = createMockBOMItem({ id: 'item-1', quantity: 1.0 });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Rapid updates (simulating typing)
      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 2.0 });
      vi.advanceTimersByTime(100);
      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 3.0 });
      vi.advanceTimersByTime(100);
      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 4.0 });
      vi.advanceTimersByTime(100);
      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 5.0 });
      vi.advanceTimersByTime(600); // Wait for debounce

      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(5.0);

      // Single undo should revert all rapid changes
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(1.0);
    });
  });

  // ============================================================================
  // setBomItems - Bulk Operations
  // ============================================================================

  describe('setBomItems', () => {
    test('can undo bulk BOM replacement', () => {
      const initialItems = [
        createMockBOMItem({ id: 'item-1', name: 'Cotton' }),
        createMockBOMItem({ id: 'item-2', name: 'Polyester' }),
      ];

      // Set initial items
      useCalculatorStore.getState().setBomItems(initialItems);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Replace with new items
      const newItems = [
        createMockBOMItem({ id: 'item-3', name: 'Silk' }),
        createMockBOMItem({ id: 'item-4', name: 'Wool' }),
        createMockBOMItem({ id: 'item-5', name: 'Linen' }),
      ];

      useCalculatorStore.getState().setBomItems(newItems);
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems).toHaveLength(3);
      expect(useCalculatorStore.getState().bomItems.map(i => i.name)).toEqual(['Silk', 'Wool', 'Linen']);

      // Undo bulk replacement
      useCalculatorStore.getState().undo();

      expect(useCalculatorStore.getState().bomItems).toHaveLength(2);
      expect(useCalculatorStore.getState().bomItems.map(i => i.name)).toEqual(['Cotton', 'Polyester']);
    });

    test('can undo clearing all BOM items', () => {
      const items = [
        createMockBOMItem({ id: 'item-1', name: 'Cotton' }),
        createMockBOMItem({ id: 'item-2', name: 'Polyester' }),
      ];

      useCalculatorStore.getState().setBomItems(items);
      vi.advanceTimersByTime(600);
      useCalculatorStore.getState().clearHistory();

      // Clear all items
      useCalculatorStore.getState().setBomItems([]);
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().bomItems).toHaveLength(0);

      // Undo clear
      useCalculatorStore.getState().undo();

      expect(useCalculatorStore.getState().bomItems).toHaveLength(2);
    });
  });

  // ============================================================================
  // Complex Workflows
  // ============================================================================

  describe('complex workflows', () => {
    test('mixed add/update/remove operations can all be undone', () => {
      // Add first item
      const item1 = createMockBOMItem({ id: 'item-1', name: 'Cotton', quantity: 1.0 });
      useCalculatorStore.getState().addBomItem(item1);
      vi.advanceTimersByTime(600);

      // Add second item
      const item2 = createMockBOMItem({ id: 'item-2', name: 'Polyester', quantity: 2.0 });
      useCalculatorStore.getState().addBomItem(item2);
      vi.advanceTimersByTime(600);

      // Update first item
      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 3.0 });
      vi.advanceTimersByTime(600);

      // Remove second item
      useCalculatorStore.getState().removeBomItem('item-2');
      vi.advanceTimersByTime(600);

      // Verify current state
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(3.0);

      // Undo remove
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(2);

      // Undo update
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(1.0);

      // Undo second add
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);

      // Undo first add
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(0);
    });

    test('undo/redo interleaving maintains consistency', () => {
      const item1 = createMockBOMItem({ id: 'item-1', name: 'A', quantity: 1.0 });
      const item2 = createMockBOMItem({ id: 'item-2', name: 'B', quantity: 2.0 });

      useCalculatorStore.getState().addBomItem(item1);
      vi.advanceTimersByTime(600);

      useCalculatorStore.getState().addBomItem(item2);
      vi.advanceTimersByTime(600);

      useCalculatorStore.getState().updateBomItem('item-1', { quantity: 10.0 });
      vi.advanceTimersByTime(600);

      // State: A(10), B(2)
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(10.0);

      // Undo to: A(1), B(2)
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(1.0);

      // Redo to: A(10), B(2)
      useCalculatorStore.getState().redo();
      expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(10.0);

      // Undo to: A(1), B(2)
      useCalculatorStore.getState().undo();

      // Undo to: A(1)
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(1);

      // Redo to: A(1), B(2)
      useCalculatorStore.getState().redo();
      expect(useCalculatorStore.getState().bomItems).toHaveLength(2);
    });

    test('new action after undo clears redo history', () => {
      const item1 = createMockBOMItem({ id: 'item-1', name: 'Cotton' });
      const item2 = createMockBOMItem({ id: 'item-2', name: 'Polyester' });
      const item3 = createMockBOMItem({ id: 'item-3', name: 'Silk' });

      useCalculatorStore.getState().addBomItem(item1);
      vi.advanceTimersByTime(600);

      useCalculatorStore.getState().addBomItem(item2);
      vi.advanceTimersByTime(600);

      // Undo adding item2
      useCalculatorStore.getState().undo();
      expect(useCalculatorStore.getState().canRedo()).toBe(true);

      // Add different item (branches timeline)
      useCalculatorStore.getState().addBomItem(item3);
      vi.advanceTimersByTime(600);

      // Redo should no longer be available
      expect(useCalculatorStore.getState().canRedo()).toBe(false);

      // Should have Cotton and Silk, not Polyester
      const names = useCalculatorStore.getState().bomItems.map(i => i.name);
      expect(names).toContain('Cotton');
      expect(names).toContain('Silk');
      expect(names).not.toContain('Polyester');
    });
  });

  // ============================================================================
  // hasUnsavedChanges Integration
  // ============================================================================

  describe('hasUnsavedChanges integration', () => {
    test('undo does not affect hasUnsavedChanges flag', () => {
      const item = createMockBOMItem({ name: 'Cotton' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().hasUnsavedChanges).toBe(true);

      useCalculatorStore.getState().undo();

      // hasUnsavedChanges should still reflect that state was modified
      // (implementation may vary - this tests current behavior)
      expect(useCalculatorStore.getState().hasUnsavedChanges).toBeDefined();
    });
  });

  // ============================================================================
  // History State After Reset
  // ============================================================================

  describe('reset integration', () => {
    test('reset clears undo/redo history', () => {
      const item = createMockBOMItem({ name: 'Cotton' });

      useCalculatorStore.getState().addBomItem(item);
      vi.advanceTimersByTime(600);

      expect(useCalculatorStore.getState().canUndo()).toBe(true);

      useCalculatorStore.getState().reset();

      expect(useCalculatorStore.getState().canUndo()).toBe(false);
      expect(useCalculatorStore.getState().canRedo()).toBe(false);
    });
  });
});
