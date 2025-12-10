/**
 * useTrendData Hook Tests
 *
 * Tests for the data transformation hook that converts scenario
 * comparison data into area chart format for trend visualization.
 *
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 *
 * Test Coverage:
 * - Data transformation from scenarios to trend chart format
 * - Series color assignment
 * - Target line calculation
 * - Date formatting and parsing
 * - Memoization behavior
 * - Edge cases and error handling
 */

import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Hook to be created at: frontend/src/hooks/useTrendData.ts
import { useTrendData } from '../../src/hooks/useTrendData';

// ============================================================================
// Test Data Fixtures
// ============================================================================

interface ScenarioData {
  id: string;
  name: string;
  calculations: Array<{
    period: string;
    total_co2e_kg: number;
  }>;
}

interface HistoricalEmissions {
  period: string;
  total_co2e_kg: number;
  materials_co2e?: number;
  energy_co2e?: number;
  transport_co2e?: number;
}

const mockScenarios: ScenarioData[] = [
  {
    id: 'baseline',
    name: 'Baseline',
    calculations: [
      { period: '2023-01', total_co2e_kg: 1500 },
      { period: '2023-02', total_co2e_kg: 1450 },
      { period: '2023-03', total_co2e_kg: 1600 },
      { period: '2023-04', total_co2e_kg: 1520 },
    ],
  },
  {
    id: 'scenario-a',
    name: 'Scenario A (10% reduction)',
    calculations: [
      { period: '2023-01', total_co2e_kg: 1350 },
      { period: '2023-02', total_co2e_kg: 1305 },
      { period: '2023-03', total_co2e_kg: 1440 },
      { period: '2023-04', total_co2e_kg: 1368 },
    ],
  },
];

const mockHistoricalData: HistoricalEmissions[] = [
  { period: '2022-01', total_co2e_kg: 1800, materials_co2e: 900, energy_co2e: 600, transport_co2e: 300 },
  { period: '2022-02', total_co2e_kg: 1750, materials_co2e: 875, energy_co2e: 580, transport_co2e: 295 },
  { period: '2022-03', total_co2e_kg: 1900, materials_co2e: 950, energy_co2e: 630, transport_co2e: 320 },
  { period: '2022-04', total_co2e_kg: 1700, materials_co2e: 850, energy_co2e: 560, transport_co2e: 290 },
];

const mockSingleSeries = [
  {
    id: 'total',
    name: 'Total Emissions',
    calculations: [
      { period: '2023-01', total_co2e_kg: 1500 },
      { period: '2023-02', total_co2e_kg: 1450 },
    ],
  },
];

const mockEmptyScenarios: ScenarioData[] = [];

// ============================================================================
// Basic Data Transformation Tests
// ============================================================================

