/**
 * useUndoRedoKeyboard Hook Tests
 *
 * Comprehensive test suite for the keyboard shortcut hook for undo/redo.
 * Tests cover:
 * - Ctrl+Z triggers undo
 * - Ctrl+Shift+Z triggers redo
 * - Cmd+Z triggers undo (Mac)
 * - Cmd+Shift+Z triggers redo (Mac)
 * - Ctrl+Y triggers redo (Windows alternative)
 * - Shortcuts disabled when input focused
 * - Shortcuts work when component mounted
 * - Cleanup on unmount
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 * TASK-FE-P5-003
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '../testUtils';
import { useUndoRedoKeyboard } from '@/hooks/useUndoRedoKeyboard';

// ============================================================================
// Mock Store
// ============================================================================

const mockUndo = vi.fn();
const mockRedo = vi.fn();
const mockCanUndo = vi.fn(() => true);
const mockCanRedo = vi.fn(() => true);

vi.mock('@/store/calculatorStore', () => ({
  useCalculatorStore: vi.fn((selector) => {
    const state = {
      undo: mockUndo,
      redo: mockRedo,
      canUndo: mockCanUndo,
      canRedo: mockCanRedo,
    };
    return selector(state);
  }),
}));

describe('useUndoRedoKeyboard', () => {
  let addEventListenerSpy: ReturnType<typeof vi.spyOn>;
  let removeEventListenerSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    addEventListenerSpy = vi.spyOn(window, 'addEventListener');
    removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
    // Reset mock return values
    mockCanUndo.mockReturnValue(true);
    mockCanRedo.mockReturnValue(true);
  });

  afterEach(() => {
    addEventListenerSpy.mockRestore();
    removeEventListenerSpy.mockRestore();
  });

  // ============================================================================
  // Hook Lifecycle
  // ============================================================================

  describe('hook lifecycle', () => {
    test('registers keydown event listener on mount', () => {
      renderHook(() => useUndoRedoKeyboard());

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );
    });

    test('removes keydown event listener on unmount', () => {
      const { unmount } = renderHook(() => useUndoRedoKeyboard());

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'keydown',
        expect.any(Function)
      );
    });

    test('re-registers listener when dependencies change', () => {
      const { rerender } = renderHook(
        ({ enabled }) => useUndoRedoKeyboard({ enabled }),
        { initialProps: { enabled: true } }
      );

      const initialCallCount = addEventListenerSpy.mock.calls.length;

      rerender({ enabled: false });

      // Should have removed and potentially re-added
      expect(removeEventListenerSpy).toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Windows/Linux Shortcuts (Ctrl)
  // ============================================================================

  describe('Ctrl+Z (undo)', () => {
    test('triggers undo when Ctrl+Z pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).toHaveBeenCalledTimes(1);
    });

    test('does not trigger undo when canUndo returns false', () => {
      mockCanUndo.mockReturnValue(false);

      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();
    });

    test('prevents default browser behavior', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
        cancelable: true,
      });
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault');

      act(() => {
        window.dispatchEvent(event);
      });

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Ctrl+Shift+Z (redo)', () => {
    test('triggers redo when Ctrl+Shift+Z pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });

    test('does not trigger redo when canRedo returns false', () => {
      mockCanRedo.mockReturnValue(false);

      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).not.toHaveBeenCalled();
    });

    test('prevents default browser behavior', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true,
        cancelable: true,
      });
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault');

      act(() => {
        window.dispatchEvent(event);
      });

      expect(preventDefaultSpy).toHaveBeenCalled();
    });
  });

  describe('Ctrl+Y (redo alternative)', () => {
    test('triggers redo when Ctrl+Y pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'y',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });

    test('does not trigger redo when canRedo returns false', () => {
      mockCanRedo.mockReturnValue(false);

      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'y',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Mac Shortcuts (Cmd/Meta)
  // ============================================================================

  describe('Cmd+Z (Mac undo)', () => {
    test('triggers undo when Cmd+Z pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        metaKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).toHaveBeenCalledTimes(1);
    });

    test('does not trigger undo when canUndo returns false', () => {
      mockCanUndo.mockReturnValue(false);

      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        metaKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();
    });
  });

  describe('Cmd+Shift+Z (Mac redo)', () => {
    test('triggers redo when Cmd+Shift+Z pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        metaKey: true,
        shiftKey: true,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });

    test('does not trigger redo when canRedo returns false', () => {
      mockCanRedo.mockReturnValue(false);

      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        metaKey: true,
        shiftKey: true,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).not.toHaveBeenCalled();
    });
  });

  describe('Cmd+Y (Mac redo alternative)', () => {
    test('triggers redo when Cmd+Y pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'y',
        metaKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // Input Focus Handling
  // ============================================================================

  describe('input focus handling', () => {
    test('does not trigger shortcuts when text input is focused', () => {
      renderHook(() => useUndoRedoKeyboard());

      // Create and focus a text input
      const input = document.createElement('input');
      input.type = 'text';
      document.body.appendChild(input);
      input.focus();

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });
      Object.defineProperty(event, 'target', { value: input });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();

      // Cleanup
      document.body.removeChild(input);
    });

    test('does not trigger shortcuts when textarea is focused', () => {
      renderHook(() => useUndoRedoKeyboard());

      // Create and focus a textarea
      const textarea = document.createElement('textarea');
      document.body.appendChild(textarea);
      textarea.focus();

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });
      Object.defineProperty(event, 'target', { value: textarea });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();

      // Cleanup
      document.body.removeChild(textarea);
    });

    test('does not trigger shortcuts when contentEditable is focused', () => {
      renderHook(() => useUndoRedoKeyboard());

      // Create and focus a contentEditable element
      const div = document.createElement('div');
      div.contentEditable = 'true';
      document.body.appendChild(div);
      div.focus();

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });
      Object.defineProperty(event, 'target', { value: div });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();

      // Cleanup
      document.body.removeChild(div);
    });

    test('does not trigger shortcuts when select element is focused', () => {
      renderHook(() => useUndoRedoKeyboard());

      // Create and focus a select element
      const select = document.createElement('select');
      document.body.appendChild(select);
      select.focus();

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });
      Object.defineProperty(event, 'target', { value: select });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();

      // Cleanup
      document.body.removeChild(select);
    });

    test('triggers shortcuts when non-input element is focused', () => {
      renderHook(() => useUndoRedoKeyboard());

      // Create and focus a div (non-input)
      const div = document.createElement('div');
      div.tabIndex = 0;
      document.body.appendChild(div);
      div.focus();

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });
      Object.defineProperty(event, 'target', { value: div });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).toHaveBeenCalledTimes(1);

      // Cleanup
      document.body.removeChild(div);
    });
  });

  // ============================================================================
  // Enabled/Disabled Option
  // ============================================================================

  describe('enabled option', () => {
    test('does not register listener when enabled=false', () => {
      const callsBefore = addEventListenerSpy.mock.calls.filter(
        (call) => call[0] === 'keydown'
      ).length;

      renderHook(() => useUndoRedoKeyboard({ enabled: false }));

      const callsAfter = addEventListenerSpy.mock.calls.filter(
        (call) => call[0] === 'keydown'
      ).length;

      // Should not have added new keydown listener
      expect(callsAfter).toBe(callsBefore);
    });

    test('does not trigger shortcuts when enabled=false', () => {
      renderHook(() => useUndoRedoKeyboard({ enabled: false }));

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();
    });

    test('re-enables shortcuts when enabled changes to true', () => {
      const { rerender } = renderHook(
        ({ enabled }) => useUndoRedoKeyboard({ enabled }),
        { initialProps: { enabled: false } }
      );

      // Should not work when disabled
      const event1 = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event1);
      });

      expect(mockUndo).not.toHaveBeenCalled();

      // Enable shortcuts
      rerender({ enabled: true });

      // Should work now
      const event2 = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event2);
      });

      expect(mockUndo).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('edge cases', () => {
    test('ignores key press without modifier', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: false,
        metaKey: false,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();
      expect(mockRedo).not.toHaveBeenCalled();
    });

    test('ignores unrelated keys with modifier', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'a',
        ctrlKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockUndo).not.toHaveBeenCalled();
      expect(mockRedo).not.toHaveBeenCalled();
    });

    test('handles uppercase Z correctly', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'Z',
        ctrlKey: true,
        shiftKey: true,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });

    test('handles both Ctrl and Meta pressed', () => {
      renderHook(() => useUndoRedoKeyboard());

      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        metaKey: true,
        shiftKey: false,
        bubbles: true,
      });

      act(() => {
        window.dispatchEvent(event);
      });

      // Should still trigger undo (either modifier is fine)
      expect(mockUndo).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // Return Values
  // ============================================================================

  describe('return values', () => {
    test('returns undo function', () => {
      const { result } = renderHook(() => useUndoRedoKeyboard());

      expect(result.current.undo).toBe(mockUndo);
    });

    test('returns redo function', () => {
      const { result } = renderHook(() => useUndoRedoKeyboard());

      expect(result.current.redo).toBe(mockRedo);
    });

    test('returns canUndo function', () => {
      const { result } = renderHook(() => useUndoRedoKeyboard());

      expect(result.current.canUndo).toBe(mockCanUndo);
    });

    test('returns canRedo function', () => {
      const { result } = renderHook(() => useUndoRedoKeyboard());

      expect(result.current.canRedo).toBe(mockCanRedo);
    });
  });
});
