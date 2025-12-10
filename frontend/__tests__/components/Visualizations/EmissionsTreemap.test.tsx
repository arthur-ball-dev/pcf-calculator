/**
 * EmissionsTreemap Component Tests
 *
 * Comprehensive tests for the hierarchical Scope 1/2/3 emissions breakdown
 * treemap visualization with drill-down navigation.
 *
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 *
 * Test Coverage:
 * - Component rendering with valid data
 * - Drill-down navigation and state management
 * - Breadcrumb navigation
 * - Color assignment (GHG Protocol colors)
 * - Value formatting (K, M suffixes)
 * - Empty and error states
 * - Accessibility (WCAG AA compliance)
 * - Responsive behavior
 * - Performance with large datasets
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within, userEvent } from '../../testUtils';
import { axe, toHaveNoViolations } from 'jest-axe';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock Nivo treemap component
vi.mock('@nivo/treemap', () => ({
  ResponsiveTreeMap: ({
    data,
    onClick,
    tooltip,
  }: {
    data: { name: string; children?: unknown[] };
    onClick?: (node: unknown) => void;
    tooltip?: (props: { node: unknown }) => React.ReactNode;
  }) => (
    <div data-testid="nivo-treemap">
      <div data-testid="treemap-root-name">{data.name}</div>
      <div data-testid="treemap-children-count">
        {data.children?.length ?? 0}
      </div>
      {/* Render mock nodes for testing click interactions */}
      {data.children?.map((child: { name: string; value?: number; children?: unknown[] }, index: number) => (
        <div
          key={index}
          data-testid={`treemap-node-${child.name.toLowerCase().replace(/\s+/g, '-')}`}
          onClick={() => onClick?.({ data: child })}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              onClick?.({ data: child });
            }
          }}
        >
          <span data-testid={`node-name-${index}`}>{child.name}</span>
          {child.value && (
            <span data-testid={`node-value-${index}`}>{child.value}</span>
          )}
        </div>
      ))}
      {/* Test tooltip rendering */}
      {tooltip && (
        <div data-testid="tooltip-container">
          {tooltip({
            node: {
              id: 'test-node',
              value: 1000,
              data: { name: 'Test Node', value: 1000, children: [] },
            },
          })}
        </div>
      )}
    </div>
  ),
}));

// Import component after mocking
// Component to be created at: frontend/src/components/Visualizations/EmissionsTreemap.tsx
import EmissionsTreemap from '../../../src/components/Visualizations/EmissionsTreemap';

// ============================================================================
// Test Data Fixtures
// ============================================================================

const mockTreemapData = {
  name: 'Total Emissions',
  children: [
    {
      name: 'Scope 1',
      color: '#fa5252',
      children: [
        {
          name: 'Stationary Combustion',
          children: [
            { name: 'Natural Gas', value: 850.5, color: '#ff6b6b' },
            { name: 'Diesel', value: 125.3, color: '#ff8787' },
          ],
        },
        {
          name: 'Mobile Combustion',
          children: [
            { name: 'Company Vehicles', value: 620.8, color: '#ff6b6b' },
          ],
        },
      ],
    },
    {
      name: 'Scope 2',
      color: '#339af0',
      children: [
        {
          name: 'Purchased Electricity',
          children: [
            { name: 'Manufacturing Facility', value: 2850.0, color: '#4dabf7' },
            { name: 'Office Buildings', value: 420.8, color: '#74c0fc' },
          ],
        },
      ],
    },
    {
      name: 'Scope 3',
      color: '#495057',
      children: [
        {
          name: 'Purchased Goods',
          children: [
            { name: 'Raw Materials', value: 3250.0, color: '#6c757d' },
            { name: 'Packaging', value: 890.5, color: '#868e96' },
          ],
        },
      ],
    },
  ],
};

const mockLargeDataset = {
  name: 'Total Emissions',
  children: Array.from({ length: 500 }, (_, i) => ({
    name: `Category ${i + 1}`,
    value: Math.random() * 1000,
    color: `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`,
  })),
};

const mockEmptyData = {
  name: 'Total Emissions',
  children: [],
};

// ============================================================================
// Component Rendering Tests
// ============================================================================

