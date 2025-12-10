/**
 * DeltaVisualization Component
 *
 * Displays a horizontal bar chart showing emissions comparison between scenarios.
 * Features:
 * - Bar widths proportional to emissions values
 * - Color-coded bars based on direction (red=increase, green=decrease, blue=same)
 * - Accessible with ARIA attributes
 * - Labels showing scenario names and emissions values
 */

import { Card, CardContent } from '@/components/ui/card';

// ================================================================
// Type Definitions
// ================================================================

export interface DeltaData {
  scenarioId: string;
  scenarioName: string;
  emissions: number;
  absoluteDelta: number;
  percentageDelta: number;
  direction: 'increase' | 'decrease' | 'same';
}

export interface DeltaVisualizationProps {
  deltas: DeltaData[];
}

// ================================================================
// Helper Functions
// ================================================================

function getBarColor(direction: string): string {
  if (direction === 'increase') return 'bg-red-400';
  if (direction === 'decrease') return 'bg-green-400';
  return 'bg-blue-400';
}

// ================================================================
// Component
// ================================================================

export function DeltaVisualization({ deltas }: DeltaVisualizationProps) {
  // Calculate max emissions for scaling bars
  // Use 1 as minimum to avoid division by zero
  const maxEmissions = Math.max(...deltas.map((d) => d.emissions), 1);

  return (
    <Card className="mt-4" data-testid="delta-visualization">
      <CardContent className="pt-4">
        <h4 className="text-sm font-medium mb-3">Emissions Comparison</h4>
        <div className="space-y-3" data-testid="bars-container">
          {deltas.map((delta) => {
            const widthPercent = (delta.emissions / maxEmissions) * 100;

            return (
              <div
                key={delta.scenarioId}
                className="flex items-center gap-3"
                data-testid={`bar-row-${delta.scenarioId}`}
              >
                <div
                  className="w-32 text-sm truncate"
                  data-testid={`scenario-label-${delta.scenarioId}`}
                >
                  {delta.scenarioName}
                </div>
                <div
                  className="flex-1 h-6 bg-gray-100 rounded-full overflow-hidden"
                  data-testid={`bar-track-${delta.scenarioId}`}
                  style={{ width: '100%' }}
                >
                  <div
                    className={`h-full transition-all duration-500 ${getBarColor(delta.direction)}`}
                    data-testid={`bar-fill-${delta.scenarioId}`}
                    style={{ width: `${widthPercent}%` }}
                    role="progressbar"
                    aria-valuenow={delta.emissions}
                    aria-valuemin={0}
                    aria-valuemax={maxEmissions}
                    aria-label={`${delta.scenarioName}: ${delta.emissions} kg CO2e`}
                  />
                </div>
                <div
                  className="w-24 text-sm text-right font-medium"
                  data-testid={`emissions-value-${delta.scenarioId}`}
                >
                  {delta.emissions.toFixed(1)} kg
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
