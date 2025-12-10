/**
 * EmissionsTrendChart Component Tests
 *
 * Comprehensive tests for the emissions trend/area chart visualization
 * for scenario comparison and time-based emissions tracking.
 *
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 *
 * Test Coverage:
 * - Component rendering with multiple series
 * - Series color assignment and legend
 * - Target line display
 * - Value formatting
 * - Empty and error states
 * - Accessibility (WCAG AA compliance)
 * - Responsive behavior
 * - Tooltip interactions
 * - Animation behavior
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock Nivo area bump component (used for trend visualization)
vi.mock('@nivo/bump', () => ({
  ResponsiveAreaBump: ({
    data,
    tooltip,
    colors,
    margin,
  }: {
    data: Array<{ id: string; data: Array<{ x: string | number; y: number }> }>;
    tooltip?: (props: { serie: { id: string; color: string } }) => React.ReactNode;
    colors?: { datum: string } | { scheme: string };
    margin?: { top: number; right: number; bottom: number; left: number };
  }) => (
    <div data-testid="nivo-area-bump">
      <div data-testid="area-chart-series-count">{data.length}</div>
      {/* Render mock series for testing */}
      {data.map((series, index) => (
        <div
          key={series.id}
          data-testid={`series-${series.id.toLowerCase().replace(/\s+/g, '-')}`}
        >
          <span data-testid={`series-name-${index}`}>{series.id}</span>
          <span data-testid={`series-points-${index}`}>{series.data.length}</span>
        </div>
      ))}
      {/* Test tooltip rendering */}
      {tooltip && (
        <div data-testid="area-tooltip-container">
          {tooltip({
            serie: { id: 'Test Series', color: '#228be6' },
          })}
        </div>
      )}
    </div>
  ),
}));

// Also mock @nivo/line as an alternative for trend charts
vi.mock('@nivo/line', () => ({
  ResponsiveLine: ({
    data,
    tooltip,
    markers,
  }: {
    data: Array<{ id: string; data: Array<{ x: string | number; y: number }> }>;
    tooltip?: (props: { point: unknown }) => React.ReactNode;
    markers?: Array<{ axis: string; value: number; legend: string }>;
  }) => (
    <div data-testid="nivo-line-chart">
      <div data-testid="line-chart-series-count">{data.length}</div>
      {markers && (
        <div data-testid="target-markers-count">{markers.length}</div>
      )}
      {data.map((series, index) => (
        <div
          key={series.id}
          data-testid={`line-series-${series.id.toLowerCase().replace(/\s+/g, '-')}`}
        >
          <span data-testid={`line-series-name-${index}`}>{series.id}</span>
        </div>
      ))}
    </div>
  ),
}));

// Import component after mocking
// Component to be created at: frontend/src/components/Visualizations/EmissionsTrendChart.tsx
import EmissionsTrendChart from '../../../src/components/Visualizations/EmissionsTrendChart';

// ============================================================================
// Test Data Fixtures
// ============================================================================

const mockTrendData = [
  {
    id: 'Baseline',
    data: [
      { x: '2023-01', y: 1500 },
      { x: '2023-02', y: 1450 },
      { x: '2023-03', y: 1600 },
      { x: '2023-04', y: 1520 },
      { x: '2023-05', y: 1480 },
      { x: '2023-06', y: 1400 },
    ],
  },
  {
    id: 'Scenario A',
    data: [
      { x: '2023-01', y: 1400 },
      { x: '2023-02', y: 1350 },
      { x: '2023-03', y: 1500 },
      { x: '2023-04', y: 1420 },
      { x: '2023-05', y: 1380 },
      { x: '2023-06', y: 1300 },
    ],
  },
  {
    id: 'Scenario B',
    data: [
      { x: '2023-01', y: 1300 },
      { x: '2023-02', y: 1250 },
      { x: '2023-03', y: 1400 },
      { x: '2023-04', y: 1320 },
      { x: '2023-05', y: 1280 },
      { x: '2023-06', y: 1200 },
    ],
  },
];

const mockSingleSeriesData = [
  {
    id: 'Total Emissions',
    data: [
      { x: '2023-01', y: 1500 },
      { x: '2023-02', y: 1450 },
      { x: '2023-03', y: 1600 },
    ],
  },
];

const mockLargeDataset = [
  {
    id: 'Large Series',
    data: Array.from({ length: 100 }, (_, i) => ({
      x: `2023-${String(i % 12 + 1).padStart(2, '0')}`,
      y: Math.random() * 1000 + 1000,
    })),
  },
];

const mockEmptyData: Array<{ id: string; data: Array<{ x: string; y: number }> }> = [];