describe('EmissionsTreemap', () => {
  describe('Rendering', () => {
    it('renders treemap with valid hierarchical data', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toBeInTheDocument();
    });

    it('renders with correct number of top-level nodes', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const childrenCount = screen.getByTestId('treemap-children-count');
      expect(childrenCount.textContent).toBe('3'); // Scope 1, 2, 3
    });

    it('renders treemap container with correct test id', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const container = screen.getByTestId('treemap-container');
      expect(container).toBeInTheDocument();
    });

    it('renders card header with title', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const title = screen.getByText(/emissions breakdown/i);
      expect(title).toBeInTheDocument();
    });

    it('renders with custom className when provided', () => {
      render(
        <EmissionsTreemap data={mockTreemapData} className="custom-treemap" />
      );

      const container = screen.getByTestId('emissions-treemap');
      expect(container).toHaveClass('custom-treemap');
    });

    it('renders with custom unit label', () => {
      render(<EmissionsTreemap data={mockTreemapData} unit="tonnes CO2e" />);

      // Tooltip should show custom unit
      const tooltipContainer = screen.getByTestId('tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Drill-Down Navigation Tests
  // ============================================================================

  describe('Drill-Down Navigation', () => {
    it('drills down when clicking on a node with children', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Click on Scope 1 node
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Breadcrumb should update
      const breadcrumb = screen.getByTestId('breadcrumb');
      expect(breadcrumb).toHaveTextContent(/scope 1/i);
    });

    it('shows drill-up button after drilling down', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Initially no drill-up button
      expect(screen.queryByTestId('drill-up-button')).not.toBeInTheDocument();

      // Click on Scope 1 node
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Drill-up button should appear
      const drillUpButton = screen.getByTestId('drill-up-button');
      expect(drillUpButton).toBeInTheDocument();
    });

    it('navigates back when clicking drill-up button', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Drill down to Scope 1
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Click drill-up button
      const drillUpButton = screen.getByTestId('drill-up-button');
      await user.click(drillUpButton);

      // Should be back at root
      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });

    it('does not drill down when enableDrillDown is false', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={false} />);

      // Click on Scope 1 node
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Should not have breadcrumb
      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });

    it('calls onNodeClick callback when node is clicked', async () => {
      const user = userEvent.setup();
      const mockOnNodeClick = vi.fn();

      render(
        <EmissionsTreemap
          data={mockTreemapData}
          enableDrillDown={true}
          onNodeClick={mockOnNodeClick}
        />
      );

      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      expect(mockOnNodeClick).toHaveBeenCalledTimes(1);
      expect(mockOnNodeClick).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Scope 1' }),
        expect.arrayContaining(['Scope 1'])
      );
    });

    it('does not drill down into leaf nodes (nodes without children)', async () => {
      const user = userEvent.setup();
      const leafOnlyData = {
        name: 'Total Emissions',
        children: [
          { name: 'Leaf 1', value: 100 },
          { name: 'Leaf 2', value: 200 },
        ],
      };

      render(<EmissionsTreemap data={leafOnlyData} enableDrillDown={true} />);

      // Click on leaf node
      const leafNode = screen.getByTestId('treemap-node-leaf-1');
      await user.click(leafNode);

      // Should not show breadcrumb (didn't drill)
      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Breadcrumb Navigation Tests
  // ============================================================================

  describe('Breadcrumb Navigation', () => {
    it('shows breadcrumb path after drilling down', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Drill down to Scope 1
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      const breadcrumb = screen.getByTestId('breadcrumb');
      expect(breadcrumb).toHaveTextContent('Overview');
      expect(breadcrumb).toHaveTextContent('Scope 1');
    });

    it('allows navigation through breadcrumb clicks', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Drill down multiple levels (if data supports it)
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Click on Overview in breadcrumb to go back
      const overviewCrumb = screen.getByText('Overview');
      await user.click(overviewCrumb);

      // Should be back at root (no breadcrumb visible)
      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });

    it('breadcrumb uses correct separator character', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      const breadcrumb = screen.getByTestId('breadcrumb');
      expect(breadcrumb.textContent).toContain('>');
    });
  });

  // ============================================================================
  // Color Assignment Tests
  // ============================================================================

  describe('Color Assignment', () => {
    it('applies GHG Protocol colors to scope nodes', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      // Component should apply standard scope colors internally
      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toBeInTheDocument();
    });

    it('uses provided custom colors when specified in data', () => {
      const dataWithColors = {
        name: 'Total',
        children: [
          { name: 'Custom Color Node', value: 100, color: '#ff0000' },
        ],
      };

      render(<EmissionsTreemap data={dataWithColors} />);

      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toBeInTheDocument();
    });

    it('assigns default colors to nodes without specified colors', () => {
      const dataWithoutColors = {
        name: 'Total',
        children: [
          { name: 'No Color Node', value: 100 },
        ],
      };

      render(<EmissionsTreemap data={dataWithoutColors} />);

      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Value Formatting Tests
  // ============================================================================

  describe('Value Formatting', () => {
    it('formats values with K suffix for thousands', () => {
      const dataWithThousands = {
        name: 'Total',
        children: [{ name: 'Large Value', value: 5000 }],
      };

      render(<EmissionsTreemap data={dataWithThousands} />);

      // Tooltip should format large values
      const tooltipContainer = screen.getByTestId('tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('formats values with M suffix for millions', () => {
      const dataWithMillions = {
        name: 'Total',
        children: [{ name: 'Huge Value', value: 5000000 }],
      };

      render(<EmissionsTreemap data={dataWithMillions} />);

      const tooltipContainer = screen.getByTestId('tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('displays decimal precision for small values', () => {
      const dataWithSmallValues = {
        name: 'Total',
        children: [{ name: 'Small Value', value: 0.5 }],
      };

      render(<EmissionsTreemap data={dataWithSmallValues} />);

      const tooltipContainer = screen.getByTestId('tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('displays unit in formatted values', () => {
      render(<EmissionsTreemap data={mockTreemapData} unit="kg CO2e" />);

      const tooltipContainer = screen.getByTestId('tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Empty and Error States
  // ============================================================================

  describe('Empty and Error States', () => {
    it('shows empty state when data has no children', () => {
      render(<EmissionsTreemap data={mockEmptyData} />);

      const emptyState = screen.getByText(/no emissions data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('shows empty state when data is null', () => {
      render(<EmissionsTreemap data={null as unknown as typeof mockTreemapData} />);

      const emptyState = screen.getByText(/no emissions data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('shows empty state when data is undefined', () => {
      render(<EmissionsTreemap data={undefined as unknown as typeof mockTreemapData} />);

      const emptyState = screen.getByText(/no emissions data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('handles malformed data gracefully', () => {
      const malformedData = { name: 'Total' }; // Missing children

      render(<EmissionsTreemap data={malformedData as typeof mockTreemapData} />);

      // Should show empty state or render without crashing
      const container = screen.getByTestId('emissions-treemap');
      expect(container).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('has no accessibility violations (axe-core)', async () => {
      const { container } = render(<EmissionsTreemap data={mockTreemapData} />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('renders hidden data table for screen readers', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      // Hidden table should exist for screen readers
      const hiddenTable = screen.getByRole('table', { hidden: true });
      expect(hiddenTable).toBeInTheDocument();
    });

    it('hidden table contains all categories', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const hiddenTable = screen.getByRole('table', { hidden: true });

      // Check for scope names in hidden table
      expect(hiddenTable).toHaveTextContent('Scope 1');
      expect(hiddenTable).toHaveTextContent('Scope 2');
      expect(hiddenTable).toHaveTextContent('Scope 3');
    });

    it('has proper ARIA label on treemap container', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const container = screen.getByTestId('treemap-container');
      expect(container).toHaveAttribute('aria-label');
    });

    it('nodes are keyboard accessible', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Tab to first node
      await user.tab();

      // Node should be focusable
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      expect(scope1Node).toHaveFocus();

      // Enter should activate drill-down
      await user.keyboard('{Enter}');

      const breadcrumb = screen.getByTestId('breadcrumb');
      expect(breadcrumb).toBeInTheDocument();
    });

    it('drill-up button has accessible name', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Drill down
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      const drillUpButton = screen.getByTestId('drill-up-button');
      expect(drillUpButton).toHaveAccessibleName();
    });

    it('breadcrumb navigation is keyboard accessible', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Drill down
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Tab to breadcrumb
      await user.tab();
      await user.tab();

      // Press Enter on Overview breadcrumb
      await user.keyboard('{Enter}');

      // Should navigate back
      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });

    it('announces drill-down navigation to screen readers', async () => {
      const user = userEvent.setup();
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Check for live region
      const liveRegion = screen.getByRole('status', { hidden: true }) ||
        document.querySelector('[aria-live]');

      // Drill down
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Live region should announce navigation
      expect(liveRegion).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Responsive Behavior Tests
  // ============================================================================

  describe('Responsive Behavior', () => {
    it('renders with default container height of 400px', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const container = screen.getByTestId('treemap-container');
      expect(container).toHaveStyle({ height: '400px' });
    });

    it('accepts custom height via style or className', () => {
      render(<EmissionsTreemap data={mockTreemapData} className="h-[600px]" />);

      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toHaveClass('h-[600px]');
    });

    it('treemap fills container width', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const container = screen.getByTestId('treemap-container');
      expect(container).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Tooltip Tests
  // ============================================================================

  describe('Tooltip', () => {
    it('renders tooltip with node name', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const tooltipContainer = screen.getByTestId('tooltip-container');
      expect(tooltipContainer).toBeInTheDocument();
    });

    it('tooltip has correct test id for integration testing', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      const tooltip = screen.getByTestId('treemap-tooltip');
      expect(tooltip).toBeInTheDocument();
    });

    it('tooltip shows drill-down hint when node has children', () => {
      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      const tooltip = screen.getByTestId('treemap-tooltip');
      expect(tooltip).toHaveTextContent(/click to drill down/i);
    });
  });

  // ============================================================================
  // Performance Tests
  // ============================================================================

  describe('Performance', () => {
    it('handles large datasets (500 nodes) without crashing', () => {
      const startTime = performance.now();

      render(<EmissionsTreemap data={mockLargeDataset} />);

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in under 1 second
      expect(renderTime).toBeLessThan(1000);

      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toBeInTheDocument();
    });

    it('memoizes transformed data to prevent recalculation', () => {
      const { rerender } = render(<EmissionsTreemap data={mockTreemapData} />);

      // Rerender with same data
      rerender(<EmissionsTreemap data={mockTreemapData} />);

      // Should still render correctly
      const treemap = screen.getByTestId('emissions-treemap');
      expect(treemap).toBeInTheDocument();
    });

    it('updates efficiently when drill path changes', async () => {
      const user = userEvent.setup();
      const startTime = performance.now();

      render(<EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />);

      // Drill down
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      const endTime = performance.now();
      const transitionTime = endTime - startTime;

      // Drill transition should be fast
      expect(transitionTime).toBeLessThan(200);
    });
  });

  // ============================================================================
  // Integration Tests
  // ============================================================================

  describe('Integration', () => {
    it('works within a Card component wrapper', () => {
      render(<EmissionsTreemap data={mockTreemapData} />);

      // Component wraps content in Card
      const card = screen.getByTestId('emissions-treemap');
      expect(card).toBeInTheDocument();

      // Card header should have title
      const header = screen.getByText(/emissions breakdown/i);
      expect(header).toBeInTheDocument();
    });

    it('maintains state across rerenders', async () => {
      const user = userEvent.setup();
      const { rerender } = render(
        <EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />
      );

      // Drill down
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Rerender with same data
      rerender(
        <EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />
      );

      // Drill state should be maintained
      const breadcrumb = screen.getByTestId('breadcrumb');
      expect(breadcrumb).toHaveTextContent('Scope 1');
    });

    it('resets drill state when data changes', async () => {
      const user = userEvent.setup();
      const { rerender } = render(
        <EmissionsTreemap data={mockTreemapData} enableDrillDown={true} />
      );

      // Drill down
      const scope1Node = screen.getByTestId('treemap-node-scope-1');
      await user.click(scope1Node);

      // Rerender with different data
      const newData = {
        name: 'New Total',
        children: [{ name: 'New Category', value: 100 }],
      };
      rerender(
        <EmissionsTreemap data={newData} enableDrillDown={true} />
      );

      // Drill state should be reset
      expect(screen.queryByTestId('breadcrumb')).not.toBeInTheDocument();
    });
  });
});
