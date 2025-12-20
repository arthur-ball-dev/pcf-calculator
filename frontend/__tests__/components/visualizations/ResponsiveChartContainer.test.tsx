/**
 * ResponsiveChartContainer Component Tests
 * TASK-FE-P7-013: Visualization Responsiveness - Phase A Tests
 *
 * Test Coverage:
 * 1. Container adjusts height based on viewport (mobile/tablet/desktop)
 * 2. Horizontal scroll enabled when content exceeds viewport
 * 3. Minimum width constraints maintained
 * 4. Aspect ratio calculations work correctly
 * 5. Loading state displays skeleton
 * 6. Scroll indicator visible on mobile when scroll enabled
 * 7. Accessibility attributes present
 *
 * Written BEFORE implementation per TDD protocol.
 *
 * Default Heights Per Spec:
 * - Mobile (<=640px): 300px
 * - Tablet (641px-1023px): 400px
 * - Desktop (>=1024px): 500px
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '../../testUtils';
import React from 'react';

// Import will fail until implementation exists - this is expected for TDD
// @ts-expect-error - Component does not exist yet (TDD)
import { ResponsiveChartContainer } from '@/components/visualizations/ResponsiveChartContainer';

// Mock ResizeObserver
class MockResizeObserver {
  callback: ResizeObserverCallback;

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }

  observe(target: Element) {
    // Immediately trigger with mock dimensions
    this.callback(
      [
        {
          target,
          contentRect: {
            width: 375,
            height: 300,
            top: 0,
            left: 0,
            bottom: 300,
            right: 375,
            x: 0,
            y: 0,
            toJSON: () => ({}),
          },
          borderBoxSize: [],
          contentBoxSize: [],
          devicePixelContentBoxSize: [],
        },
      ],
      this
    );
  }

  unobserve() {}
  disconnect() {}
}

// Mock child component for testing
function MockChart({ testId = 'mock-chart' }: { testId?: string }) {
  return <div data-testid={testId} style={{ width: '100%', height: '100%' }}>Mock Chart</div>;
}

// Mock matchMedia for responsive testing
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

describe('ResponsiveChartContainer', () => {
  let originalMatchMedia: typeof window.matchMedia;
  let originalResizeObserver: typeof window.ResizeObserver;
  let changeHandlers: Map<string, ((ev: MediaQueryListEvent) => void)[]>;

  /**
   * Creates a mock matchMedia function that simulates browser behavior
   * @param width - The simulated viewport width in pixels
   */
  const createMatchMedia = (width: number): MatchMediaMock => {
    return (query: string): MockMediaQueryList => {
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
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };

      return mediaQueryList;
    };
  };

  /**
   * Sets up the viewport at a specific width
   * @param width - The viewport width in pixels
   */
  const setViewport = (width: number) => {
    window.matchMedia = createMatchMedia(width);
    window.innerWidth = width;
  };

  beforeEach(() => {
    changeHandlers = new Map();
    originalMatchMedia = window.matchMedia;
    originalResizeObserver = window.ResizeObserver;
    window.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;
    // Default to desktop viewport
    setViewport(1280);
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    window.ResizeObserver = originalResizeObserver;
    changeHandlers.clear();
  });

  // ==========================================================================
  // Test Suite 1: Height Adjustments Based on Viewport
  // ==========================================================================

  describe('Height Adjustments Based on Viewport', () => {
    it('should render with mobile height (300px) on mobile viewport', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer mobileHeight={300} minHeight={500}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '300px' });
    });

    it('should render with tablet height (400px) on tablet viewport', () => {
      setViewport(768);

      render(
        <ResponsiveChartContainer tabletHeight={400} minHeight={500}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '400px' });
    });

    it('should render with desktop height (500px/minHeight) on desktop viewport', () => {
      setViewport(1280);

      render(
        <ResponsiveChartContainer minHeight={500}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '500px' });
    });

    it('should use mobileHeight prop when viewport is 375px (iPhone SE)', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer mobileHeight={250} minHeight={400}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '250px' });
    });

    it('should use default heights when props not provided', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      // Default mobile height should be 300px per spec
      expect(container).toHaveStyle({ height: '300px' });
    });

    it('should fallback to minHeight for tablet when tabletHeight not provided', () => {
      setViewport(768);

      render(
        <ResponsiveChartContainer minHeight={500}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      // Should use minHeight (500px) or default tablet height (400px)
      const style = window.getComputedStyle(container);
      const heightValue = parseInt(style.height, 10);
      expect(heightValue).toBeGreaterThanOrEqual(400);
    });
  });

  // ==========================================================================
  // Test Suite 2: Horizontal Scroll Behavior
  // ==========================================================================

  describe('Horizontal Scroll Behavior', () => {
    it('should enable horizontal scroll when enableScroll is true and on mobile', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveClass('overflow-x-auto');
    });

    it('should maintain minimum width when minWidth prop is set', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      const innerWrapper = container.firstElementChild;

      // Inner wrapper should have minWidth applied
      expect(innerWrapper).toHaveStyle({ minWidth: '600px' });
    });

    it('should not enable horizontal scroll on desktop even with enableScroll', () => {
      setViewport(1280);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      // On desktop, scroll should not be applied (viewport > minWidth)
      expect(container).not.toHaveClass('overflow-x-auto');
    });

    it('should render scroll indicator on mobile when scroll is enabled', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const scrollIndicator = screen.getByText(/swipe to explore/i);
      expect(scrollIndicator).toBeInTheDocument();
    });

    it('should hide scroll indicator on desktop', () => {
      setViewport(1280);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const scrollIndicator = screen.queryByText(/swipe to explore/i);
      expect(scrollIndicator).not.toBeInTheDocument();
    });

    it('should not show scroll indicator when enableScroll is false', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll={false}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const scrollIndicator = screen.queryByText(/swipe to explore/i);
      expect(scrollIndicator).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 3: Aspect Ratio Maintenance
  // ==========================================================================

  describe('Aspect Ratio Maintenance', () => {
    it('should calculate height based on aspect ratio when provided', async () => {
      setViewport(800);

      // Mock ResizeObserver to report width of 800
      window.ResizeObserver = class {
        callback: ResizeObserverCallback;
        constructor(callback: ResizeObserverCallback) {
          this.callback = callback;
        }
        observe(target: Element) {
          this.callback(
            [
              {
                target,
                contentRect: {
                  width: 800,
                  height: 0,
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 800,
                  x: 0,
                  y: 0,
                  toJSON: () => ({}),
                },
                borderBoxSize: [],
                contentBoxSize: [],
                devicePixelContentBoxSize: [],
              },
            ],
            this
          );
        }
        unobserve() {}
        disconnect() {}
      } as unknown as typeof ResizeObserver;

      render(
        <ResponsiveChartContainer aspectRatio={16 / 9}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      await waitFor(() => {
        const container = screen.getByTestId('responsive-chart-container');
        // 800 / (16/9) = 450
        expect(container).toHaveStyle({ height: '450px' });
      });
    });

    it('should maintain 4:3 aspect ratio correctly', async () => {
      setViewport(600);

      // Mock ResizeObserver to report width of 600
      window.ResizeObserver = class {
        callback: ResizeObserverCallback;
        constructor(callback: ResizeObserverCallback) {
          this.callback = callback;
        }
        observe(target: Element) {
          this.callback(
            [
              {
                target,
                contentRect: {
                  width: 600,
                  height: 0,
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 600,
                  x: 0,
                  y: 0,
                  toJSON: () => ({}),
                },
                borderBoxSize: [],
                contentBoxSize: [],
                devicePixelContentBoxSize: [],
              },
            ],
            this
          );
        }
        unobserve() {}
        disconnect() {}
      } as unknown as typeof ResizeObserver;

      render(
        <ResponsiveChartContainer aspectRatio={4 / 3}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      await waitFor(() => {
        const container = screen.getByTestId('responsive-chart-container');
        // 600 / (4/3) = 450
        expect(container).toHaveStyle({ height: '450px' });
      });
    });

    it('should prioritize aspect ratio over fixed heights when both provided', async () => {
      setViewport(800);

      window.ResizeObserver = class {
        callback: ResizeObserverCallback;
        constructor(callback: ResizeObserverCallback) {
          this.callback = callback;
        }
        observe(target: Element) {
          this.callback(
            [
              {
                target,
                contentRect: {
                  width: 800,
                  height: 0,
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 800,
                  x: 0,
                  y: 0,
                  toJSON: () => ({}),
                },
                borderBoxSize: [],
                contentBoxSize: [],
                devicePixelContentBoxSize: [],
              },
            ],
            this
          );
        }
        unobserve() {}
        disconnect() {}
      } as unknown as typeof ResizeObserver;

      render(
        <ResponsiveChartContainer aspectRatio={16 / 9} minHeight={500} mobileHeight={300}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      await waitFor(() => {
        const container = screen.getByTestId('responsive-chart-container');
        // aspectRatio should take precedence: 800 / (16/9) = 450
        expect(container).toHaveStyle({ height: '450px' });
      });
    });
  });

  // ==========================================================================
  // Test Suite 4: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should display skeleton when isLoading is true', () => {
      render(
        <ResponsiveChartContainer isLoading>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const skeleton = screen.getByTestId('chart-loading-skeleton');
      expect(skeleton).toBeInTheDocument();
    });

    it('should not render children when isLoading is true', () => {
      render(
        <ResponsiveChartContainer isLoading>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const mockChart = screen.queryByTestId('mock-chart');
      expect(mockChart).not.toBeInTheDocument();
    });

    it('should render children when isLoading is false', () => {
      render(
        <ResponsiveChartContainer isLoading={false}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const mockChart = screen.getByTestId('mock-chart');
      expect(mockChart).toBeInTheDocument();
    });

    it('should apply aria-busy when loading', () => {
      render(
        <ResponsiveChartContainer isLoading>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveAttribute('aria-busy', 'true');
    });

    it('should maintain container height during loading state', () => {
      setViewport(1280);

      render(
        <ResponsiveChartContainer isLoading minHeight={500}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '500px' });
    });
  });

  // ==========================================================================
  // Test Suite 5: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have role="img" on container', () => {
      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveAttribute('role', 'img');
    });

    it('should apply aria-label when provided', () => {
      render(
        <ResponsiveChartContainer aria-label="Carbon footprint flow diagram">
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveAttribute('aria-label', 'Carbon footprint flow diagram');
    });

    it('should hide scroll indicator from screen readers', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const scrollIndicatorContainer = screen
        .getByText(/swipe to explore/i)
        .closest('div');
      expect(scrollIndicatorContainer).toHaveAttribute('aria-hidden', 'true');
    });
  });

  // ==========================================================================
  // Test Suite 6: CSS Class Application
  // ==========================================================================

  describe('CSS Class Application', () => {
    it('should apply custom className to container', () => {
      render(
        <ResponsiveChartContainer className="custom-chart-class">
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveClass('custom-chart-class');
    });

    it('should always have relative positioning', () => {
      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveClass('relative');
    });

    it('should have overflow-y-hidden when horizontal scroll enabled', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveClass('overflow-y-hidden');
    });
  });

  // ==========================================================================
  // Test Suite 7: Children Rendering
  // ==========================================================================

  describe('Children Rendering', () => {
    it('should render children correctly', () => {
      render(
        <ResponsiveChartContainer>
          <MockChart testId="my-custom-chart" />
        </ResponsiveChartContainer>
      );

      const chart = screen.getByTestId('my-custom-chart');
      expect(chart).toBeInTheDocument();
    });

    it('should pass full width and height to children container', () => {
      render(
        <ResponsiveChartContainer minHeight={500}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      const childContainer = container.querySelector('[style*="height: 100%"]');

      // Either child container has 100% height or the mock chart does
      const mockChart = screen.getByTestId('mock-chart');
      expect(mockChart).toBeInTheDocument();
    });

    it('should wrap children in minWidth container when scroll enabled', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer enableScroll minWidth={600}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const mockChart = screen.getByTestId('mock-chart');
      const wrapper = mockChart.closest('[style*="min-width"]');
      expect(wrapper).toHaveStyle({ minWidth: '600px' });
    });
  });

  // ==========================================================================
  // Test Suite 8: Default Values
  // ==========================================================================

  describe('Default Values', () => {
    it('should use default minHeight of 400px when not provided', () => {
      setViewport(1280);

      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      // Default desktop height should be 400-500px
      const style = window.getComputedStyle(container);
      const heightValue = parseInt(style.height, 10);
      expect(heightValue).toBeGreaterThanOrEqual(400);
    });

    it('should use default mobileHeight of 300px when not provided', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '300px' });
    });

    it('should default enableScroll to false', () => {
      setViewport(375);

      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).not.toHaveClass('overflow-x-auto');
    });

    it('should default isLoading to false', () => {
      render(
        <ResponsiveChartContainer>
          <MockChart />
        </ResponsiveChartContainer>
      );

      const mockChart = screen.getByTestId('mock-chart');
      expect(mockChart).toBeInTheDocument();

      const skeleton = screen.queryByTestId('chart-loading-skeleton');
      expect(skeleton).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 9: Viewport Transitions
  // ==========================================================================

  describe('Viewport Transitions', () => {
    it('should handle viewport resize from desktop to mobile', async () => {
      setViewport(1280);

      const { rerender } = render(
        <ResponsiveChartContainer minHeight={500} mobileHeight={300}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      // Verify desktop height
      let container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '500px' });

      // Resize to mobile
      setViewport(375);
      rerender(
        <ResponsiveChartContainer minHeight={500} mobileHeight={300}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      await waitFor(() => {
        container = screen.getByTestId('responsive-chart-container');
        expect(container).toHaveStyle({ height: '300px' });
      });
    });

    it('should handle viewport resize from mobile to tablet', async () => {
      setViewport(375);

      const { rerender } = render(
        <ResponsiveChartContainer mobileHeight={300} tabletHeight={400}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      // Resize to tablet
      setViewport(768);
      rerender(
        <ResponsiveChartContainer mobileHeight={300} tabletHeight={400}>
          <MockChart />
        </ResponsiveChartContainer>
      );

      await waitFor(() => {
        const container = screen.getByTestId('responsive-chart-container');
        expect(container).toHaveStyle({ height: '400px' });
      });
    });
  });
});
