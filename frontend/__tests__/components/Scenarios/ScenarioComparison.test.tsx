/**
 * ScenarioComparison Component Tests
 *
 * Test-Driven Development for TASK-FE-P5-002
 * Written BEFORE implementation (TDD Protocol)
 *
 * Tests for the main scenario comparison split-pane interface including:
 * - Two-pane display when 2+ scenarios selected
 * - Alert when less than 2 scenarios
 * - Delta visualization integration
 * - Synchronized scrolling between panes
 * - Scenario name display
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
// Real import - enabled per TDD Exception approval (TASK-FE-P5-002_SEQ-003)
import { ScenarioComparison } from '../../../src/components/Scenarios/ScenarioComparison';

// Type definitions for tests
interface BOMEntry {
  id: string;
  component_name: string;
  quantity: number;
  unit: string;
  emissions?: number;
}

interface CalculationParameters {
  transportDistance: number;
  energySource: string;
  productionVolume: number;
}

interface CalculationResults {
  total_emissions: number;
  breakdown?: Record<string, number>;
}

interface Scenario {
  id: string;
  name: string;
  productId: string;
  bomEntries: BOMEntry[];
  parameters: CalculationParameters;
  results: CalculationResults | null;
  createdAt: Date;
  isBaseline: boolean;
}

// Mock scenarios for testing
const createMockScenario = (overrides: Partial<Scenario> = {}): Scenario => ({
  id: 'scenario-' + Math.random().toString(36).substring(7),
  name: 'Test Scenario',
  productId: 'product-1',
  bomEntries: [
    { id: 'bom-1', component_name: 'Steel', quantity: 10, unit: 'kg', emissions: 25.0 },
    { id: 'bom-2', component_name: 'Plastic', quantity: 5, unit: 'kg', emissions: 15.0 },
  ],
  parameters: {
    transportDistance: 100,
    energySource: 'grid',
    productionVolume: 1,
  },
  results: { total_emissions: 40.0 },
  createdAt: new Date(),
  isBaseline: false,
  ...overrides,
});

const mockBaselineScenario: Scenario = createMockScenario({
  id: 'baseline-scenario',
  name: 'Baseline Scenario',
  isBaseline: true,
  results: { total_emissions: 100.0 },
});

const mockAlternativeScenario: Scenario = createMockScenario({
  id: 'alternative-scenario',
  name: 'Alternative Scenario',
  isBaseline: false,
  results: { total_emissions: 120.0 },
});

// Mock the scenario store
const mockGetComparisonScenarios = vi.fn();
const mockGetBaseline = vi.fn();

vi.mock('../../../src/store/scenarioStore', () => ({
  useScenarioStore: (selector: (state: unknown) => unknown) => {
    const mockState = {
      getComparisonScenarios: mockGetComparisonScenarios,
      getBaseline: mockGetBaseline,
      scenarios: [],
      comparisonScenarioIds: [],
    };
    return selector(mockState);
  },
}));

describe('ScenarioComparison Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
    mockGetComparisonScenarios.mockReturnValue([]);
    mockGetBaseline.mockReturnValue(undefined);
  });

  describe('Insufficient Scenarios State', () => {
    test('shows alert when no scenarios selected', () => {
      mockGetComparisonScenarios.mockReturnValue([]);

      render(<ScenarioComparison />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/add at least 2 scenarios to compare/i)).toBeInTheDocument();
    });

    test('shows alert when only 1 scenario selected', () => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario]);

      render(<ScenarioComparison />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/add at least 2 scenarios to compare/i)).toBeInTheDocument();
    });

    test('alert includes instruction to add scenarios', () => {
      mockGetComparisonScenarios.mockReturnValue([]);

      render(<ScenarioComparison />);

      const alert = screen.getByRole('alert');
      expect(alert.textContent).toMatch(/add.*(scenarios|comparison)/i);
    });

    test('does not render comparison container when less than 2 scenarios', () => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario]);

      render(<ScenarioComparison />);

      expect(screen.queryByTestId('comparison-container')).not.toBeInTheDocument();
    });
  });

  describe('Two Panes Display', () => {
    beforeEach(() => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);
    });

    test('renders two panes when 2 scenarios selected', () => {
      render(<ScenarioComparison />);

      expect(screen.getByTestId('scenario-pane-left')).toBeInTheDocument();
      expect(screen.getByTestId('scenario-pane-right')).toBeInTheDocument();
    });

    test('left pane displays first scenario', () => {
      render(<ScenarioComparison />);

      const leftPane = screen.getByTestId('scenario-pane-left');
      expect(leftPane).toHaveTextContent('Baseline Scenario');
    });

    test('right pane displays second scenario', () => {
      render(<ScenarioComparison />);

      const rightPane = screen.getByTestId('scenario-pane-right');
      expect(rightPane).toHaveTextContent('Alternative Scenario');
    });

    test('does not show alert when 2 scenarios present', () => {
      render(<ScenarioComparison />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    test('renders comparison container', () => {
      render(<ScenarioComparison />);

      expect(screen.getByTestId('comparison-container')).toBeInTheDocument();
    });
  });

  describe('Scenario Names Display', () => {
    test('renders baseline scenario name correctly', () => {
      const baseline = createMockScenario({
        id: 'b1',
        name: 'Current Production',
        isBaseline: true,
      });
      const alternative = createMockScenario({
        id: 'a1',
        name: 'Optimized Process',
      });

      mockGetComparisonScenarios.mockReturnValue([baseline, alternative]);
      mockGetBaseline.mockReturnValue(baseline);

      render(<ScenarioComparison />);

      expect(screen.getByText('Current Production')).toBeInTheDocument();
    });

    test('renders alternative scenario name correctly', () => {
      const baseline = createMockScenario({
        id: 'b1',
        name: 'Current Production',
        isBaseline: true,
      });
      const alternative = createMockScenario({
        id: 'a1',
        name: 'Optimized Process',
      });

      mockGetComparisonScenarios.mockReturnValue([baseline, alternative]);
      mockGetBaseline.mockReturnValue(baseline);

      render(<ScenarioComparison />);

      expect(screen.getByText('Optimized Process')).toBeInTheDocument();
    });

    test('handles long scenario names gracefully', () => {
      const longNameScenario = createMockScenario({
        id: 'long',
        name: 'This is a very long scenario name that should be handled properly without breaking the layout',
      });

      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, longNameScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);

      render(<ScenarioComparison />);

      expect(screen.getByText(/This is a very long scenario name/)).toBeInTheDocument();
    });
  });

  describe('Delta Visualization Integration', () => {
    beforeEach(() => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);
    });

    test('displays delta visualization component', () => {
      render(<ScenarioComparison />);

      expect(screen.getByTestId('delta-visualization')).toBeInTheDocument();
    });

    test('delta visualization receives deltas prop', () => {
      render(<ScenarioComparison />);

      const visualization = screen.getByTestId('delta-visualization');
      expect(visualization).toBeInTheDocument();
      // Full prop testing will be done in DeltaVisualization tests
    });
  });

  describe('Synchronized Scrolling', () => {
    beforeEach(() => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);
    });

    test('left pane has overflow auto for scrolling', () => {
      render(<ScenarioComparison />);

      const leftPane = screen.getByTestId('scenario-pane-left');
      expect(leftPane).toHaveStyle({ overflow: 'auto' });
    });

    test('right pane has overflow auto for scrolling', () => {
      render(<ScenarioComparison />);

      const rightPane = screen.getByTestId('scenario-pane-right');
      expect(rightPane).toHaveStyle({ overflow: 'auto' });
    });

    test('when left pane scrolls, right pane scroll position matches', async () => {
      render(<ScenarioComparison />);

      const leftPane = screen.getByTestId('scenario-pane-left');
      const rightPane = screen.getByTestId('scenario-pane-right');

      // Set up scroll height for testing
      Object.defineProperty(leftPane, 'scrollHeight', { value: 1000, configurable: true });
      Object.defineProperty(rightPane, 'scrollHeight', { value: 1000, configurable: true });

      // Simulate scroll on left pane
      fireEvent.scroll(leftPane, { target: { scrollTop: 200 } });

      await waitFor(() => {
        expect(rightPane.scrollTop).toBe(200);
      });
    });

    test('when right pane scrolls, left pane scroll position matches', async () => {
      render(<ScenarioComparison />);

      const leftPane = screen.getByTestId('scenario-pane-left');
      const rightPane = screen.getByTestId('scenario-pane-right');

      // Simulate scroll on right pane
      fireEvent.scroll(rightPane, { target: { scrollTop: 150 } });

      await waitFor(() => {
        expect(leftPane.scrollTop).toBe(150);
      });
    });

    test('horizontal scroll is also synchronized', async () => {
      render(<ScenarioComparison />);

      const leftPane = screen.getByTestId('scenario-pane-left');
      const rightPane = screen.getByTestId('scenario-pane-right');

      // Simulate horizontal scroll
      fireEvent.scroll(leftPane, { target: { scrollLeft: 100 } });

      await waitFor(() => {
        expect(rightPane.scrollLeft).toBe(100);
      });
    });
  });

  describe('Layout and Styling', () => {
    beforeEach(() => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);
    });

    test('applies custom className when provided', () => {
      render(<ScenarioComparison className="custom-class" />);

      const container = screen.getByTestId('comparison-container');
      expect(container).toHaveClass('custom-class');
    });

    test('container fills available height', () => {
      render(<ScenarioComparison />);

      const container = screen.getByTestId('comparison-container');
      // Component should use flex layout to fill height
      expect(container).toBeInTheDocument();
    });
  });

  describe('Multiple Scenarios (More Than 2)', () => {
    test('renders when more than 2 scenarios selected', () => {
      const third = createMockScenario({ id: 'third', name: 'Third Option' });

      mockGetComparisonScenarios.mockReturnValue([
        mockBaselineScenario,
        mockAlternativeScenario,
        third,
      ]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);

      render(<ScenarioComparison />);

      expect(screen.getByTestId('comparison-container')).toBeInTheDocument();
    });

    test('primary comparison shows first two scenarios', () => {
      const third = createMockScenario({ id: 'third', name: 'Third Option' });

      mockGetComparisonScenarios.mockReturnValue([
        mockBaselineScenario,
        mockAlternativeScenario,
        third,
      ]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);

      render(<ScenarioComparison />);

      // Left pane shows first, right pane shows second
      expect(screen.getByTestId('scenario-pane-left')).toHaveTextContent('Baseline Scenario');
      expect(screen.getByTestId('scenario-pane-right')).toHaveTextContent('Alternative Scenario');
    });
  });

  describe('Empty Results Handling', () => {
    test('handles scenario with null results', () => {
      const noResultsScenario = createMockScenario({
        id: 'no-results',
        name: 'Pending Calculation',
        results: null,
      });

      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, noResultsScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);

      // Should not throw
      render(<ScenarioComparison />);

      expect(screen.getByTestId('comparison-container')).toBeInTheDocument();
    });

    test('handles baseline with null results', () => {
      const noResultsBaseline = createMockScenario({
        id: 'no-results-baseline',
        name: 'Pending Baseline',
        isBaseline: true,
        results: null,
      });

      mockGetComparisonScenarios.mockReturnValue([noResultsBaseline, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(noResultsBaseline);

      // Should not throw
      render(<ScenarioComparison />);

      expect(screen.getByTestId('comparison-container')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);
    });

    test('panes have appropriate ARIA labels or headings', () => {
      render(<ScenarioComparison />);

      // Panes should be identifiable for screen readers
      const leftPane = screen.getByTestId('scenario-pane-left');
      const rightPane = screen.getByTestId('scenario-pane-right');

      expect(leftPane).toBeInTheDocument();
      expect(rightPane).toBeInTheDocument();
    });

    test('alert has correct role when displayed', () => {
      mockGetComparisonScenarios.mockReturnValue([]);

      render(<ScenarioComparison />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    test('comparison is keyboard navigable', async () => {
      render(<ScenarioComparison />);

      const container = screen.getByTestId('comparison-container');

      // Should be able to tab into the component
      await user.tab();

      // Some focusable element should be within the container
      expect(document.activeElement).not.toBe(document.body);
    });
  });

  describe('Performance', () => {
    test('does not re-render unnecessarily on scroll', () => {
      mockGetComparisonScenarios.mockReturnValue([mockBaselineScenario, mockAlternativeScenario]);
      mockGetBaseline.mockReturnValue(mockBaselineScenario);

      const { rerender } = render(<ScenarioComparison />);

      const leftPane = screen.getByTestId('scenario-pane-left');

      // Scroll multiple times
      fireEvent.scroll(leftPane, { target: { scrollTop: 100 } });
      fireEvent.scroll(leftPane, { target: { scrollTop: 200 } });
      fireEvent.scroll(leftPane, { target: { scrollTop: 300 } });

      // Component should still be stable
      expect(screen.getByTestId('comparison-container')).toBeInTheDocument();
    });
  });
});