describe('useTrendData', () => {
  describe('Basic Transformation', () => {
    it('transforms scenario data to trend chart format', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      expect(result.current.series).toBeDefined();
      expect(Array.isArray(result.current.series)).toBe(true);
    });

    it('returns correct number of series', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      expect(result.current.series.length).toBe(2);
    });

    it('series have correct structure', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      result.current.series.forEach((series) => {
        expect(series).toHaveProperty('id');
        expect(series).toHaveProperty('data');
        expect(Array.isArray(series.data)).toBe(true);
      });
    });

    it('data points have x and y properties', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      result.current.series.forEach((series) => {
        series.data.forEach((point) => {
          expect(point).toHaveProperty('x');
          expect(point).toHaveProperty('y');
        });
      });
    });

    it('preserves series names from scenario names', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      const seriesIds = result.current.series.map((s) => s.id);

      expect(seriesIds).toContain('Baseline');
      expect(seriesIds).toContain('Scenario A (10% reduction)');
    });

    it('correctly maps CO2e values to y-axis', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      const baseline = result.current.series.find((s) => s.id === 'Baseline');
      const firstPoint = baseline?.data[0];

      expect(firstPoint?.y).toBe(1500);
    });
  });

  // ============================================================================
  // Historical Data Tests
  // ============================================================================

  describe('Historical Data', () => {
    it('transforms historical emissions to trend format', () => {
      const { result } = renderHook(() =>
        useTrendData({ historical: mockHistoricalData })
      );

      expect(result.current.series.length).toBeGreaterThan(0);
    });

    it('creates series for total emissions from historical data', () => {
      const { result } = renderHook(() =>
        useTrendData({ historical: mockHistoricalData })
      );

      const totalSeries = result.current.series.find(
        (s) => s.id === 'Total Emissions' || s.id === 'Historical'
      );

      expect(totalSeries).toBeDefined();
    });

    it('can create separate series for each emission category', () => {
      const { result } = renderHook(() =>
        useTrendData({
          historical: mockHistoricalData,
          splitByCategory: true,
        })
      );

      const seriesIds = result.current.series.map((s) => s.id);

      expect(seriesIds).toContain('Materials');
      expect(seriesIds).toContain('Energy');
      expect(seriesIds).toContain('Transport');
    });

    it('combines scenarios and historical data', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          historical: mockHistoricalData,
        })
      );

      // Should have both scenario series and historical series
      expect(result.current.series.length).toBeGreaterThan(2);
    });
  });

  // ============================================================================
  // Color Assignment Tests
  // ============================================================================

  describe('Color Assignment', () => {
    it('assigns colors to each series', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      result.current.series.forEach((series) => {
        expect(series.color).toBeDefined();
        expect(typeof series.color).toBe('string');
      });
    });

    it('assigns distinct colors to different series', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      const colors = result.current.series.map((s) => s.color);
      const uniqueColors = new Set(colors);

      expect(uniqueColors.size).toBe(colors.length);
    });

    it('uses consistent color for same series across rerenders', () => {
      const { result, rerender } = renderHook(
        ({ scenarios }) => useTrendData({ scenarios }),
        { initialProps: { scenarios: mockScenarios } }
      );

      const firstColors = result.current.series.map((s) => s.color);

      rerender({ scenarios: mockScenarios });

      const secondColors = result.current.series.map((s) => s.color);

      expect(firstColors).toEqual(secondColors);
    });

    it('allows custom color scheme', () => {
      const customColors = ['#ff0000', '#00ff00', '#0000ff'];

      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          colors: customColors,
        })
      );

      result.current.series.forEach((series, index) => {
        expect(series.color).toBe(customColors[index % customColors.length]);
      });
    });
  });

  // ============================================================================
  // Target Line Tests
  // ============================================================================

  describe('Target Line', () => {
    it('calculates target line when target value is provided', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 1200,
        })
      );

      expect(result.current.targetLine).toBeDefined();
    });

    it('target line has correct value', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 1200,
        })
      );

      expect(result.current.targetLine?.value).toBe(1200);
    });

    it('target line includes label', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 1200,
          targetLabel: '2025 Target',
        })
      );

      expect(result.current.targetLine?.label).toBe('2025 Target');
    });

    it('uses default label when not specified', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 1200,
        })
      );

      expect(result.current.targetLine?.label).toBe('Target');
    });

    it('does not create target line when targetValue is undefined', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
        })
      );

      expect(result.current.targetLine).toBeUndefined();
    });

    it('does not create target line when targetValue is zero', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 0,
        })
      );

      expect(result.current.targetLine).toBeUndefined();
    });
  });

  // ============================================================================
  // Date Formatting Tests
  // ============================================================================

  describe('Date Formatting', () => {
    it('parses YYYY-MM format correctly', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      const firstPoint = result.current.series[0].data[0];

      expect(firstPoint.x).toBe('2023-01');
    });

    it('handles ISO date format', () => {
      const isoScenarios = [
        {
          id: 'iso-dates',
          name: 'ISO Format',
          calculations: [
            { period: '2023-01-15T00:00:00Z', total_co2e_kg: 1500 },
            { period: '2023-02-15T00:00:00Z', total_co2e_kg: 1450 },
          ],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: isoScenarios })
      );

      expect(result.current.series.length).toBe(1);
      expect(result.current.series[0].data.length).toBe(2);
    });

    it('handles quarterly format (Q1 2023)', () => {
      const quarterlyScenarios = [
        {
          id: 'quarterly',
          name: 'Quarterly Data',
          calculations: [
            { period: 'Q1 2023', total_co2e_kg: 4500 },
            { period: 'Q2 2023', total_co2e_kg: 4300 },
          ],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: quarterlyScenarios })
      );

      expect(result.current.series[0].data[0].x).toBe('Q1 2023');
    });

    it('handles yearly format', () => {
      const yearlyScenarios = [
        {
          id: 'yearly',
          name: 'Yearly Data',
          calculations: [
            { period: '2021', total_co2e_kg: 18000 },
            { period: '2022', total_co2e_kg: 17000 },
            { period: '2023', total_co2e_kg: 15000 },
          ],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: yearlyScenarios })
      );

      expect(result.current.series[0].data.length).toBe(3);
    });

    it('sorts data points chronologically', () => {
      const unsortedScenarios = [
        {
          id: 'unsorted',
          name: 'Unsorted Data',
          calculations: [
            { period: '2023-03', total_co2e_kg: 1600 },
            { period: '2023-01', total_co2e_kg: 1500 },
            { period: '2023-02', total_co2e_kg: 1450 },
          ],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: unsortedScenarios, sortByDate: true })
      );

      const xValues = result.current.series[0].data.map((d) => d.x);

      expect(xValues).toEqual(['2023-01', '2023-02', '2023-03']);
    });
  });

  // ============================================================================
  // Edge Cases Tests
  // ============================================================================

  describe('Edge Cases', () => {
    it('handles empty scenarios array', () => {
      const { result } = renderHook(() =>
        useTrendData({ scenarios: mockEmptyScenarios })
      );

      expect(result.current.series).toEqual([]);
    });

    it('handles null input gracefully', () => {
      const { result } = renderHook(() =>
        useTrendData({ scenarios: null as unknown as ScenarioData[] })
      );

      expect(result.current.series).toEqual([]);
    });

    it('handles undefined input gracefully', () => {
      const { result } = renderHook(() =>
        useTrendData({ scenarios: undefined as unknown as ScenarioData[] })
      );

      expect(result.current.series).toEqual([]);
    });

    it('handles scenario with empty calculations array', () => {
      const emptyCalcScenarios = [
        {
          id: 'empty',
          name: 'Empty Calculations',
          calculations: [],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: emptyCalcScenarios })
      );

      expect(result.current.series[0].data).toEqual([]);
    });

    it('handles single data point per series', () => {
      const singlePointScenarios = [
        {
          id: 'single',
          name: 'Single Point',
          calculations: [{ period: '2023-01', total_co2e_kg: 1500 }],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: singlePointScenarios })
      );

      expect(result.current.series[0].data.length).toBe(1);
    });

    it('handles very large number of data points', () => {
      const largeScenarios = [
        {
          id: 'large',
          name: 'Large Dataset',
          calculations: Array.from({ length: 1000 }, (_, i) => ({
            period: `2020-${String((i % 12) + 1).padStart(2, '0')}`,
            total_co2e_kg: 1000 + Math.random() * 500,
          })),
        },
      ];

      const startTime = performance.now();

      const { result } = renderHook(() =>
        useTrendData({ scenarios: largeScenarios })
      );

      const endTime = performance.now();

      // Should complete quickly
      expect(endTime - startTime).toBeLessThan(100);
      expect(result.current.series[0].data.length).toBe(1000);
    });

    it('handles zero values correctly', () => {
      const zeroScenarios = [
        {
          id: 'zeros',
          name: 'Zero Values',
          calculations: [
            { period: '2023-01', total_co2e_kg: 0 },
            { period: '2023-02', total_co2e_kg: 0 },
          ],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: zeroScenarios })
      );

      expect(result.current.series[0].data[0].y).toBe(0);
      expect(result.current.series[0].data[1].y).toBe(0);
    });

    it('handles negative values (for adjustments)', () => {
      const negativeScenarios = [
        {
          id: 'negative',
          name: 'With Adjustments',
          calculations: [
            { period: '2023-01', total_co2e_kg: 1500 },
            { period: '2023-02', total_co2e_kg: -100 }, // Carbon offset
          ],
        },
      ];

      const { result } = renderHook(() =>
        useTrendData({ scenarios: negativeScenarios })
      );

      expect(result.current.series[0].data[1].y).toBe(-100);
    });
  });

  // ============================================================================
  // Memoization Tests
  // ============================================================================

  describe('Memoization', () => {
    it('returns same reference for identical input', () => {
      const { result, rerender } = renderHook(
        ({ scenarios }) => useTrendData({ scenarios }),
        { initialProps: { scenarios: mockScenarios } }
      );

      const firstResult = result.current;

      rerender({ scenarios: mockScenarios });

      const secondResult = result.current;

      expect(firstResult.series).toBe(secondResult.series);
    });

    it('returns new reference when scenarios change', () => {
      const { result, rerender } = renderHook(
        ({ scenarios }) => useTrendData({ scenarios }),
        { initialProps: { scenarios: mockScenarios } }
      );

      const firstResult = result.current;

      const newScenarios = [
        {
          id: 'new',
          name: 'New Scenario',
          calculations: [{ period: '2024-01', total_co2e_kg: 2000 }],
        },
      ];

      rerender({ scenarios: newScenarios });

      const secondResult = result.current;

      expect(firstResult.series).not.toBe(secondResult.series);
    });

    it('memoizes target line calculation', () => {
      const { result, rerender } = renderHook(
        ({ scenarios, targetValue }) => useTrendData({ scenarios, targetValue }),
        { initialProps: { scenarios: mockScenarios, targetValue: 1200 } }
      );

      const firstTargetLine = result.current.targetLine;

      rerender({ scenarios: mockScenarios, targetValue: 1200 });

      const secondTargetLine = result.current.targetLine;

      expect(firstTargetLine).toBe(secondTargetLine);
    });
  });

  // ============================================================================
  // Y-Axis Domain Tests
  // ============================================================================

  describe('Y-Axis Domain', () => {
    it('calculates yDomain from data', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      expect(result.current.yDomain).toBeDefined();
      expect(result.current.yDomain).toHaveProperty('min');
      expect(result.current.yDomain).toHaveProperty('max');
    });

    it('yDomain min is below minimum data point', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      // Min y value in mockScenarios is 1305
      expect(result.current.yDomain.min).toBeLessThanOrEqual(1305);
    });

    it('yDomain max is above maximum data point', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      // Max y value in mockScenarios is 1600
      expect(result.current.yDomain.max).toBeGreaterThanOrEqual(1600);
    });

    it('includes target value in yDomain when below data', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 1000, // Below all data
        })
      );

      expect(result.current.yDomain.min).toBeLessThanOrEqual(1000);
    });

    it('includes target value in yDomain when above data', () => {
      const { result } = renderHook(() =>
        useTrendData({
          scenarios: mockScenarios,
          targetValue: 2000, // Above all data
        })
      );

      expect(result.current.yDomain.max).toBeGreaterThanOrEqual(2000);
    });

    it('adds padding to yDomain', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      // Should have some padding (not exactly min/max of data)
      const allYValues = mockScenarios.flatMap((s) =>
        s.calculations.map((c) => c.total_co2e_kg)
      );
      const dataMin = Math.min(...allYValues);
      const dataMax = Math.max(...allYValues);

      expect(result.current.yDomain.min).toBeLessThan(dataMin);
      expect(result.current.yDomain.max).toBeGreaterThan(dataMax);
    });
  });

  // ============================================================================
  // Unit Handling Tests
  // ============================================================================

  describe('Unit Handling', () => {
    it('returns unit in result', () => {
      const { result } = renderHook(() =>
        useTrendData({ scenarios: mockScenarios, unit: 'kg CO2e' })
      );

      expect(result.current.unit).toBe('kg CO2e');
    });

    it('uses default unit when not specified', () => {
      const { result } = renderHook(() => useTrendData({ scenarios: mockScenarios }));

      expect(result.current.unit).toBe('kg CO2e');
    });

    it('supports tonnes unit', () => {
      const { result } = renderHook(() =>
        useTrendData({ scenarios: mockScenarios, unit: 'tonnes CO2e' })
      );

      expect(result.current.unit).toBe('tonnes CO2e');
    });
  });
});
