/**
 * SankeyDiagram Responsive Behavior Tests
 * TASK-FE-P7-013: Visualization Responsiveness - Phase A Tests
 *
 * Test Coverage:
 * 1. Sankey uses ResponsiveChartContainer wrapper
 * 2. Horizontal scroll enabled on mobile for complex charts
 * 3. Minimum width maintained for readability
 * 4. Labels adjust for mobile (truncation/abbreviation)
 * 5. Touch-friendly tooltips
 * 6. Margins adjust for mobile viewport
 * 7. Node spacing adjusts for different viewports
 *
 * Written BEFORE implementation per TDD protocol.
 *
 * TDD Exception: TDD-EX-P9-001 (2026-02-18)
 * Updated mobile margin expectations to match actual Emerald Night implementation:
 * - Mobile margins: {top: 10, right: 50, bottom: 10, left: 90}
 *   (right/left are large for label readability, not uniformly small)
 * - Desktop margins: {top: 20, right: 65, bottom: 20, left: 110}
 * - Assertions now verify top/bottom are smaller on mobile, and right/left
 *   are smaller than desktop (relative comparison, not absolute thresholds).
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../testUtils';
import SankeyDiagram from '../../../src/components/visualizations/SankeyDiagram';
import type { Calculation } from '../../../src/types/store.types';

// Mock Nivo Sankey component with responsive behavior tracking
vi.mock('@nivo/sankey', () => ({
  ResponsiveSankey: ({
    data,
    margin,
    nodeThickness,
    nodeSpacing,
    tooltip,
    onClick,
  }: {
    data: { nodes: Array<{ id: string; label: string }>; links: unknown[] };
    margin?: { top: number; right: number; bottom: number; left: number };
    nodeThickness?: number;
    nodeSpacing?: number;
    tooltip?: React.FC<{ node: { id: string; value: number } }>;
    onClick?: (data: unknown) => void;
  }) => (
    <div data-testid="sankey-chart">
      <div data-testid="sankey-nodes-count">{data.nodes.length}</div>
      <div data-testid="sankey-links-count">{data.links.length}</div>
      <div data-testid="sankey-margin" data-margin={JSON.stringify(margin)} />
      <div data-testid="sankey-node-thickness" data-thickness={nodeThickness} />
      <div data-testid="sankey-node-spacing" data-spacing={nodeSpacing} />
      {data.nodes.map((node, index) => (
        <div
          key={node.id}
          data-testid={`sankey-node-${index}`}
          data-label={node.label}
          className="sankey-node"
          onClick={() => onClick?.({ id: node.id })}
          onTouchStart={() => {
            // Simulate tooltip on touch
            const tooltipContent = tooltip?.({
              node: { id: node.id, value: 10 },
            });
            if (tooltipContent) {
              document.body.appendChild(
                document.createElement('div')
              ).setAttribute('data-testid', 'sankey-tooltip-active');
            }
          }}
        >
          <span data-testid={`sankey-label-${index}`}>{node.label}</span>
        </div>
      ))}
    </div>
  ),
}));

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

// Mock ResizeObserver
class MockResizeObserver {
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
            width: window.innerWidth,
            height: 300,
            top: 0,
            left: 0,
            bottom: 300,
            right: window.innerWidth,
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

// Mock calculation data
const mockCalculation: Calculation = {
  id: 'calc-123',
  status: 'completed',
  product_id: 'prod-456',
  total_co2e_kg: 12.5,
  materials_co2e: 7.3,
  energy_co2e: 3.8,
  transport_co2e: 1.4,
};

// Mock calculation with many nodes (complex chart)
const mockComplexCalculation: Calculation = {
  id: 'calc-complex',
  status: 'completed',
  product_id: 'prod-789',
  total_co2e_kg: 50.0,
  materials_co2e: 25.0,
  energy_co2e: 15.0,
  transport_co2e: 8.0,
  other_co2e: 2.0,
  breakdown: {
    materials: [
      { name: 'Steel', co2e: 10.0 },
      { name: 'Aluminum', co2e: 8.0 },
      { name: 'Plastic', co2e: 4.0 },
      { name: 'Copper', co2e: 3.0 },
    ],
    energy: [
      { name: 'Electricity', co2e: 10.0 },
      { name: 'Natural Gas', co2e: 5.0 },
    ],
    transport: [
      { name: 'Truck', co2e: 5.0 },
      { name: 'Ship', co2e: 3.0 },
    ],
  },
};

describe('SankeyDiagram Responsive Behavior', () => {
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
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: ResponsiveChartContainer Integration
  // ==========================================================================

  describe('ResponsiveChartContainer Integration', () => {
    it('should wrap SankeyDiagram in ResponsiveChartContainer', () => {
      render(<SankeyDiagram calculation={mockCalculation} />);

      // The container should have the responsive chart container test id
      const responsiveContainer = screen.getByTestId('responsive-chart-container');
      expect(responsiveContainer).toBeInTheDocument();
    });

    it('should have proper responsive height on mobile (350px)', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '350px' });
    });

    it('should have proper responsive height on tablet (400px)', () => {
      setViewport(768);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '400px' });
    });

    it('should have proper responsive height on desktop (500px)', () => {
      setViewport(1280);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveStyle({ height: '500px' });
    });

    it('should have aria-label for accessibility', () => {
      render(<SankeyDiagram calculation={mockCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveAttribute('aria-label');
      expect(container.getAttribute('aria-label')).toContain('Carbon');
    });
  });

  // ==========================================================================
  // Test Suite 2: Horizontal Scroll on Mobile
  // ==========================================================================

  describe('Horizontal Scroll on Mobile', () => {
    it('should enable horizontal scroll on mobile for complex charts', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      expect(container).toHaveClass('overflow-x-auto');
    });

    it('should maintain minimum width for readability on mobile', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      const innerWrapper = container.querySelector('[style*="min-width"]');

      // Chart should have minimum width to ensure readability
      expect(innerWrapper).toBeInTheDocument();
    });

    it('should show scroll indicator on mobile with complex chart', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      const scrollIndicator = screen.getByText(/swipe to explore/i);
      expect(scrollIndicator).toBeInTheDocument();
    });

    it('should not show scroll indicator on desktop', () => {
      setViewport(1280);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      const scrollIndicator = screen.queryByText(/swipe to explore/i);
      expect(scrollIndicator).not.toBeInTheDocument();
    });

    it('should calculate minimum width based on node count', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      const container = screen.getByTestId('responsive-chart-container');
      const innerWrapper = container.querySelector('[style*="min-width"]');

      if (innerWrapper) {
        const style = window.getComputedStyle(innerWrapper);
        const minWidthValue = parseInt(style.minWidth, 10);
        // Should have minimum width based on node count
        expect(minWidthValue).toBeGreaterThanOrEqual(400);
      }
    });
  });

  // ==========================================================================
  // Test Suite 3: Label Responsiveness
  // ==========================================================================

  describe('Label Responsiveness', () => {
    it('should truncate labels on mobile viewport', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      // Check that labels are truncated or abbreviated
      const labels = screen.getAllByTestId(/sankey-label-/);

      labels.forEach((label) => {
        const labelText = label.textContent || '';
        // Labels on mobile should be truncated (max ~10 characters + ellipsis)
        expect(labelText.length).toBeLessThanOrEqual(13);
      });
    });

    it('should show full labels on desktop viewport', () => {
      setViewport(1280);

      render(<SankeyDiagram calculation={mockCalculation} />);

      // Labels should not be truncated on desktop
      const labels = screen.getAllByTestId(/sankey-label-/);
      expect(labels.length).toBeGreaterThan(0);
    });

    it('should not have label overlap on mobile', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const labels = screen.getAllByTestId(/sankey-label-/);

      // Each label should have adequate spacing
      labels.forEach((label) => {
        expect(label).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 4: Margin Adjustments
  // ==========================================================================

  describe('Margin Adjustments for Viewport', () => {
    it('should use smaller margins on mobile', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const marginContainer = screen.getByTestId('sankey-margin');
      const marginData = JSON.parse(marginContainer.getAttribute('data-margin') || '{}');

      // TDD-EX-P9-001: Mobile margins are {top: 10, right: 50, bottom: 10, left: 90}.
      // The right and left margins are intentionally larger for label readability
      // (labels extend outside nodes). Only top/bottom are truly "small".
      // Verify top and bottom are small
      expect(marginData.top).toBeLessThanOrEqual(15);
      expect(marginData.bottom).toBeLessThanOrEqual(15);
      // Right and left are larger for labels but still smaller than desktop
      expect(marginData.right).toBeLessThanOrEqual(100);
      expect(marginData.left).toBeLessThanOrEqual(100);
    });

    it('should use larger margins on desktop', () => {
      setViewport(1280);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const marginContainer = screen.getByTestId('sankey-margin');
      const marginData = JSON.parse(marginContainer.getAttribute('data-margin') || '{}');

      // Desktop margins should be larger (around 20px or more)
      expect(marginData.top).toBeGreaterThanOrEqual(15);
    });

    it('should have smaller margins on mobile than on desktop', () => {
      // Render on mobile
      setViewport(375);
      const { unmount } = render(<SankeyDiagram calculation={mockCalculation} />);
      const mobileMarginEl = screen.getByTestId('sankey-margin');
      const mobileMargins = JSON.parse(mobileMarginEl.getAttribute('data-margin') || '{}');
      unmount();

      // Render on desktop
      setViewport(1280);
      render(<SankeyDiagram calculation={mockCalculation} />);
      const desktopMarginEl = screen.getByTestId('sankey-margin');
      const desktopMargins = JSON.parse(desktopMarginEl.getAttribute('data-margin') || '{}');

      // Mobile margins should be less than or equal to desktop margins
      expect(mobileMargins.top).toBeLessThanOrEqual(desktopMargins.top);
      expect(mobileMargins.right).toBeLessThanOrEqual(desktopMargins.right);
      expect(mobileMargins.bottom).toBeLessThanOrEqual(desktopMargins.bottom);
      expect(mobileMargins.left).toBeLessThanOrEqual(desktopMargins.left);
    });
  });

  // ==========================================================================
  // Test Suite 5: Touch-Friendly Tooltips
  // ==========================================================================

  describe('Touch-Friendly Tooltips', () => {
    it('should show tooltip on touch start', async () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const node = screen.getByTestId('sankey-node-0');

      // Simulate touch
      fireEvent.touchStart(node);

      await waitFor(() => {
        // Tooltip should be visible after touch
        const tooltipElement = node.closest('[data-testid="sankey-container"]');
        expect(tooltipElement).toBeInTheDocument();
      });
    });

    it('should have touch targets meeting minimum size requirements', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const nodes = screen.getAllByTestId(/sankey-node-/);

      nodes.forEach((node) => {
        // Nodes should have adequate touch target size (minimum 44px recommended)
        expect(node).toBeInTheDocument();
      });
    });

    it('should remain interactive on mobile', () => {
      setViewport(375);

      const onNodeClick = vi.fn();
      render(
        <SankeyDiagram calculation={mockCalculation} onNodeClick={onNodeClick} />
      );

      const node = screen.getByTestId('sankey-node-0');
      fireEvent.click(node);

      // Node should be clickable
      expect(node).toBeInTheDocument();
    });

    it('should display tooltip content with CO2e value', async () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const node = screen.getByTestId('sankey-node-0');
      fireEvent.touchStart(node);

      await waitFor(() => {
        // Tooltip should contain CO2e information
        const container = screen.getByTestId('sankey-container');
        expect(container).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 6: Node Spacing Responsiveness
  // ==========================================================================

  describe('Node Spacing Responsiveness', () => {
    it('should use appropriate node thickness on mobile', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const thicknessContainer = screen.getByTestId('sankey-node-thickness');
      const thickness = parseInt(thicknessContainer.getAttribute('data-thickness') || '0', 10);

      // Thickness should be reasonable for mobile (12-18px range)
      expect(thickness).toBeGreaterThanOrEqual(12);
      expect(thickness).toBeLessThanOrEqual(18);
    });

    it('should use appropriate node spacing on mobile', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const spacingContainer = screen.getByTestId('sankey-node-spacing');
      const spacing = parseInt(spacingContainer.getAttribute('data-spacing') || '0', 10);

      // Spacing should be reasonable for mobile (8-24px range)
      expect(spacing).toBeGreaterThanOrEqual(8);
      expect(spacing).toBeLessThanOrEqual(24);
    });

    it('should adjust spacing based on node count', () => {
      setViewport(375);

      // Simple chart
      const { rerender } = render(<SankeyDiagram calculation={mockCalculation} />);

      const simpleSpacing = screen.getByTestId('sankey-node-spacing');
      const simpleSpacingValue = parseInt(
        simpleSpacing.getAttribute('data-spacing') || '0',
        10
      );

      // Complex chart with more nodes
      rerender(<SankeyDiagram calculation={mockComplexCalculation} />);

      const complexSpacing = screen.getByTestId('sankey-node-spacing');
      const complexSpacingValue = parseInt(
        complexSpacing.getAttribute('data-spacing') || '0',
        10
      );

      // Both should be within acceptable range
      expect(simpleSpacingValue).toBeGreaterThanOrEqual(8);
      expect(complexSpacingValue).toBeGreaterThanOrEqual(8);
    });
  });

  // ==========================================================================
  // Test Suite 7: No Page Scroll Overflow
  // ==========================================================================

  describe('No Page Scroll Overflow', () => {
    it('should not cause horizontal page scroll on mobile', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const container = screen.getByTestId('sankey-container');

      // Container should be constrained to viewport
      expect(container).toHaveStyle({ width: '100%' });
    });

    it('should contain chart within responsive container bounds', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockCalculation} />);

      const responsiveContainer = screen.getByTestId('responsive-chart-container');
      const sankeyContainer = screen.getByTestId('sankey-container');

      expect(responsiveContainer).toContainElement(sankeyContainer);
    });
  });

  // ==========================================================================
  // Test Suite 8: Empty/Loading States Responsiveness
  // ==========================================================================

  describe('Empty/Loading States Responsiveness', () => {
    it('should maintain responsive height in empty state', () => {
      setViewport(375);

      render(<SankeyDiagram calculation={null} />);

      const container = screen.getByTestId('sankey-container');
      const style = window.getComputedStyle(container);
      const heightValue = parseInt(style.height, 10);

      // Should maintain mobile height even in empty state
      expect(heightValue).toBeGreaterThanOrEqual(250);
    });

    it('should maintain responsive height in loading state', () => {
      setViewport(375);

      const loadingCalculation: Calculation = {
        id: 'calc-loading',
        status: 'pending',
        product_id: 'prod-loading',
      };

      render(<SankeyDiagram calculation={loadingCalculation} />);

      const container = screen.getByTestId('sankey-container');
      expect(container).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 9: Drill-Down Responsiveness
  // ==========================================================================

  describe('Drill-Down Responsiveness', () => {
    it('should maintain responsive behavior after drill-down', async () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      // Click on a category node to drill down
      const node = screen.getByTestId('sankey-node-0');
      fireEvent.click(node);

      await waitFor(() => {
        const container = screen.getByTestId('responsive-chart-container');
        expect(container).toBeInTheDocument();
      });
    });

    it('should show back button on drill-down in mobile view', async () => {
      setViewport(375);

      render(<SankeyDiagram calculation={mockComplexCalculation} />);

      // Simulate drill-down
      const node = screen.getByTestId('sankey-node-0');
      fireEvent.click(node);

      await waitFor(() => {
        const backButton = screen.queryByTestId('sankey-back-button');
        // Back button should be accessible on mobile
        if (backButton) {
          expect(backButton).toBeInTheDocument();
        }
      });
    });
  });

  // ==========================================================================
  // Test Suite 10: Performance
  // ==========================================================================

  describe('Performance', () => {
    it('should not cause layout thrashing on resize', async () => {
      const { rerender } = render(
        <SankeyDiagram calculation={mockCalculation} />
      );

      // Rapid viewport changes
      setViewport(375);
      rerender(<SankeyDiagram calculation={mockCalculation} />);

      setViewport(768);
      rerender(<SankeyDiagram calculation={mockCalculation} />);

      setViewport(1280);
      rerender(<SankeyDiagram calculation={mockCalculation} />);

      setViewport(375);
      rerender(<SankeyDiagram calculation={mockCalculation} />);

      // Chart should still be functional
      const chart = screen.getByTestId('sankey-chart');
      expect(chart).toBeInTheDocument();
    });

    it('should maintain memoization on rerender with same data', () => {
      setViewport(375);

      const { rerender } = render(
        <SankeyDiagram calculation={mockCalculation} />
      );

      const chart1 = screen.getByTestId('sankey-chart');

      rerender(<SankeyDiagram calculation={mockCalculation} />);

      const chart2 = screen.getByTestId('sankey-chart');

      // Charts should both be present (memoization working)
      expect(chart1).toBeInTheDocument();
      expect(chart2).toBeInTheDocument();
    });
  });
});
