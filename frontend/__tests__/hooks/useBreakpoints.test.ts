/**
 * useBreakpoints Hook Tests
 * TASK-FE-P7-009: Mobile Responsive Layouts - Phase A Tests
 *
 * Test Coverage:
 * 1. Returns correct breakpoint state for mobile viewport (isMobile)
 * 2. Returns correct breakpoint state for tablet viewport (isTablet)
 * 3. Returns correct breakpoint state for desktop viewport (isDesktop)
 * 4. Returns correct breakpoint state for large desktop viewport (isLargeDesktop)
 * 5. Returns correct breakpoint name
 * 6. Memoizes results correctly
 * 7. Updates on viewport resize
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '../testUtils';
import { useBreakpoints, BREAKPOINTS } from '@/hooks/useBreakpoints';

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

describe('useBreakpoints Hook', () => {
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
  // Test Suite 1: BREAKPOINTS Constants
  // ==========================================================================

  describe('BREAKPOINTS Constants', () => {
    it('should export correct Tailwind CSS 4 breakpoint values', () => {
      expect(BREAKPOINTS).toEqual({
        sm: 640,
        md: 768,
        lg: 1024,
        xl: 1280,
        '2xl': 1536,
      });
    });

    it('should have sm breakpoint at 640px', () => {
      expect(BREAKPOINTS.sm).toBe(640);
    });

    it('should have md breakpoint at 768px', () => {
      expect(BREAKPOINTS.md).toBe(768);
    });

    it('should have lg breakpoint at 1024px', () => {
      expect(BREAKPOINTS.lg).toBe(1024);
    });

    it('should have xl breakpoint at 1280px', () => {
      expect(BREAKPOINTS.xl).toBe(1280);
    });

    it('should have 2xl breakpoint at 1536px', () => {
      expect(BREAKPOINTS['2xl']).toBe(1536);
    });
  });

  // ==========================================================================
  // Test Suite 2: Mobile Viewport (<=640px)
  // ==========================================================================

  describe('Mobile Viewport (<=640px)', () => {
    it('should identify mobile viewport at 375px (iPhone SE)', () => {
      window.matchMedia = createMatchMedia(375);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(true);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.isLargeDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('mobile');
    });

    it('should identify mobile viewport at 320px (small mobile)', () => {
      window.matchMedia = createMatchMedia(320);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(true);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('mobile');
    });

    it('should identify mobile viewport at 480px (mobile landscape)', () => {
      window.matchMedia = createMatchMedia(480);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(true);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('mobile');
    });

    it('should identify mobile viewport at exactly 640px boundary', () => {
      window.matchMedia = createMatchMedia(640);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(true);
      expect(result.current.breakpoint).toBe('mobile');
    });
  });

  // ==========================================================================
  // Test Suite 3: Tablet Viewport (641px - 1023px)
  // ==========================================================================

  describe('Tablet Viewport (641px - 1023px)', () => {
    it('should identify tablet viewport at 768px (iPad portrait)', () => {
      window.matchMedia = createMatchMedia(768);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.isLargeDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('tablet');
    });

    it('should identify tablet viewport at 641px (just above mobile)', () => {
      window.matchMedia = createMatchMedia(641);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('tablet');
    });

    it('should identify tablet viewport at 1023px (just below desktop)', () => {
      window.matchMedia = createMatchMedia(1023);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('tablet');
    });

    it('should identify tablet viewport at 900px (mid-range tablet)', () => {
      window.matchMedia = createMatchMedia(900);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('tablet');
    });
  });

  // ==========================================================================
  // Test Suite 4: Desktop Viewport (1024px - 1279px)
  // ==========================================================================

  describe('Desktop Viewport (1024px - 1279px)', () => {
    it('should identify desktop viewport at 1024px (laptop)', () => {
      window.matchMedia = createMatchMedia(1024);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isLargeDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('desktop');
    });

    it('should identify desktop viewport at 1200px (standard laptop)', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isLargeDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('desktop');
    });

    it('should identify desktop viewport at 1279px (just below large desktop)', () => {
      window.matchMedia = createMatchMedia(1279);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isLargeDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('desktop');
    });
  });

  // ==========================================================================
  // Test Suite 5: Large Desktop Viewport (>=1280px)
  // ==========================================================================

  describe('Large Desktop Viewport (>=1280px)', () => {
    it('should identify large desktop viewport at 1280px', () => {
      window.matchMedia = createMatchMedia(1280);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isLargeDesktop).toBe(true);
      expect(result.current.breakpoint).toBe('largeDesktop');
    });

    it('should identify large desktop viewport at 1920px (Full HD)', () => {
      window.matchMedia = createMatchMedia(1920);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isLargeDesktop).toBe(true);
      expect(result.current.breakpoint).toBe('largeDesktop');
    });

    it('should identify large desktop viewport at 2560px (4K scaled)', () => {
      window.matchMedia = createMatchMedia(2560);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isLargeDesktop).toBe(true);
      expect(result.current.breakpoint).toBe('largeDesktop');
    });
  });

  // ==========================================================================
  // Test Suite 6: Viewport Transitions (Resize)
  // ==========================================================================

  describe('Viewport Transitions (Resize)', () => {
    it('should update from desktop to mobile on resize', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      // Initially desktop
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isMobile).toBe(false);
      expect(result.current.breakpoint).toBe('desktop');

      // Resize to mobile
      act(() => {
        simulateResize(375);
      });

      expect(result.current.isMobile).toBe(true);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.breakpoint).toBe('mobile');
    });

    it('should update from mobile to tablet on resize', () => {
      window.matchMedia = createMatchMedia(375);

      const { result } = renderHook(() => useBreakpoints());

      // Initially mobile
      expect(result.current.isMobile).toBe(true);
      expect(result.current.breakpoint).toBe('mobile');

      // Resize to tablet
      act(() => {
        simulateResize(768);
      });

      expect(result.current.isMobile).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.breakpoint).toBe('tablet');
    });

    it('should update from tablet to desktop on resize', () => {
      window.matchMedia = createMatchMedia(768);

      const { result } = renderHook(() => useBreakpoints());

      // Initially tablet
      expect(result.current.isTablet).toBe(true);
      expect(result.current.breakpoint).toBe('tablet');

      // Resize to desktop
      act(() => {
        simulateResize(1024);
      });

      expect(result.current.isTablet).toBe(false);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.breakpoint).toBe('desktop');
    });

    it('should handle rapid resize events correctly', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      // Rapid resizes
      act(() => {
        simulateResize(768);
      });
      expect(result.current.breakpoint).toBe('tablet');

      act(() => {
        simulateResize(375);
      });
      expect(result.current.breakpoint).toBe('mobile');

      act(() => {
        simulateResize(1280);
      });
      expect(result.current.breakpoint).toBe('largeDesktop');

      act(() => {
        simulateResize(1024);
      });
      expect(result.current.breakpoint).toBe('desktop');
    });
  });

  // ==========================================================================
  // Test Suite 7: Return Type and Structure
  // ==========================================================================

  describe('Return Type and Structure', () => {
    it('should return object with all expected properties', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      expect(result.current).toHaveProperty('isMobile');
      expect(result.current).toHaveProperty('isTablet');
      expect(result.current).toHaveProperty('isDesktop');
      expect(result.current).toHaveProperty('isLargeDesktop');
      expect(result.current).toHaveProperty('breakpoint');
    });

    it('should return boolean types for all boolean properties', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      expect(typeof result.current.isMobile).toBe('boolean');
      expect(typeof result.current.isTablet).toBe('boolean');
      expect(typeof result.current.isDesktop).toBe('boolean');
      expect(typeof result.current.isLargeDesktop).toBe('boolean');
    });

    it('should return string type for breakpoint property', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      expect(typeof result.current.breakpoint).toBe('string');
    });

    it('should return one of the valid breakpoint names', () => {
      const validBreakpoints = ['mobile', 'tablet', 'desktop', 'largeDesktop'];
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      expect(validBreakpoints).toContain(result.current.breakpoint);
    });
  });

  // ==========================================================================
  // Test Suite 8: Memoization
  // ==========================================================================

  describe('Memoization', () => {
    it('should return stable object reference when values do not change', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result, rerender } = renderHook(() => useBreakpoints());

      const firstResult = result.current;

      // Force rerender without changing viewport
      rerender();

      // Should be the same object reference due to memoization
      expect(result.current).toBe(firstResult);
    });

    it('should return new object reference when values change', () => {
      window.matchMedia = createMatchMedia(1200);

      const { result } = renderHook(() => useBreakpoints());

      const firstResult = result.current;

      // Change viewport
      act(() => {
        simulateResize(375);
      });

      // Should be a different object reference
      expect(result.current).not.toBe(firstResult);
      expect(result.current.breakpoint).not.toBe(firstResult.breakpoint);
    });
  });

  // ==========================================================================
  // Test Suite 9: Real-world Use Cases
  // ==========================================================================

  describe('Real-world Use Cases', () => {
    it('should work for conditional component rendering based on breakpoint', () => {
      window.matchMedia = createMatchMedia(375);

      const { result } = renderHook(() => useBreakpoints());

      // Simulate conditional rendering logic
      const shouldShowMobileNav = result.current.isMobile;
      const shouldShowDesktopSidebar = result.current.isDesktop;

      expect(shouldShowMobileNav).toBe(true);
      expect(shouldShowDesktopSidebar).toBe(false);
    });

    it('should work for conditional class application based on breakpoint', () => {
      window.matchMedia = createMatchMedia(768);

      const { result } = renderHook(() => useBreakpoints());

      // Simulate conditional class logic
      const containerClass = result.current.isMobile ? 'p-4' : 'p-8';
      const gridCols = result.current.isMobile
        ? 'grid-cols-1'
        : result.current.isTablet
        ? 'grid-cols-2'
        : 'grid-cols-3';

      expect(containerClass).toBe('p-8'); // Tablet uses desktop padding
      expect(gridCols).toBe('grid-cols-2');
    });

    it('should correctly identify calculator wizard layout requirements', () => {
      // Mobile: vertical stepper, reduced padding
      window.matchMedia = createMatchMedia(375);

      const { result: mobileResult } = renderHook(() => useBreakpoints());
      expect(mobileResult.current.isMobile).toBe(true);

      // Tablet: horizontal stepper, abbreviated labels
      window.matchMedia = createMatchMedia(768);

      const { result: tabletResult } = renderHook(() => useBreakpoints());
      expect(tabletResult.current.isTablet).toBe(true);

      // Desktop: full stepper with complete labels
      window.matchMedia = createMatchMedia(1280);

      const { result: desktopResult } = renderHook(() => useBreakpoints());
      expect(desktopResult.current.isDesktop).toBe(true);
    });
  });
});
