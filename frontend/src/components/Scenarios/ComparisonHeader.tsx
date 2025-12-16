/**
 * ComparisonHeader Component
 *
 * Displays a summary header for scenario comparisons including:
 * - Number of scenarios being compared
 * - Quick summary statistics
 */

import type { Scenario } from '@/store/scenarioStore';
import type { DeltaData } from './DeltaVisualization';

// ================================================================
// Type Definitions
// ================================================================

export interface ComparisonHeaderProps {
  scenarios: Scenario[];
  deltas: DeltaData[] | null;
}

// ================================================================
// Component
// ================================================================

export function ComparisonHeader({ scenarios }: ComparisonHeaderProps) {
  // Calculate summary stats
  const totalScenarios = scenarios.length;
  const baseline = scenarios.find((s) => s.isBaseline);
  const baselineEmissions = baseline?.results?.total_emissions ?? 0;

  // Find best and worst scenarios
  const scenariosWithResults = scenarios.filter((s) => s.results !== null);
  const sortedByEmissions = [...scenariosWithResults].sort(
    (a, b) => (a.results?.total_emissions ?? 0) - (b.results?.total_emissions ?? 0)
  );

  const bestScenario = sortedByEmissions[0];
  const worstScenario = sortedByEmissions[sortedByEmissions.length - 1];

  return (
    <div className="bg-gray-50 border-b px-4 py-3" data-testid="comparison-header">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Scenario Comparison</h2>
          <p className="text-sm text-gray-500">
            Comparing {totalScenarios} scenario{totalScenarios !== 1 ? 's' : ''}
            {baseline && ` against "${baseline.name}"`}
          </p>
        </div>

        {scenariosWithResults.length > 1 && (
          <div className="flex gap-6">
            {/* Best scenario summary */}
            {bestScenario && bestScenario.id !== baseline?.id && (
              <div className="text-right">
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  Lowest Emissions
                </div>
                <div className="text-sm font-medium text-green-600">
                  {bestScenario.name}
                </div>
                <div className="text-xs text-gray-500">
                  {bestScenario.results?.total_emissions.toFixed(1)} kg CO2e
                </div>
              </div>
            )}

            {/* Worst scenario summary */}
            {worstScenario && worstScenario.id !== baseline?.id && worstScenario.id !== bestScenario?.id && (
              <div className="text-right">
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  Highest Emissions
                </div>
                <div className="text-sm font-medium text-red-600">
                  {worstScenario.name}
                </div>
                <div className="text-xs text-gray-500">
                  {worstScenario.results?.total_emissions.toFixed(1)} kg CO2e
                </div>
              </div>
            )}

            {/* Baseline emissions */}
            {baseline && baseline.results && (
              <div className="text-right">
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  Baseline
                </div>
                <div className="text-sm font-medium text-blue-600">
                  {baseline.name}
                </div>
                <div className="text-xs text-gray-500">
                  {baselineEmissions.toFixed(1)} kg CO2e
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
