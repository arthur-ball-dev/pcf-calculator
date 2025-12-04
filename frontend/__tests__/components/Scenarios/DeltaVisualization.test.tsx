/**
 * DeltaVisualization Component Tests
 *
 * Test-Driven Development for TASK-FE-P5-002
 * Written BEFORE implementation (TDD Protocol)
 *
 * Tests for delta bar chart visualization including:
 * - Rendering bars for each scenario
 * - Bar widths proportional to emissions
 * - Correct colors based on direction (increase/decrease/same)
 * - Labels and values display
 */

import { describe, test, expect, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
// Real import - enabled per TDD Exception approval (TASK-FE-P5-002_SEQ-003)
import { DeltaVisualization, type DeltaData } from '../../../src/components/Scenarios/DeltaVisualization';

describe('DeltaVisualization Component', () => {
  // Helper to create delta data
  const createDelta = (overrides: Partial<DeltaData> = {}): DeltaData => ({
    scenarioId: 'scenario-' + Math.random().toString(36).substring(7),
    scenarioName: 'Test Scenario',
    emissions: 100,
    absoluteDelta: 0,
    percentageDelta: 0,
    direction: 'same',
    ...overrides,
  });

  describe('Rendering Bars', () => {
    test('renders a bar for each scenario', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'a', scenarioName: 'Scenario A', emissions: 100 }),
        createDelta({ scenarioId: 'b', scenarioName: 'Scenario B', emissions: 120 }),
        createDelta({ scenarioId: 'c', scenarioName: 'Scenario C', emissions: 80 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('bar-row-a')).toBeInTheDocument();
      expect(screen.getByTestId('bar-row-b')).toBeInTheDocument();
      expect(screen.getByTestId('bar-row-c')).toBeInTheDocument();
    });

    test('renders correct number of bars', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: '1' }),
        createDelta({ scenarioId: '2' }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const container = screen.getByTestId('bars-container');
      const bars = container.querySelectorAll('[data-testid^="bar-row-"]');
      expect(bars).toHaveLength(2);
    });

    test('renders empty state when no deltas provided', () => {
      render(<DeltaVisualization deltas={[]} />);

      const container = screen.getByTestId('bars-container');
      expect(container.children).toHaveLength(0);
    });

    test('renders visualization container with testid', () => {
      render(<DeltaVisualization deltas={[createDelta()]} />);

      expect(screen.getByTestId('delta-visualization')).toBeInTheDocument();
    });

    test('renders heading for the visualization', () => {
      render(<DeltaVisualization deltas={[createDelta()]} />);

      expect(screen.getByText(/emissions comparison/i)).toBeInTheDocument();
    });
  });

  describe('Bar Width Proportions', () => {
    test('bar widths are proportional to emissions values', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'max', emissions: 200 }),
        createDelta({ scenarioId: 'half', emissions: 100 }),
        createDelta({ scenarioId: 'quarter', emissions: 50 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const maxBar = screen.getByTestId('bar-fill-max');
      const halfBar = screen.getByTestId('bar-fill-half');
      const quarterBar = screen.getByTestId('bar-fill-quarter');

      // Max emissions should be 100% width
      expect(maxBar).toHaveStyle({ width: '100%' });
      // 100/200 = 50%
      expect(halfBar).toHaveStyle({ width: '50%' });
      // 50/200 = 25%
      expect(quarterBar).toHaveStyle({ width: '25%' });
    });

    test('largest bar fills 100% of track', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'big', emissions: 500 }),
        createDelta({ scenarioId: 'small', emissions: 100 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const bigBar = screen.getByTestId('bar-fill-big');
      expect(bigBar).toHaveStyle({ width: '100%' });
    });

    test('handles equal emissions (all bars same width)', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'a', emissions: 100 }),
        createDelta({ scenarioId: 'b', emissions: 100 }),
        createDelta({ scenarioId: 'c', emissions: 100 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const barA = screen.getByTestId('bar-fill-a');
      const barB = screen.getByTestId('bar-fill-b');
      const barC = screen.getByTestId('bar-fill-c');

      expect(barA).toHaveStyle({ width: '100%' });
      expect(barB).toHaveStyle({ width: '100%' });
      expect(barC).toHaveStyle({ width: '100%' });
    });

    test('handles zero emissions gracefully', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'zero', emissions: 0 }),
        createDelta({ scenarioId: 'positive', emissions: 100 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const zeroBar = screen.getByTestId('bar-fill-zero');
      expect(zeroBar).toHaveStyle({ width: '0%' });
    });

    test('handles very small emissions values', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'tiny', emissions: 0.1 }),
        createDelta({ scenarioId: 'normal', emissions: 100 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const tinyBar = screen.getByTestId('bar-fill-tiny');
      // 0.1/100 = 0.1%
      expect(tinyBar).toHaveStyle({ width: '0.1%' });
    });

    test('handles single scenario (bar fills 100%)', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'only', emissions: 50 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const onlyBar = screen.getByTestId('bar-fill-only');
      expect(onlyBar).toHaveStyle({ width: '100%' });
    });
  });

  describe('Colors Based on Direction', () => {
    test('increase direction shows red color', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'inc', direction: 'increase', emissions: 120 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-inc');
      expect(bar).toHaveClass('bg-red-400');
    });

    test('decrease direction shows green color', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'dec', direction: 'decrease', emissions: 80 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-dec');
      expect(bar).toHaveClass('bg-green-400');
    });

    test('same direction shows blue/neutral color', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'same', direction: 'same', emissions: 100 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-same');
      expect(bar).toHaveClass('bg-blue-400');
    });

    test('mixed directions show appropriate colors', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'baseline', direction: 'same', emissions: 100 }),
        createDelta({ scenarioId: 'worse', direction: 'increase', emissions: 150 }),
        createDelta({ scenarioId: 'better', direction: 'decrease', emissions: 70 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('bar-fill-baseline')).toHaveClass('bg-blue-400');
      expect(screen.getByTestId('bar-fill-worse')).toHaveClass('bg-red-400');
      expect(screen.getByTestId('bar-fill-better')).toHaveClass('bg-green-400');
    });
  });

  describe('Labels and Values', () => {
    test('displays scenario name as label', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'test', scenarioName: 'Production Baseline' }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('scenario-label-test')).toHaveTextContent('Production Baseline');
    });

    test('displays emissions value with unit', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'test', emissions: 125.5 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('emissions-value-test')).toHaveTextContent('125.5 kg');
    });

    test('formats emissions to 1 decimal place', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'precise', emissions: 99.999 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      // Should round to 100.0
      expect(screen.getByTestId('emissions-value-precise')).toHaveTextContent('100.0 kg');
    });

    test('handles long scenario names', () => {
      const deltas: DeltaData[] = [
        createDelta({
          scenarioId: 'long',
          scenarioName: 'Very Long Scenario Name That Might Need Truncation',
        }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('scenario-label-long')).toHaveTextContent(
        /Very Long Scenario Name/
      );
    });
  });

  describe('Bar Track and Fill', () => {
    test('bar track has gray background', () => {
      const deltas: DeltaData[] = [createDelta({ scenarioId: 'track' })];

      render(<DeltaVisualization deltas={deltas} />);

      const track = screen.getByTestId('bar-track-track');
      expect(track).toHaveClass('bg-gray-100');
    });

    test('bar track has 100% width', () => {
      const deltas: DeltaData[] = [createDelta({ scenarioId: 'full' })];

      render(<DeltaVisualization deltas={deltas} />);

      const track = screen.getByTestId('bar-track-full');
      expect(track).toHaveStyle({ width: '100%' });
    });
  });

  describe('Accessibility', () => {
    test('bars have progressbar role', () => {
      const deltas: DeltaData[] = [createDelta({ scenarioId: 'a11y' })];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-a11y');
      expect(bar).toHaveAttribute('role', 'progressbar');
    });

    test('bars have aria-valuenow with emissions value', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'aria', emissions: 75 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-aria');
      expect(bar).toHaveAttribute('aria-valuenow', '75');
    });

    test('bars have aria-valuemin of 0', () => {
      const deltas: DeltaData[] = [createDelta({ scenarioId: 'min' })];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-min');
      expect(bar).toHaveAttribute('aria-valuemin', '0');
    });

    test('bars have aria-valuemax with max emissions', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'first', emissions: 50 }),
        createDelta({ scenarioId: 'max', emissions: 200 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      // All bars should have max set to highest emissions
      const firstBar = screen.getByTestId('bar-fill-first');
      expect(firstBar).toHaveAttribute('aria-valuemax', '200');
    });

    test('bars have descriptive aria-label', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'labeled', scenarioName: 'My Scenario', emissions: 150 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const bar = screen.getByTestId('bar-fill-labeled');
      expect(bar).toHaveAttribute('aria-label', 'My Scenario: 150 kg CO2e');
    });
  });

  describe('Order Preservation', () => {
    test('bars render in same order as deltas array', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'first', scenarioName: 'First' }),
        createDelta({ scenarioId: 'second', scenarioName: 'Second' }),
        createDelta({ scenarioId: 'third', scenarioName: 'Third' }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const container = screen.getByTestId('bars-container');
      const rows = container.querySelectorAll('[data-testid^="bar-row-"]');

      expect(rows[0]).toHaveAttribute('data-testid', 'bar-row-first');
      expect(rows[1]).toHaveAttribute('data-testid', 'bar-row-second');
      expect(rows[2]).toHaveAttribute('data-testid', 'bar-row-third');
    });
  });

  describe('Edge Cases', () => {
    test('handles negative emissions (carbon sequestration)', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'neg', emissions: -50, direction: 'decrease' }),
        createDelta({ scenarioId: 'pos', emissions: 100, direction: 'increase' }),
      ];

      // Should handle without crashing
      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('delta-visualization')).toBeInTheDocument();
    });

    test('handles very large emissions values', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'huge', emissions: 999999999 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      expect(screen.getByTestId('emissions-value-huge')).toHaveTextContent('999999999.0 kg');
    });

    test('handles decimal emissions in bar width calculation', () => {
      const deltas: DeltaData[] = [
        createDelta({ scenarioId: 'full', emissions: 100.0 }),
        createDelta({ scenarioId: 'partial', emissions: 33.33 }),
      ];

      render(<DeltaVisualization deltas={deltas} />);

      const partialBar = screen.getByTestId('bar-fill-partial');
      // 33.33/100 = 33.33%
      expect(partialBar).toHaveStyle({ width: '33.33%' });
    });
  });

  describe('Styling', () => {
    test('bar fill has transition for smooth animation', () => {
      const deltas: DeltaData[] = [createDelta({ scenarioId: 'animated' })];

      render(<DeltaVisualization deltas={deltas} />);

      // Check that component renders (animation classes will be tested in E2E)
      expect(screen.getByTestId('bar-fill-animated')).toBeInTheDocument();
    });
  });
});
