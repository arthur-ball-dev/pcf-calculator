/**
 * useTrendData Hook
 *
 * Transforms scenario comparison data into area chart format for
 * emissions trend visualization. Supports multiple scenarios,
 * target lines, and historical data.
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 */

import { useMemo } from 'react';

// ============================================================================
// Types
// ============================================================================

export interface ScenarioCalculation {
  period: string;
  total_co2e_kg: number;
}

export interface ScenarioData {
  id: string;
  name: string;
  calculations: ScenarioCalculation[];
}

export interface HistoricalEmissions {
  period: string;
  total_co2e_kg: number;
  materials_co2e?: number;
  energy_co2e?: number;
  transport_co2e?: number;
}

export interface TrendDataPoint {
  x: string;
  y: number;
}

export interface TrendSeries {
  id: string;
  data: TrendDataPoint[];
  color: string;
}

export interface TargetLine {
  value: number;
  label: string;
}

export interface YDomain {
  min: number;
  max: number;
}

export interface UseTrendDataResult {
  series: TrendSeries[];
  targetLine?: TargetLine;
  yDomain: YDomain;
  unit: string;
}

export interface UseTrendDataOptions {
  /** Scenario data to transform */
  scenarios?: ScenarioData[] | null;
  /** Historical emissions data */
  historical?: HistoricalEmissions[] | null;
  /** Split historical data by emission category */
  splitByCategory?: boolean;
  /** Target value for reference line */
  targetValue?: number;
  /** Label for target line */
  targetLabel?: string;
  /** Custom color scheme */
  colors?: string[];
  /** Sort data points chronologically */
  sortByDate?: boolean;
  /** Unit label for values */
  unit?: string;
}

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_COLORS = [
  '#228be6', '#fa5252', '#40c057', '#fab005',
  '#7950f2', '#e64980', '#15aabf', '#82c91e',
];

const CATEGORY_COLORS: Record<string, string> = {
  Materials: '#51cf66',
  Energy: '#339af0',
  Transport: '#fa5252',
  'Total Emissions': '#495057',
  Historical: '#868e96',
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Parse and normalize date string for sorting
 */
function parseDateKey(dateStr: string): string {
  // Handle various date formats
  if (dateStr.startsWith('Q')) {
    // Quarterly format: "Q1 2023" -> "2023-Q1"
    const [quarter, year] = dateStr.split(' ');
    return `${year}-${quarter}`;
  }
  if (/^\d{4}$/.test(dateStr)) {
    // Year only: "2023" -> "2023-01"
    return `${dateStr}-01`;
  }
  if (dateStr.includes('T')) {
    // ISO format: extract date part
    return dateStr.split('T')[0];
  }
  // Default: return as-is (assumed YYYY-MM format)
  return dateStr;
}

/**
 * Sort data points chronologically
 */
function sortDataPoints(data: TrendDataPoint[]): TrendDataPoint[] {
  return [...data].sort((a, b) => {
    const keyA = parseDateKey(String(a.x));
    const keyB = parseDateKey(String(b.x));
    return keyA.localeCompare(keyB);
  });
}

/**
 * Calculate y-axis domain with padding
 */
function calculateYDomain(
  allValues: number[],
  targetValue?: number
): YDomain {
  if (allValues.length === 0) {
    return { min: 0, max: 100 };
  }

  let min = Math.min(...allValues);
  let max = Math.max(...allValues);

  // Include target value in domain if provided
  if (targetValue !== undefined && targetValue > 0) {
    min = Math.min(min, targetValue);
    max = Math.max(max, targetValue);
  }

  // Add 10% padding
  const range = max - min;
  const padding = range * 0.1;

  return {
    min: Math.max(0, min - padding),
    max: max + padding,
  };
}

// ============================================================================
// Hook
// ============================================================================

export function useTrendData(options: UseTrendDataOptions): UseTrendDataResult {
  const {
    scenarios,
    historical,
    splitByCategory = false,
    targetValue,
    targetLabel = 'Target',
    colors = DEFAULT_COLORS,
    sortByDate = false,
    unit = 'kg CO2e',
  } = options;

  const result = useMemo<UseTrendDataResult>(() => {
    const series: TrendSeries[] = [];
    const allValues: number[] = [];
    let colorIndex = 0;

    // Process scenarios
    if (scenarios && Array.isArray(scenarios)) {
      for (const scenario of scenarios) {
        if (!scenario.calculations) continue;

        let dataPoints: TrendDataPoint[] = scenario.calculations.map((calc) => ({
          x: calc.period,
          y: calc.total_co2e_kg,
        }));

        if (sortByDate) {
          dataPoints = sortDataPoints(dataPoints);
        }

        // Collect all y values for domain calculation
        dataPoints.forEach((p) => allValues.push(p.y));

        series.push({
          id: scenario.name,
          data: dataPoints,
          color: colors[colorIndex % colors.length],
        });

        colorIndex++;
      }
    }

    // Process historical data
    if (historical && Array.isArray(historical)) {
      if (splitByCategory) {
        // Create separate series for each category
        const categories = ['Materials', 'Energy', 'Transport'];

        for (const category of categories) {
          const key = `${category.toLowerCase()}_co2e` as keyof HistoricalEmissions;
          const hasData = historical.some((h) => h[key] !== undefined && h[key] !== null);

          if (!hasData) continue;

          let dataPoints: TrendDataPoint[] = historical.map((h) => ({
            x: h.period,
            y: (h[key] as number) || 0,
          }));

          if (sortByDate) {
            dataPoints = sortDataPoints(dataPoints);
          }

          dataPoints.forEach((p) => allValues.push(p.y));

          series.push({
            id: category,
            data: dataPoints,
            color: CATEGORY_COLORS[category] || colors[colorIndex % colors.length],
          });

          colorIndex++;
        }
      } else {
        // Single series for total emissions
        let dataPoints: TrendDataPoint[] = historical.map((h) => ({
          x: h.period,
          y: h.total_co2e_kg,
        }));

        if (sortByDate) {
          dataPoints = sortDataPoints(dataPoints);
        }

        dataPoints.forEach((p) => allValues.push(p.y));

        series.push({
          id: 'Total Emissions',
          data: dataPoints,
          color: CATEGORY_COLORS['Historical'] || colors[colorIndex % colors.length],
        });
      }
    }

    // Calculate target line
    const targetLine =
      targetValue !== undefined && targetValue > 0
        ? { value: targetValue, label: targetLabel }
        : undefined;

    // Calculate y-axis domain
    const yDomain = calculateYDomain(allValues, targetValue);

    return {
      series,
      targetLine,
      yDomain,
      unit,
    };
  }, [scenarios, historical, splitByCategory, targetValue, targetLabel, colors, sortByDate, unit]);

  return result;
}

export default useTrendData;
