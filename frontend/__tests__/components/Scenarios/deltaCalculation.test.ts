/**
 * Delta Calculation Tests
 *
 * Test-Driven Development for TASK-FE-P5-002
 * Written BEFORE implementation (TDD Protocol)
 *
 * Tests for calculating emissions deltas between scenarios including:
 * - Absolute delta (kg CO2e difference)
 * - Percentage delta (% change from baseline)
 * - Direction classification (increase/decrease/same)
 * - Edge cases (zero baseline, identical values)
 */

import { describe, test, expect } from 'vitest';
// Real import - enabled per TDD Exception approval (TASK-FE-P5-002_SEQ-003)
import { calculateDelta, calculateDeltas, type DeltaResult, type ScenarioData } from '../../../src/components/Scenarios/deltaCalculation';

describe('Delta Calculations', () => {
  describe('calculateDelta - Single Scenario Comparison', () => {
    describe('Increase Scenario', () => {
      test('Baseline 100, Alternative 120 returns +20 absolute delta', () => {
        const result = calculateDelta(100, 120, 'scenario-1', 'Alternative A');

        expect(result.absoluteDelta).toBe(20);
      });

      test('Baseline 100, Alternative 120 returns +20% percentage delta', () => {
        const result = calculateDelta(100, 120, 'scenario-1', 'Alternative A');

        expect(result.percentageDelta).toBe(20);
      });

      test('Baseline 100, Alternative 120 returns direction="increase"', () => {
        const result = calculateDelta(100, 120, 'scenario-1', 'Alternative A');

        expect(result.direction).toBe('increase');
      });

      test('includes scenario metadata in result', () => {
        const result = calculateDelta(100, 120, 'scenario-abc', 'High Emissions Option');

        expect(result.scenarioId).toBe('scenario-abc');
        expect(result.scenarioName).toBe('High Emissions Option');
        expect(result.emissions).toBe(120);
      });
    });

    describe('Decrease Scenario', () => {
      test('Baseline 100, Alternative 80 returns -20 absolute delta', () => {
        const result = calculateDelta(100, 80, 'scenario-2', 'Alternative B');

        expect(result.absoluteDelta).toBe(-20);
      });

      test('Baseline 100, Alternative 80 returns -20% percentage delta', () => {
        const result = calculateDelta(100, 80, 'scenario-2', 'Alternative B');

        expect(result.percentageDelta).toBe(-20);
      });

      test('Baseline 100, Alternative 80 returns direction="decrease"', () => {
        const result = calculateDelta(100, 80, 'scenario-2', 'Alternative B');

        expect(result.direction).toBe('decrease');
      });
    });

    describe('No Change Scenario', () => {
      test('Baseline 100, Alternative 100 returns 0 absolute delta', () => {
        const result = calculateDelta(100, 100, 'scenario-3', 'Alternative C');

        expect(result.absoluteDelta).toBe(0);
      });

      test('Baseline 100, Alternative 100 returns 0% percentage delta', () => {
        const result = calculateDelta(100, 100, 'scenario-3', 'Alternative C');

        expect(result.percentageDelta).toBe(0);
      });

      test('Baseline 100, Alternative 100 returns direction="same"', () => {
        const result = calculateDelta(100, 100, 'scenario-3', 'Alternative C');

        expect(result.direction).toBe('same');
      });
    });

    describe('Division by Zero Handling', () => {
      test('Baseline 0, Alternative 100 handles division by zero gracefully', () => {
        const result = calculateDelta(0, 100, 'scenario-4', 'From Zero');

        // Should not throw, should return a valid result
        expect(result).toBeDefined();
        expect(result.absoluteDelta).toBe(100);
      });

      test('Baseline 0, Alternative 100 returns percentage as Infinity or special value', () => {
        const result = calculateDelta(0, 100, 'scenario-4', 'From Zero');

        // Implementation can choose: Infinity, NaN, 0, or a large number
        // Most commonly: Infinity or 0
        expect([Infinity, 0, NaN, 100]).toContain(result.percentageDelta);
      });

      test('Baseline 0, Alternative 100 returns direction="increase"', () => {
        const result = calculateDelta(0, 100, 'scenario-4', 'From Zero');

        expect(result.direction).toBe('increase');
      });

      test('Baseline 0, Alternative 0 returns 0% and direction="same"', () => {
        const result = calculateDelta(0, 0, 'scenario-5', 'Both Zero');

        expect(result.absoluteDelta).toBe(0);
        expect(result.percentageDelta).toBe(0);
        expect(result.direction).toBe('same');
      });

      test('Baseline 0, Alternative -50 handles negative alternative', () => {
        const result = calculateDelta(0, -50, 'scenario-6', 'Negative');

        expect(result.absoluteDelta).toBe(-50);
        expect(result.direction).toBe('decrease');
      });
    });

    describe('Decimal Precision', () => {
      test('calculates precise percentage for non-round numbers', () => {
        // 150 / 100 - 1 = 50%
        const result = calculateDelta(100, 150, 'scenario-7', 'Fifty Percent');

        expect(result.percentageDelta).toBe(50);
      });

      test('handles decimal emissions values', () => {
        // 110.5 - 100.25 = 10.25 absolute
        // (10.25 / 100.25) * 100 = ~10.22%
        const result = calculateDelta(100.25, 110.5, 'scenario-8', 'Decimals');

        expect(result.absoluteDelta).toBeCloseTo(10.25, 2);
        expect(result.percentageDelta).toBeCloseTo(10.22, 1);
      });

      test('small percentage changes calculated correctly', () => {
        // 101 - 100 = 1, 1/100 = 1%
        const result = calculateDelta(100, 101, 'scenario-9', 'Small Change');

        expect(result.absoluteDelta).toBe(1);
        expect(result.percentageDelta).toBe(1);
        expect(result.direction).toBe('increase');
      });
    });

    describe('Large Values', () => {
      test('handles large emission values', () => {
        const result = calculateDelta(1000000, 1200000, 'scenario-10', 'Large Scale');

        expect(result.absoluteDelta).toBe(200000);
        expect(result.percentageDelta).toBe(20);
        expect(result.direction).toBe('increase');
      });

      test('handles very small emission values', () => {
        const result = calculateDelta(0.001, 0.0012, 'scenario-11', 'Tiny Scale');

        expect(result.absoluteDelta).toBeCloseTo(0.0002, 4);
        expect(result.percentageDelta).toBe(20);
        expect(result.direction).toBe('increase');
      });
    });
  });

  describe('calculateDeltas - Multiple Scenario Comparison', () => {
    test('returns empty array for empty scenarios list', () => {
      const result = calculateDeltas(100, []);

      expect(result).toEqual([]);
    });

    test('returns array with delta for each scenario', () => {
      const scenarios: ScenarioData[] = [
        { id: 'a', name: 'Scenario A', emissions: 120 },
        { id: 'b', name: 'Scenario B', emissions: 80 },
        { id: 'c', name: 'Scenario C', emissions: 100 },
      ];

      const results = calculateDeltas(100, scenarios);

      expect(results).toHaveLength(3);
    });

    test('calculates correct deltas for multiple scenarios', () => {
      const scenarios: ScenarioData[] = [
        { id: 'a', name: 'Higher', emissions: 150 },
        { id: 'b', name: 'Lower', emissions: 50 },
      ];

      const results = calculateDeltas(100, scenarios);

      const higher = results.find(r => r.scenarioId === 'a');
      const lower = results.find(r => r.scenarioId === 'b');

      expect(higher?.absoluteDelta).toBe(50);
      expect(higher?.percentageDelta).toBe(50);
      expect(higher?.direction).toBe('increase');

      expect(lower?.absoluteDelta).toBe(-50);
      expect(lower?.percentageDelta).toBe(-50);
      expect(lower?.direction).toBe('decrease');
    });

    test('preserves scenario order in results', () => {
      const scenarios: ScenarioData[] = [
        { id: 'first', name: 'First', emissions: 110 },
        { id: 'second', name: 'Second', emissions: 90 },
        { id: 'third', name: 'Third', emissions: 100 },
      ];

      const results = calculateDeltas(100, scenarios);

      expect(results[0].scenarioId).toBe('first');
      expect(results[1].scenarioId).toBe('second');
      expect(results[2].scenarioId).toBe('third');
    });

    test('handles baseline of 0 for all scenarios', () => {
      const scenarios: ScenarioData[] = [
        { id: 'a', name: 'A', emissions: 50 },
        { id: 'b', name: 'B', emissions: 100 },
      ];

      // Should not throw
      const results = calculateDeltas(0, scenarios);

      expect(results).toHaveLength(2);
      expect(results[0].absoluteDelta).toBe(50);
      expect(results[1].absoluteDelta).toBe(100);
    });

    test('includes baseline scenario when in list (direction=same)', () => {
      const scenarios: ScenarioData[] = [
        { id: 'baseline', name: 'Baseline', emissions: 100 },
        { id: 'alt', name: 'Alternative', emissions: 120 },
      ];

      const results = calculateDeltas(100, scenarios);

      const baseline = results.find(r => r.scenarioId === 'baseline');
      expect(baseline?.direction).toBe('same');
      expect(baseline?.absoluteDelta).toBe(0);
      expect(baseline?.percentageDelta).toBe(0);
    });
  });

  describe('Direction Classification', () => {
    test('very small positive change is classified as increase', () => {
      const result = calculateDelta(100, 100.001, 'scenario-x', 'Tiny Increase');

      expect(result.direction).toBe('increase');
    });

    test('very small negative change is classified as decrease', () => {
      const result = calculateDelta(100, 99.999, 'scenario-y', 'Tiny Decrease');

      expect(result.direction).toBe('decrease');
    });

    test('negative emissions values handled correctly', () => {
      // Edge case: carbon sequestration scenario
      const result = calculateDelta(-10, -20, 'scenario-z', 'Sequestration');

      // -20 - (-10) = -10 (decrease in emissions)
      expect(result.absoluteDelta).toBe(-10);
      expect(result.direction).toBe('decrease');
    });
  });

  describe('Type Safety', () => {
    test('returns all required fields in DeltaResult', () => {
      const result = calculateDelta(100, 120, 'test-id', 'Test Name');

      expect(result).toHaveProperty('scenarioId');
      expect(result).toHaveProperty('scenarioName');
      expect(result).toHaveProperty('emissions');
      expect(result).toHaveProperty('absoluteDelta');
      expect(result).toHaveProperty('percentageDelta');
      expect(result).toHaveProperty('direction');
    });

    test('direction is strictly typed enum value', () => {
      const increase = calculateDelta(100, 120, 'a', 'A');
      const decrease = calculateDelta(100, 80, 'b', 'B');
      const same = calculateDelta(100, 100, 'c', 'C');

      expect(['increase', 'decrease', 'same']).toContain(increase.direction);
      expect(['increase', 'decrease', 'same']).toContain(decrease.direction);
      expect(['increase', 'decrease', 'same']).toContain(same.direction);
    });

    test('numeric fields are actual numbers', () => {
      const result = calculateDelta(100, 120, 'test', 'Test');

      expect(typeof result.emissions).toBe('number');
      expect(typeof result.absoluteDelta).toBe('number');
      expect(typeof result.percentageDelta).toBe('number');
    });
  });
});
