/**
 * ScenarioPanel Component
 *
 * Displays an individual scenario's data including:
 * - Scenario name with optional baseline badge
 * - Total emissions with color-coded delta display
 * - BOM entries breakdown
 *
 * Used within ScenarioComparison for side-by-side comparison.
 */

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Scenario } from '@/store/scenarioStore';

// ================================================================
// Type Definitions
// ================================================================

export interface ComparisonDelta {
  absoluteDelta: number;
  percentageDelta: number;
  direction: 'increase' | 'decrease' | 'same';
}

export interface ScenarioPanelProps {
  scenario: Scenario;
  isBaseline?: boolean;
  comparisonDelta?: ComparisonDelta;
}

// ================================================================
// Helper Functions
// ================================================================

function getDeltaColor(direction: string): string {
  if (direction === 'increase') return 'text-red-600 bg-red-50';
  if (direction === 'decrease') return 'text-green-600 bg-green-50';
  return 'text-gray-600 bg-gray-50';
}

// ================================================================
// Component
// ================================================================

export function ScenarioPanel({
  scenario,
  isBaseline,
  comparisonDelta,
}: ScenarioPanelProps) {
  return (
    <Card data-testid={`scenario-panel-${scenario.id}`}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle>
            <h3 className="text-lg font-semibold">{scenario.name}</h3>
          </CardTitle>
          {isBaseline && (
            <Badge
              variant="outline"
              className="bg-blue-50 text-blue-700"
              data-testid="baseline-badge"
            >
              Baseline
            </Badge>
          )}
        </div>

        {comparisonDelta && (
          <div
            data-testid="delta-display"
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-sm font-medium ${getDeltaColor(comparisonDelta.direction)}`}
            data-direction={comparisonDelta.direction}
          >
            <span>
              {comparisonDelta.percentageDelta > 0 ? '+' : ''}
              {comparisonDelta.percentageDelta.toFixed(1)}%
            </span>
            <span
              data-testid="absolute-delta"
              className="text-xs opacity-75"
            >
              ({comparisonDelta.absoluteDelta > 0 ? '+' : ''}
              {comparisonDelta.absoluteDelta.toFixed(2)} kg CO2e)
            </span>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {/* Total Emissions */}
        <div
          className="mb-4 p-4 bg-gray-50 rounded-lg"
          data-testid="total-emissions"
        >
          <div className="text-sm text-gray-500">Total Emissions</div>
          <div className="text-2xl font-bold">
            {scenario.results?.total_emissions !== undefined
              ? scenario.results.total_emissions.toFixed(2)
              : 'N/A'}
            <span className="text-sm font-normal text-gray-500 ml-1">
              kg CO2e
            </span>
          </div>
        </div>

        {/* BOM Breakdown */}
        <div className="space-y-2" data-testid="bom-entries">
          <h4 className="text-sm font-medium text-gray-700">
            Component Breakdown
          </h4>
          {scenario.bomEntries.map((entry, index) => (
            <div
              key={entry.id || index}
              className="flex justify-between items-center py-2 border-b last:border-0"
              data-testid={`bom-entry-${index}`}
            >
              <div>
                <div className="font-medium text-sm">{entry.component_name}</div>
                <div className="text-xs text-gray-500">
                  {entry.quantity} {entry.unit}
                </div>
              </div>
              <div className="text-right">
                <div className="font-medium text-sm">
                  {entry.emissions?.toFixed(2) ?? '0.00'} kg
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
