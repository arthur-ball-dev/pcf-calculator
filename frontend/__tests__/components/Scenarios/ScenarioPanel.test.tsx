/**
 * ScenarioPanel Component Tests
 *
 * Test-Driven Development for TASK-FE-P5-002
 * Written BEFORE implementation (TDD Protocol)
 *
 * Tests for individual scenario display panel including:
 * - Scenario name display
 * - Baseline badge display
 * - Total emissions value
 * - Delta percentage with color coding
 * - BOM entries list
 */

import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '../../testUtils';
// Real import - enabled per TDD Exception approval (TASK-FE-P5-002_SEQ-003)
import { ScenarioPanel, type ComparisonDelta } from '../../../src/components/Scenarios/ScenarioPanel';
import type { Scenario, BOMEntry } from '../../../src/store/scenarioStore';

// Mock helper for creating scenarios
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

describe('ScenarioPanel Component', () => {
  describe('Scenario Name Display', () => {
    test('displays scenario name', () => {
      const scenario = createMockScenario({ name: 'Production Baseline' });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByText('Production Baseline')).toBeInTheDocument();
    });

    test('displays name in a heading element', () => {
      const scenario = createMockScenario({ name: 'My Scenario' });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByRole('heading', { name: /My Scenario/i })).toBeInTheDocument();
    });

    test('handles special characters in name', () => {
      const scenario = createMockScenario({ name: 'Test & Analysis <2024>' });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByText('Test & Analysis <2024>')).toBeInTheDocument();
    });

    test('handles empty name gracefully', () => {
      const scenario = createMockScenario({ name: '' });

      render(<ScenarioPanel scenario={scenario} />);

      // Should render without error
      expect(screen.getByTestId('scenario-panel-' + scenario.id)).toBeInTheDocument();
    });
  });

  describe('Baseline Badge Display', () => {
    test('shows "Baseline" badge when isBaseline=true', () => {
      const scenario = createMockScenario({ isBaseline: true });

      render(<ScenarioPanel scenario={scenario} isBaseline={true} />);

      expect(screen.getByTestId('baseline-badge')).toBeInTheDocument();
      expect(screen.getByText('Baseline')).toBeInTheDocument();
    });

    test('does not show badge when isBaseline=false', () => {
      const scenario = createMockScenario({ isBaseline: false });

      render(<ScenarioPanel scenario={scenario} isBaseline={false} />);

      expect(screen.queryByTestId('baseline-badge')).not.toBeInTheDocument();
    });

    test('does not show badge when isBaseline prop omitted', () => {
      const scenario = createMockScenario();

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.queryByTestId('baseline-badge')).not.toBeInTheDocument();
    });

    test('badge has appropriate styling', () => {
      const scenario = createMockScenario({ isBaseline: true });

      render(<ScenarioPanel scenario={scenario} isBaseline={true} />);

      const badge = screen.getByTestId('baseline-badge');
      // Badge should exist and be visible
      expect(badge).toBeVisible();
    });
  });

  describe('Total Emissions Display', () => {
    test('displays total emissions value', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 125.75 },
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('total-emissions')).toHaveTextContent('125.75');
    });

    test('formats emissions with 2 decimal places', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 100.5 },
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('total-emissions')).toHaveTextContent('100.50');
    });

    test('displays unit "kg CO2e"', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 50 },
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('total-emissions')).toHaveTextContent('kg CO2e');
    });

    test('shows "N/A" when results is null', () => {
      const scenario = createMockScenario({
        results: null,
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('total-emissions')).toHaveTextContent('N/A');
    });

    test('handles zero emissions', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 0 },
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('total-emissions')).toHaveTextContent('0.00');
    });

    test('handles large emission values', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 1234567.89 },
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('total-emissions')).toHaveTextContent('1234567.89');
    });
  });

  describe('Delta Percentage Display - Increase', () => {
    test('shows delta percentage with positive sign for increase', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 120 },
      });
      const delta: ComparisonDelta = {
        absoluteDelta: 20,
        percentageDelta: 20,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('delta-display')).toHaveTextContent('+20.0%');
    });

    test('displays red color for increase', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 15,
        percentageDelta: 15,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      const deltaDisplay = screen.getByTestId('delta-display');
      expect(deltaDisplay).toHaveClass('text-red-600');
    });

    test('shows red background for increase', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 10,
        percentageDelta: 10,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      const deltaDisplay = screen.getByTestId('delta-display');
      expect(deltaDisplay).toHaveClass('bg-red-50');
    });

    test('shows absolute delta value with increase', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 25.5,
        percentageDelta: 25.5,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('absolute-delta')).toHaveTextContent('+25.50 kg CO2e');
    });
  });

  describe('Delta Percentage Display - Decrease', () => {
    test('shows delta percentage with negative sign for decrease', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 80 },
      });
      const delta: ComparisonDelta = {
        absoluteDelta: -20,
        percentageDelta: -20,
        direction: 'decrease',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('delta-display')).toHaveTextContent('-20.0%');
    });

    test('displays green color for decrease', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: -15,
        percentageDelta: -15,
        direction: 'decrease',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      const deltaDisplay = screen.getByTestId('delta-display');
      expect(deltaDisplay).toHaveClass('text-green-600');
    });

    test('shows green background for decrease', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: -30,
        percentageDelta: -30,
        direction: 'decrease',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      const deltaDisplay = screen.getByTestId('delta-display');
      expect(deltaDisplay).toHaveClass('bg-green-50');
    });

    test('shows absolute delta value with decrease', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: -12.75,
        percentageDelta: -12.75,
        direction: 'decrease',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('absolute-delta')).toHaveTextContent('-12.75 kg CO2e');
    });
  });

  describe('Delta Percentage Display - Same', () => {
    test('shows 0% for same direction', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 0,
        percentageDelta: 0,
        direction: 'same',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('delta-display')).toHaveTextContent('0.0%');
    });

    test('displays gray/neutral color for same', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 0,
        percentageDelta: 0,
        direction: 'same',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      const deltaDisplay = screen.getByTestId('delta-display');
      expect(deltaDisplay).toHaveClass('text-gray-600');
    });

    test('shows gray background for same', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 0,
        percentageDelta: 0,
        direction: 'same',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      const deltaDisplay = screen.getByTestId('delta-display');
      expect(deltaDisplay).toHaveClass('bg-gray-50');
    });
  });

  describe('Delta Display Without comparisonDelta', () => {
    test('does not show delta when comparisonDelta is undefined', () => {
      const scenario = createMockScenario();

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.queryByTestId('delta-display')).not.toBeInTheDocument();
    });

    test('baseline scenario typically has no delta display', () => {
      const scenario = createMockScenario({ isBaseline: true });

      render(<ScenarioPanel scenario={scenario} isBaseline={true} />);

      expect(screen.queryByTestId('delta-display')).not.toBeInTheDocument();
    });
  });

  describe('BOM Entries List', () => {
    test('renders BOM entries list', () => {
      const scenario = createMockScenario({
        bomEntries: [
          { id: 'b1', component_name: 'Steel', quantity: 10, unit: 'kg', emissions: 25.0 },
          { id: 'b2', component_name: 'Plastic', quantity: 5, unit: 'kg', emissions: 15.0 },
        ],
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('bom-entries')).toBeInTheDocument();
    });

    test('displays correct number of BOM entries', () => {
      const scenario = createMockScenario({
        bomEntries: [
          { id: 'b1', component_name: 'Steel', quantity: 10, unit: 'kg', emissions: 25.0 },
          { id: 'b2', component_name: 'Plastic', quantity: 5, unit: 'kg', emissions: 15.0 },
          { id: 'b3', component_name: 'Copper', quantity: 2, unit: 'kg', emissions: 8.0 },
        ],
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('bom-entry-0')).toBeInTheDocument();
      expect(screen.getByTestId('bom-entry-1')).toBeInTheDocument();
      expect(screen.getByTestId('bom-entry-2')).toBeInTheDocument();
    });

    test('displays component name for each entry', () => {
      const scenario = createMockScenario({
        bomEntries: [
          { id: 'b1', component_name: 'Aluminum', quantity: 7, unit: 'kg', emissions: 18.0 },
        ],
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByText('Aluminum')).toBeInTheDocument();
    });

    test('displays quantity and unit for each entry', () => {
      const scenario = createMockScenario({
        bomEntries: [
          { id: 'b1', component_name: 'Steel', quantity: 15, unit: 'kg', emissions: 30.0 },
        ],
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByText(/15.*kg/)).toBeInTheDocument();
    });

    test('displays emissions for each entry', () => {
      const scenario = createMockScenario({
        bomEntries: [
          { id: 'b1', component_name: 'Steel', quantity: 10, unit: 'kg', emissions: 25.5 },
        ],
      });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByText(/25.50.*kg/)).toBeInTheDocument();
    });

    test('handles empty BOM entries', () => {
      const scenario = createMockScenario({
        bomEntries: [],
      });

      render(<ScenarioPanel scenario={scenario} />);

      const bomContainer = screen.getByTestId('bom-entries');
      expect(bomContainer.querySelectorAll('[data-testid^="bom-entry-"]')).toHaveLength(0);
    });

    test('handles BOM entry without emissions value', () => {
      const scenario = createMockScenario({
        bomEntries: [
          { id: 'b1', component_name: 'Unknown Material', quantity: 5, unit: 'kg' },
        ],
      });

      render(<ScenarioPanel scenario={scenario} />);

      // Should show 0.00 or similar default
      expect(screen.getByText(/0.00.*kg/)).toBeInTheDocument();
    });

    test('handles large number of BOM entries', () => {
      const manyEntries = Array.from({ length: 20 }, (_, i) => ({
        id: 'bom-' + i,
        component_name: 'Material ' + (i + 1),
        quantity: i + 1,
        unit: 'kg',
        emissions: (i + 1) * 2,
      }));

      const scenario = createMockScenario({ bomEntries: manyEntries });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByText('Material 1')).toBeInTheDocument();
      expect(screen.getByText('Material 20')).toBeInTheDocument();
    });
  });

  describe('Panel Identification', () => {
    test('panel has testid based on scenario id', () => {
      const scenario = createMockScenario({ id: 'unique-scenario-id' });

      render(<ScenarioPanel scenario={scenario} />);

      expect(screen.getByTestId('scenario-panel-unique-scenario-id')).toBeInTheDocument();
    });
  });

  describe('Decimal Formatting', () => {
    test('delta percentage formatted to 1 decimal place', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 12.567,
        percentageDelta: 12.567,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('delta-display')).toHaveTextContent('12.6%');
    });

    test('absolute delta formatted to 2 decimal places', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 12.567,
        percentageDelta: 12.567,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      expect(screen.getByTestId('absolute-delta')).toHaveTextContent('12.57');
    });
  });

  describe('Accessibility', () => {
    test('scenario panel is accessible', () => {
      const scenario = createMockScenario({ name: 'Accessible Scenario' });

      render(<ScenarioPanel scenario={scenario} />);

      // Has heading for scenario name
      expect(screen.getAllByRole('heading').length).toBeGreaterThan(0);
    });

    test('emissions value is readable', () => {
      const scenario = createMockScenario({
        results: { total_emissions: 100 },
      });

      render(<ScenarioPanel scenario={scenario} />);

      // Emissions should include unit for context
      expect(screen.getByTestId('total-emissions')).toHaveTextContent('kg CO2e');
    });

    test('delta direction is indicated beyond color', () => {
      const scenario = createMockScenario();
      const delta: ComparisonDelta = {
        absoluteDelta: 20,
        percentageDelta: 20,
        direction: 'increase',
      };

      render(<ScenarioPanel scenario={scenario} comparisonDelta={delta} />);

      // Has + sign for increase, not just color
      expect(screen.getByTestId('delta-display')).toHaveTextContent('+');
      // Or has data attribute for direction
      expect(screen.getByTestId('delta-display')).toHaveAttribute('data-direction', 'increase');
    });
  });
});
