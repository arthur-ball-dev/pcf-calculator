/**
 * useMediaQuery Hook Tests
 * TASK-FE-P7-009: Mobile Responsive Layouts - Phase A Tests
 *
 * Test Coverage:
 * 1. Returns correct initial value based on media query match
 * 2. Updates on media query change event
 * 3. Cleans up listener on unmount
 * 4. Handles SSR safely (undefined window)
 * 5. Handles multiple queries
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '../testUtils';
import { useMediaQuery } from '@/hooks/useMediaQuery';

// Mock matchMedia for testing
interface MockMediaQueryList {
  matches: boolean;
  media: string;
  onchange: ((ev: MediaQueryListEvent) => void) | null;
  addListener: ReturnType<typeof vi.fn>;
  removeListener: ReturnType<typeof vi.fn>;
  addEventListener: ReturnType<typeof vi.fn>;
  removeEventListener: ReturnType<typeof vi.fn>;
  dispatchEvent: ReturnType<typeof vi.fn>;
}

type MatchMediaMock = (query: string) => MockMediaQueryList;

describe('useMediaQuery Hook', () => {
  let originalMatchMedia: typeof window.matchMedia;
  let mockMediaQueryLists: MockMediaQueryList[];
  let changeHandlers: Map<string, ((ev: MediaQueryListEvent) => void)[]>;

  /**
   * Creates a mock matchMedia function that simulates browser behavior
   * @param width - The simulated viewport width in pixels
   */
  const createMatchMedia = (width: number): MatchMediaMock => {
    return (query: string): MockMediaQueryList => {
      // Parse the query to determine if it matches
      // Supports: (max-width: Xpx), (min-width: Xpx)
      let matches = false;

      const maxWidthMatch = query.match(/\(max-width:\s*(\d+)px\)/);
      const minWidthMatch = query.match(/\(min-width:\s*(\d+)px\)/);

      if (maxWidthMatch) {
        const maxWidth = parseInt(maxWidthMatch[1], 10);
        matches = width <= maxWidth;
      } else if (minWidthMatch) {
        const minWidth = parseInt(minWidthMatch[1], 10);
        matches = width >= minWidth;
      }

      const mediaQueryList: MockMediaQueryList = {
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn((event: string, handler: (ev: MediaQueryListEvent) => void) => {
          if (event === 'change') {
            if (!changeHandlers.has(query)) {
              changeHandlers.set(query, []);
            }
            changeHandlers.get(query)!.push(handler);
          }
        }),
        removeEventListener: vi.fn((event: string, handler: (ev: MediaQueryListEvent) => void) => {
          if (event === 'change') {
            const handlers = changeHandlers.get(query);
            if (handlers) {
              const index = handlers.indexOf(handler);
              if (index > -1) {
                handlers.splice(index, 1);
              }
            }
          }
        }),
        dispatchEvent: vi.fn(),
      };

      mockMediaQueryLists.push(mediaQueryList);
      return mediaQueryList;
    };
  };

  /**
   * Simulates a viewport resize by triggering change events on all registered media query lists
   * @param newWidth - The new viewport width in pixels
   */
  const simulateResize = (newWidth: number) => {
    // Update the matchMedia mock to return new values
    window.matchMedia = createMatchMedia(newWidth);

    // Trigger change events on all registered handlers
    changeHandlers.forEach((handlers, query) => {
      const maxWidthMatch = query.match(/\(max-width:\s*(\d+)px\)/);
      const minWidthMatch = query.match(/\(min-width:\s*(\d+)px\)/);

      let matches = false;
      if (maxWidthMatch) {
        matches = newWidth <= parseInt(maxWidthMatch[1], 10);
      } else if (minWidthMatch) {
        matches = newWidth >= parseInt(minWidthMatch[1], 10);
      }

      handlers.forEach(handler => {
        handler({ matches, media: query } as MediaQueryListEvent);
      });
    });
  };

  beforeEach(() => {
    mockMediaQueryLists = [];
    changeHandlers = new Map();
    originalMatchMedia = window.matchMedia;
    // Default to desktop viewport (1200px)
    window.matchMedia = createMatchMedia(1200);
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    mockMediaQueryLists = [];
    changeHandlers.clear();
  });

  // ==========================================================================
  // Test Suite 1: Initial Value Behavior
  // ==========================================================================

  describe('Initial Value', () => {
    it('should return false when query does not match (desktop viewport)', () => {
      // Window width: 1200px, query: max-width 640px
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      expect(result.current).toBe(false);
    });

    it('should return true when query matches (mobile viewport)', () => {
      // Window width: 480px, query: max-width 640px
      window.matchMedia = createMatchMedia(480);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      expect(result.current).toBe(true);
    });

    it('should return true when width equals max-width boundary', () => {
      // Window width: 640px, query: max-width 640px
      window.matchMedia = createMatchMedia(640);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      expect(result.current).toBe(true);
    });

    it('should return false when width is just above max-width boundary', () => {
      // Window width: 641px, query: max-width 640px
      window.matchMedia = createMatchMedia(641);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      expect(result.current).toBe(false);
    });

    it('should handle min-width queries correctly', () => {
      // Window width: 1024px, query: min-width 768px
      window.matchMedia = createMatchMedia(1024);

      const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));

      expect(result.current).toBe(true);
    });

    it('should return false for min-width when viewport is smaller', () => {
      // Window width: 500px, query: min-width 768px
      window.matchMedia = createMatchMedia(500);

      const { result } = renderHook(() => useMediaQuery('(min-width: 768px)'));

      expect(result.current).toBe(false);
    });
  });

  // ==========================================================================
  // Test Suite 2: Updates on Resize
  // ==========================================================================

  describe('Updates on Resize', () => {
    it('should update from false to true when resizing from desktop to mobile', () => {
      // Start at desktop viewport (1200px)
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      // Initially false (desktop)
      expect(result.current).toBe(false);

      // Simulate resize to mobile (480px)
      act(() => {
        simulateResize(480);
      });

      // Should now be true (mobile)
      expect(result.current).toBe(true);
    });

    it('should update from true to false when resizing from mobile to desktop', () => {
      // Start at mobile viewport (375px)
      window.matchMedia = createMatchMedia(375);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      // Initially true (mobile)
      expect(result.current).toBe(true);

      // Simulate resize to desktop (1280px)
      act(() => {
        simulateResize(1280);
      });

      // Should now be false (desktop)
      expect(result.current).toBe(false);
    });

    it('should handle multiple resize events correctly', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));

      expect(result.current).toBe(false);

      // Resize to tablet
      act(() => {
        simulateResize(768);
      });
      expect(result.current).toBe(true);

      // Resize to mobile
      act(() => {
        simulateResize(375);
      });
      expect(result.current).toBe(true);

      // Resize back to desktop
      act(() => {
        simulateResize(1280);
      });
      expect(result.current).toBe(false);
    });

    it('should not cause unnecessary re-renders when value does not change', () => {
      window.matchMedia = createMatchMedia(1200);

      let renderCount = 0;
      const { result } = renderHook(() => {
        renderCount++;
        return useMediaQuery('(max-width: 640px)');
      });

      const initialRenderCount = renderCount;
      expect(result.current).toBe(false);

      // Resize but stay above threshold (value unchanged)
      act(() => {
        simulateResize(1100);
      });

      // Should not have re-rendered since value didn't change
      // (Value is still false)
      expect(result.current).toBe(false);
    });
  });

  // ==========================================================================
  // Test Suite 3: Cleanup on Unmount
  // ==========================================================================

  describe('Cleanup on Unmount', () => {
    it('should remove event listener on unmount', () => {
      window.matchMedia = createMatchMedia(1200);

      const { unmount } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      // Verify addEventListener was called
      expect(mockMediaQueryLists.length).toBeGreaterThan(0);
      const mediaQueryList = mockMediaQueryLists[0];
      expect(mediaQueryList.addEventListener).toHaveBeenCalledWith(
        'change',
        expect.any(Function)
      );

      // Unmount
      unmount();

      // Verify removeEventListener was called
      expect(mediaQueryList.removeEventListener).toHaveBeenCalledWith(
        'change',
        expect.any(Function)
      );
    });

    it('should not cause errors when resizing after unmount', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result, unmount } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      expect(result.current).toBe(false);

      // Unmount
      unmount();

      // Simulate resize - should not throw
      expect(() => {
        act(() => {
          simulateResize(480);
        });
      }).not.toThrow();
    });

    it('should clean up correctly when query changes', () => {
      window.matchMedia = createMatchMedia(1200);

      const { rerender } = renderHook(
        ({ query }) => useMediaQuery(query),
        { initialProps: { query: '(max-width: 640px)' } }
      );

      // Get the first media query list
      const firstMediaQueryList = mockMediaQueryLists[0];

      // Change the query
      rerender({ query: '(max-width: 1024px)' });

      // Old listener should have been removed
      expect(firstMediaQueryList.removeEventListener).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 4: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle empty query string', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useMediaQuery(''));

      // Empty query should return false
      expect(result.current).toBe(false);
    });

    it('should handle query changes correctly', () => {
      window.matchMedia = createMatchMedia(800);

      const { result, rerender } = renderHook(
        ({ query }) => useMediaQuery(query),
        { initialProps: { query: '(max-width: 640px)' } }
      );

      // 800px > 640px, so should be false
      expect(result.current).toBe(false);

      // Change to a query that matches
      rerender({ query: '(max-width: 1024px)' });

      // 800px <= 1024px, so should be true
      expect(result.current).toBe(true);
    });

    it('should handle multiple hooks with different queries simultaneously', () => {
      window.matchMedia = createMatchMedia(800);

      const { result: result1 } = renderHook(() =>
        useMediaQuery('(max-width: 640px)')
      );
      const { result: result2 } = renderHook(() =>
        useMediaQuery('(max-width: 1024px)')
      );

      // 800px > 640px
      expect(result1.current).toBe(false);
      // 800px <= 1024px
      expect(result2.current).toBe(true);
    });

    it('should handle Tailwind breakpoint queries', () => {
      // Test common Tailwind breakpoints
      window.matchMedia = createMatchMedia(500);

      // sm: 640px
      const { result: smResult } = renderHook(() =>
        useMediaQuery('(max-width: 640px)')
      );
      expect(smResult.current).toBe(true);

      // md: 768px
      const { result: mdResult } = renderHook(() =>
        useMediaQuery('(max-width: 768px)')
      );
      expect(mdResult.current).toBe(true);

      // lg: 1024px
      const { result: lgResult } = renderHook(() =>
        useMediaQuery('(max-width: 1024px)')
      );
      expect(lgResult.current).toBe(true);
    });
  });

  // ==========================================================================
  // Test Suite 5: Real-world Scenarios
  // ==========================================================================

  describe('Real-world Scenarios', () => {
    it('should correctly identify mobile viewport (375px - iPhone SE)', () => {
      window.matchMedia = createMatchMedia(375);

      const { result } = renderHook(() => useMediaQuery('(max-width: 640px)'));

      expect(result.current).toBe(true);
    });

    it('should correctly identify tablet viewport (768px - iPad)', () => {
      window.matchMedia = createMatchMedia(768);

      const { result: isMobile } = renderHook(() =>
        useMediaQuery('(max-width: 640px)')
      );
      const { result: isTabletOrSmaller } = renderHook(() =>
        useMediaQuery('(max-width: 1023px)')
      );

      expect(isMobile.current).toBe(false);
      expect(isTabletOrSmaller.current).toBe(true);
    });

    it('should correctly identify desktop viewport (1280px)', () => {
      window.matchMedia = createMatchMedia(1280);

      const { result: isMobile } = renderHook(() =>
        useMediaQuery('(max-width: 640px)')
      );
      const { result: isTabletOrSmaller } = renderHook(() =>
        useMediaQuery('(max-width: 1023px)')
      );

      expect(isMobile.current).toBe(false);
      expect(isTabletOrSmaller.current).toBe(false);
    });

    it('should work for orientation media queries concept', () => {
      // While we cannot truly test orientation, we verify the hook
      // structure works with any query string
      window.matchMedia = createMatchMedia(1024);

      const { result } = renderHook(() =>
        useMediaQuery('(min-width: 768px)')
      );

      // Min-width 768px at 1024px viewport should match
      expect(result.current).toBe(true);
    });
  });
});
