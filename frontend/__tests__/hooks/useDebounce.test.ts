/**
 * useDebounce Hook Tests
 * TASK-FE-P5-004: Enhanced Product Search - Phase A Tests
 *
 * Test Coverage:
 * 1. Returns initial value immediately
 * 2. Returns debounced value after delay
 * 3. Resets timer when value changes rapidly
 * 4. Uses default 300ms delay
 * 5. Cleans up on unmount
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '../testUtils';
import { useDebounce } from '@/hooks/useDebounce';

describe('useDebounce Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ==========================================================================
  // Test Suite 1: Initial Value Behavior
  // ==========================================================================

  describe('Initial Value', () => {
    it('should return the initial value immediately', () => {
      const { result } = renderHook(() => useDebounce('initial'));

      expect(result.current).toBe('initial');
    });

    it('should return initial value for different types (string)', () => {
      const { result } = renderHook(() => useDebounce('test string'));

      expect(result.current).toBe('test string');
    });

    it('should return initial value for different types (number)', () => {
      const { result } = renderHook(() => useDebounce(42));

      expect(result.current).toBe(42);
    });

    it('should return initial value for different types (object)', () => {
      const obj = { name: 'test', value: 123 };
      const { result } = renderHook(() => useDebounce(obj));

      expect(result.current).toEqual(obj);
    });

    it('should return initial value for different types (null)', () => {
      const { result } = renderHook(() => useDebounce(null));

      expect(result.current).toBeNull();
    });

    it('should return initial value for different types (undefined)', () => {
      const { result } = renderHook(() => useDebounce(undefined));

      expect(result.current).toBeUndefined();
    });

    it('should return initial value for different types (boolean)', () => {
      const { result } = renderHook(() => useDebounce(true));

      expect(result.current).toBe(true);
    });
  });

  // ==========================================================================
  // Test Suite 2: Debounce Delay Behavior
  // ==========================================================================

  describe('Debounce Delay', () => {
    it('should NOT update value before delay has passed', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value),
        { initialProps: { value: 'initial' } }
      );

      expect(result.current).toBe('initial');

      // Change the value
      rerender({ value: 'updated' });

      // Value should still be initial (before delay)
      expect(result.current).toBe('initial');

      // Advance time but not enough
      act(() => {
        vi.advanceTimersByTime(299);
      });

      // Still should be initial
      expect(result.current).toBe('initial');
    });

    it('should update value AFTER delay has passed', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // Advance time past the default delay (300ms)
      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current).toBe('updated');
    });

    it('should use default 300ms delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // At 299ms, should still be initial
      act(() => {
        vi.advanceTimersByTime(299);
      });
      expect(result.current).toBe('initial');

      // At 300ms, should be updated
      act(() => {
        vi.advanceTimersByTime(1);
      });
      expect(result.current).toBe('updated');
    });

    it('should respect custom delay value', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 500),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // At 499ms, should still be initial
      act(() => {
        vi.advanceTimersByTime(499);
      });
      expect(result.current).toBe('initial');

      // At 500ms, should be updated
      act(() => {
        vi.advanceTimersByTime(1);
      });
      expect(result.current).toBe('updated');
    });

    it('should work with zero delay', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 0),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // With 0 delay, should update after minimal time
      act(() => {
        vi.advanceTimersByTime(0);
      });

      expect(result.current).toBe('updated');
    });
  });

  // ==========================================================================
  // Test Suite 3: Rapid Value Changes (Timer Reset)
  // ==========================================================================

  describe('Rapid Value Changes', () => {
    it('should reset timer when value changes rapidly', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'initial' } }
      );

      // First change
      rerender({ value: 'first' });

      // Advance 200ms (not enough)
      act(() => {
        vi.advanceTimersByTime(200);
      });

      // Second change - should reset timer
      rerender({ value: 'second' });

      // Advance another 200ms (total 400ms from first, but only 200ms from second)
      act(() => {
        vi.advanceTimersByTime(200);
      });

      // Should still be initial because timer was reset
      expect(result.current).toBe('initial');

      // Advance remaining 100ms
      act(() => {
        vi.advanceTimersByTime(100);
      });

      // Now should be 'second'
      expect(result.current).toBe('second');
    });

    it('should only fire once after rapid typing stops', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: '' } }
      );

      // Simulate rapid typing: s -> sm -> sma -> smar -> smart
      const typeSequence = ['s', 'sm', 'sma', 'smar', 'smart'];

      for (const typed of typeSequence) {
        rerender({ value: typed });
        act(() => {
          vi.advanceTimersByTime(50); // 50ms between keystrokes
        });
      }

      // After 250ms (5 * 50ms), still should be empty (initial)
      expect(result.current).toBe('');

      // Wait for final debounce
      act(() => {
        vi.advanceTimersByTime(300);
      });

      // Now should be 'smart' (final value)
      expect(result.current).toBe('smart');
    });

    it('should handle typing "smartphone" with only one final update', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: '' } }
      );

      // Type "smart" then "phone" within 300ms
      rerender({ value: 'smart' });
      act(() => {
        vi.advanceTimersByTime(100);
      });

      rerender({ value: 'smartphone' });
      act(() => {
        vi.advanceTimersByTime(100);
      });

      // Still empty
      expect(result.current).toBe('');

      // Wait for debounce
      act(() => {
        vi.advanceTimersByTime(300);
      });

      // Should be 'smartphone', not 'smart'
      expect(result.current).toBe('smartphone');
    });
  });

  // ==========================================================================
  // Test Suite 4: Cleanup on Unmount
  // ==========================================================================

  describe('Cleanup on Unmount', () => {
    it('should clear timeout on unmount', () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

      const { rerender, unmount } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // Unmount before delay completes
      unmount();

      // clearTimeout should have been called
      expect(clearTimeoutSpy).toHaveBeenCalled();

      clearTimeoutSpy.mockRestore();
    });

    it('should not update value after unmount', () => {
      const { result, rerender, unmount } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // Capture current value
      const valueBeforeUnmount = result.current;

      // Unmount
      unmount();

      // Advance time past delay
      act(() => {
        vi.advanceTimersByTime(500);
      });

      // Value should remain as it was before unmount
      // (No error should be thrown, and state should not update)
      expect(valueBeforeUnmount).toBe('initial');
    });

    it('should clear timeout when value changes', () => {
      const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

      const { rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'initial' } }
      );

      // First change
      rerender({ value: 'first' });

      // Second change - should clear previous timeout
      rerender({ value: 'second' });

      // clearTimeout should have been called to cancel the first timer
      expect(clearTimeoutSpy).toHaveBeenCalled();

      clearTimeoutSpy.mockRestore();
    });
  });

  // ==========================================================================
  // Test Suite 5: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle same value rerender without resetting timer', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'test' } }
      );

      // Rerender with same value
      rerender({ value: 'test' });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      // Value should remain 'test'
      expect(result.current).toBe('test');
    });

    it('should handle empty string value', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: '' });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current).toBe('');
    });

    it('should handle changing delay value', () => {
      const { result, rerender } = renderHook(
        ({ value, delay }) => useDebounce(value, delay),
        { initialProps: { value: 'initial', delay: 300 } }
      );

      // Change value and delay
      rerender({ value: 'updated', delay: 500 });

      // Advance 400ms (would trigger with old delay, but not new)
      act(() => {
        vi.advanceTimersByTime(400);
      });

      expect(result.current).toBe('initial');

      // Advance remaining 100ms
      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(result.current).toBe('updated');
    });

    it('should handle very large delay values', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 10000),
        { initialProps: { value: 'initial' } }
      );

      rerender({ value: 'updated' });

      // Advance 9999ms
      act(() => {
        vi.advanceTimersByTime(9999);
      });

      expect(result.current).toBe('initial');

      // Final 1ms
      act(() => {
        vi.advanceTimersByTime(1);
      });

      expect(result.current).toBe('updated');
    });

    it('should handle array values', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: [1, 2, 3] } }
      );

      rerender({ value: [4, 5, 6] });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current).toEqual([4, 5, 6]);
    });

    it('should handle function values', () => {
      const fn1 = () => 'first';
      const fn2 = () => 'second';

      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: fn1 } }
      );

      rerender({ value: fn2 });

      act(() => {
        vi.advanceTimersByTime(300);
      });

      expect(result.current).toBe(fn2);
      expect(result.current()).toBe('second');
    });
  });

  // ==========================================================================
  // Test Suite 6: Multiple Sequential Updates
  // ==========================================================================

  describe('Multiple Sequential Updates', () => {
    it('should handle multiple debounced updates over time', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: 'initial' } }
      );

      // First update cycle
      rerender({ value: 'first' });
      act(() => {
        vi.advanceTimersByTime(300);
      });
      expect(result.current).toBe('first');

      // Second update cycle
      rerender({ value: 'second' });
      act(() => {
        vi.advanceTimersByTime(300);
      });
      expect(result.current).toBe('second');

      // Third update cycle
      rerender({ value: 'third' });
      act(() => {
        vi.advanceTimersByTime(300);
      });
      expect(result.current).toBe('third');
    });

    it('should track search query pattern: type, pause, type more', () => {
      const { result, rerender } = renderHook(
        ({ value }) => useDebounce(value, 300),
        { initialProps: { value: '' } }
      );

      // User types "lap"
      rerender({ value: 'lap' });
      act(() => {
        vi.advanceTimersByTime(300);
      });
      expect(result.current).toBe('lap');

      // User pauses, then continues with "top"
      rerender({ value: 'laptop' });
      act(() => {
        vi.advanceTimersByTime(300);
      });
      expect(result.current).toBe('laptop');
    });
  });
});