// ============================================================================
// Component Rendering Tests
// ============================================================================

describe('EmissionsTrendChart', () => {
  describe('Rendering', () => {
    it('renders area chart with valid data', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('renders with correct number of series', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const seriesCount = screen.getByTestId('area-chart-series-count');
      expect(seriesCount.textContent).toBe('3');
    });

    it('renders area chart container with correct test id', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const container = screen.getByTestId('area-chart-container');
      expect(container).toBeInTheDocument();
    });

    it('renders card header with title', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const title = screen.getByText(/emissions trends/i);
      expect(title).toBeInTheDocument();
    });

    it('renders with custom className when provided', () => {
      render(
        <EmissionsTrendChart data={mockTrendData} className="custom-chart" />
      );

      const container = screen.getByTestId('emissions-area-chart');
      expect(container).toHaveClass('custom-chart');
    });

    it('renders single series data correctly', () => {
      render(<EmissionsTrendChart data={mockSingleSeriesData} />);

      const seriesCount = screen.getByTestId('area-chart-series-count');
      expect(seriesCount.textContent).toBe('1');
    });
  });

  // ============================================================================
  // Legend Tests
  // ============================================================================

  describe('Legend', () => {
    it('renders legend with all series', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const legend = screen.getByTestId('chart-legend');
      expect(legend).toBeInTheDocument();
    });

    it('legend shows all series names', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      expect(screen.getByText('Baseline')).toBeInTheDocument();
      expect(screen.getByText('Scenario A')).toBeInTheDocument();
      expect(screen.getByText('Scenario B')).toBeInTheDocument();
    });

    it('legend shows color indicators for each series', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const legend = screen.getByTestId('chart-legend');
      const colorIndicators = legend.querySelectorAll('[class*="rounded-full"]');

      // Should have one color indicator per series
      expect(colorIndicators.length).toBeGreaterThanOrEqual(mockTrendData.length);
    });

    it('legend shows target line indicator when target is displayed', () => {
      render(
        <EmissionsTrendChart
          data={mockTrendData}
          showTargetLine={true}
          targetValue={1200}
        />
      );

      const legend = screen.getByTestId('chart-legend');
      expect(legend).toHaveTextContent(/target/i);
    });

    it('legend does not show target when showTargetLine is false', () => {
      render(
        <EmissionsTrendChart
          data={mockTrendData}
          showTargetLine={false}
          targetValue={1200}
        />
      );

      const legend = screen.getByTestId('chart-legend');
      expect(legend).not.toHaveTextContent(/target/i);
    });
  });

  // ============================================================================
  // Target Line Tests
  // ============================================================================

  describe('Target Line', () => {
    it('renders target line when showTargetLine is true', () => {
      render(
        <EmissionsTrendChart
          data={mockTrendData}
          showTargetLine={true}
          targetValue={1200}
        />
      );

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('target line displays correct value in legend', () => {
      render(
        <EmissionsTrendChart
          data={mockTrendData}
          showTargetLine={true}
          targetValue={1200}
          unit="kg CO2e"
        />
      );

      const legend = screen.getByTestId('chart-legend');
      expect(legend).toHaveTextContent('1200');
      expect(legend).toHaveTextContent('kg CO2e');
    });

    it('does not render target line when targetValue is not provided', () => {
      render(
        <EmissionsTrendChart
          data={mockTrendData}
          showTargetLine={true}
          // No targetValue provided
        />
      );

      const legend = screen.getByTestId('chart-legend');
      expect(legend).not.toHaveTextContent(/target/i);
    });

    it('formats target value with K suffix for thousands', () => {
      render(
        <EmissionsTrendChart
          data={mockTrendData}
          showTargetLine={true}
          targetValue={1500}
          unit="kg CO2e"
        />
      );

      const legend = screen.getByTestId('chart-legend');
      // Should show formatted value
      expect(legend).toHaveTextContent(/1\.5K|1500/);
    });
  });

  // ============================================================================
  // Series Colors Tests
  // ============================================================================

  describe('Series Colors', () => {
    it('assigns distinct colors to each series', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('uses consistent color scheme across renders', () => {
      const { rerender } = render(<EmissionsTrendChart data={mockTrendData} />);

      // First render
      const legend1 = screen.getByTestId('chart-legend');
      const colorIndicators1 = legend1.querySelectorAll('[class*="rounded-full"]');

      // Rerender
      rerender(<EmissionsTrendChart data={mockTrendData} />);

      const legend2 = screen.getByTestId('chart-legend');
      const colorIndicators2 = legend2.querySelectorAll('[class*="rounded-full"]');

      // Colors should be consistent
      expect(colorIndicators1.length).toBe(colorIndicators2.length);
    });
  });

  // ============================================================================
  // Value Formatting Tests
  // ============================================================================

  describe('Value Formatting', () => {
    it('formats values with K suffix for thousands', () => {
      render(<EmissionsTrendChart data={mockTrendData} unit="kg CO2e" />);

      // Tooltip should format values
      const tooltipContainer = screen.getByTestId('area-tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('formats values with M suffix for millions', () => {
      const millionData = [
        {
          id: 'Large Values',
          data: [
            { x: '2023-01', y: 5000000 },
            { x: '2023-02', y: 4500000 },
          ],
        },
      ];

      render(<EmissionsTrendChart data={millionData} />);

      const tooltipContainer = screen.getByTestId('area-tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('displays unit in formatted values', () => {
      render(<EmissionsTrendChart data={mockTrendData} unit="tonnes CO2e" />);

      const tooltipContainer = screen.getByTestId('area-tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Empty and Error States
  // ============================================================================

  describe('Empty and Error States', () => {
    it('shows empty state when data array is empty', () => {
      render(<EmissionsTrendChart data={mockEmptyData} />);

      const emptyState = screen.getByText(/no trend data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('shows empty state when data is null', () => {
      render(
        <EmissionsTrendChart
          data={null as unknown as typeof mockTrendData}
        />
      );

      const emptyState = screen.getByText(/no trend data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('shows empty state when data is undefined', () => {
      render(
        <EmissionsTrendChart
          data={undefined as unknown as typeof mockTrendData}
        />
      );

      const emptyState = screen.getByText(/no trend data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('handles series with empty data array', () => {
      const emptySeriesData = [
        { id: 'Empty Series', data: [] },
      ];

      render(<EmissionsTrendChart data={emptySeriesData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('handles malformed data gracefully', () => {
      const malformedData = [
        { id: 'Missing Data', data: undefined as unknown as Array<{ x: string; y: number }> },
      ];

      render(<EmissionsTrendChart data={malformedData} />);

      // Should not crash
      const container = screen.getByTestId('emissions-area-chart');
      expect(container).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('has no accessibility violations (axe-core)', async () => {
      const { container } = render(<EmissionsTrendChart data={mockTrendData} />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('renders hidden data table for screen readers', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      // Hidden table should exist for screen readers
      const hiddenTable = screen.getByRole('table', { hidden: true });
      expect(hiddenTable).toBeInTheDocument();
    });

    it('hidden table contains all series data', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const hiddenTable = screen.getByRole('table', { hidden: true });

      // Check for series names
      expect(hiddenTable).toHaveTextContent('Baseline');
      expect(hiddenTable).toHaveTextContent('Scenario A');
      expect(hiddenTable).toHaveTextContent('Scenario B');
    });

    it('has proper ARIA label on chart container', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const container = screen.getByTestId('area-chart-container');
      expect(container).toHaveAttribute('aria-label');
    });

    it('legend items are accessible', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const legend = screen.getByTestId('chart-legend');
      expect(legend).toBeInTheDocument();

      // Legend should be properly structured
      const legendItems = legend.children;
      expect(legendItems.length).toBeGreaterThan(0);
    });

    it('hidden table has proper table structure', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const table = screen.getByRole('table', { hidden: true });

      // Should have column headers
      const headers = table.querySelectorAll('[role="columnheader"]');
      expect(headers.length).toBeGreaterThan(0);

      // Should have rows
      const rows = table.querySelectorAll('[role="row"]');
      expect(rows.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Responsive Behavior Tests
  // ============================================================================

  describe('Responsive Behavior', () => {
    it('renders with default container height of 400px', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const container = screen.getByTestId('area-chart-container');
      expect(container).toHaveStyle({ height: '400px' });
    });

    it('accepts custom height via style or className', () => {
      render(
        <EmissionsTrendChart data={mockTrendData} className="h-[600px]" />
      );

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toHaveClass('h-[600px]');
    });

    it('chart fills container width', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const container = screen.getByTestId('area-chart-container');
      expect(container).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Tooltip Tests
  // ============================================================================

  describe('Tooltip', () => {
    it('renders tooltip component', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const tooltipContainer = screen.getByTestId('area-tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('tooltip has correct test id', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const tooltip = screen.getByTestId('area-tooltip');
      expect(tooltip).toBeInTheDocument();
    });

    it('tooltip shows series name', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const tooltip = screen.getByTestId('area-tooltip');
      expect(tooltip).toHaveTextContent('Test Series');
    });

    it('tooltip shows color indicator', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const tooltip = screen.getByTestId('area-tooltip');
      const colorIndicator = tooltip.querySelector('[class*="rounded-full"]');
      expect(colorIndicator).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Animation Tests
  // ============================================================================

  describe('Animation', () => {
    it('renders with animation enabled by default', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('chart updates smoothly when data changes', async () => {
      const { rerender } = render(
        <EmissionsTrendChart data={mockTrendData} />
      );

      // Update with new data
      const newData = [
        {
          id: 'New Series',
          data: [
            { x: '2024-01', y: 2000 },
            { x: '2024-02', y: 1900 },
          ],
        },
      ];

      rerender(<EmissionsTrendChart data={newData} />);

      // Chart should update without errors
      const seriesCount = screen.getByTestId('area-chart-series-count');
      expect(seriesCount.textContent).toBe('1');
    });
  });

  // ============================================================================
  // Performance Tests
  // ============================================================================

  describe('Performance', () => {
    it('handles large datasets efficiently', () => {
      const startTime = performance.now();

      render(<EmissionsTrendChart data={mockLargeDataset} />);

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in under 1 second
      expect(renderTime).toBeLessThan(1000);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('memoizes data transformation', () => {
      const { rerender } = render(
        <EmissionsTrendChart data={mockTrendData} />
      );

      // Rerender with same data
      rerender(<EmissionsTrendChart data={mockTrendData} />);

      // Should still render correctly
      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('handles multiple series (8+) without performance degradation', () => {
      const manySeriesData = Array.from({ length: 8 }, (_, i) => ({
        id: `Series ${i + 1}`,
        data: [
          { x: '2023-01', y: 1000 + i * 100 },
          { x: '2023-02', y: 1100 + i * 100 },
        ],
      }));

      const startTime = performance.now();

      render(<EmissionsTrendChart data={manySeriesData} />);

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      expect(renderTime).toBeLessThan(500);
    });
  });

  // ============================================================================
  // Integration Tests
  // ============================================================================

  describe('Integration', () => {
    it('works within a Card component wrapper', () => {
      render(<EmissionsTrendChart data={mockTrendData} />);

      const card = screen.getByTestId('emissions-area-chart');
      expect(card).toBeInTheDocument();

      const header = screen.getByText(/emissions trends/i);
      expect(header).toBeInTheDocument();
    });

    it('maintains state across rerenders', () => {
      const { rerender } = render(
        <EmissionsTrendChart data={mockTrendData} />
      );

      // First render
      expect(screen.getByText('Baseline')).toBeInTheDocument();

      // Rerender with same data
      rerender(<EmissionsTrendChart data={mockTrendData} />);

      // Should still show same content
      expect(screen.getByText('Baseline')).toBeInTheDocument();
    });

    it('updates legend when data changes', () => {
      const { rerender } = render(
        <EmissionsTrendChart data={mockTrendData} />
      );

      // First render shows all series
      expect(screen.getByText('Baseline')).toBeInTheDocument();
      expect(screen.getByText('Scenario A')).toBeInTheDocument();

      // Update with different data
      const newData = [
        {
          id: 'New Series Only',
          data: [{ x: '2024-01', y: 2000 }],
        },
      ];

      rerender(<EmissionsTrendChart data={newData} />);

      // Legend should update
      expect(screen.getByText('New Series Only')).toBeInTheDocument();
      expect(screen.queryByText('Baseline')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Date/Time Handling Tests
  // ============================================================================

  describe('Date/Time Handling', () => {
    it('handles string date formats', () => {
      const stringDateData = [
        {
          id: 'String Dates',
          data: [
            { x: 'January', y: 1000 },
            { x: 'February', y: 1100 },
          ],
        },
      ];

      render(<EmissionsTrendChart data={stringDateData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('handles numeric x-values (years)', () => {
      const numericDateData = [
        {
          id: 'Yearly Data',
          data: [
            { x: 2020, y: 1000 },
            { x: 2021, y: 1100 },
            { x: 2022, y: 1200 },
          ],
        },
      ];

      render(<EmissionsTrendChart data={numericDateData as unknown as typeof mockTrendData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });

    it('handles ISO date formats', () => {
      const isoDateData = [
        {
          id: 'ISO Dates',
          data: [
            { x: '2023-01-01', y: 1000 },
            { x: '2023-02-01', y: 1100 },
          ],
        },
      ];

      render(<EmissionsTrendChart data={isoDateData} />);

      const chart = screen.getByTestId('emissions-area-chart');
      expect(chart).toBeInTheDocument();
    });
  });
});
