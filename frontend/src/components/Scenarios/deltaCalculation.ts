/**
 * Delta Calculation Utilities
 *
 * Utility functions for calculating emissions deltas between scenarios.
 * Used by ScenarioComparison component for comparing PCF calculation scenarios.
 */

export interface DeltaResult {
  scenarioId: string;
  scenarioName: string;
  emissions: number;
  absoluteDelta: number;
  percentageDelta: number;
  direction: 'increase' | 'decrease' | 'same';
}

export interface ScenarioData {
  id: string;
  name: string;
  emissions: number;
}

/**
 * Determines the direction of change based on absolute delta
 */
function getDirection(absoluteDelta: number): 'increase' | 'decrease' | 'same' {
  if (absoluteDelta > 0) return 'increase';
  if (absoluteDelta < 0) return 'decrease';
  return 'same';
}

/**
 * Calculates the delta between baseline and alternative emissions
 *
 * @param baselineEmissions - The baseline emissions value (reference point)
 * @param alternativeEmissions - The alternative scenario emissions
 * @param scenarioId - ID of the alternative scenario
 * @param scenarioName - Name of the alternative scenario
 * @returns DeltaResult containing absolute delta, percentage delta, and direction
 */
export function calculateDelta(
  baselineEmissions: number,
  alternativeEmissions: number,
  scenarioId: string,
  scenarioName: string
): DeltaResult {
  const absoluteDelta = alternativeEmissions - baselineEmissions;

  // Handle division by zero
  let percentageDelta: number;
  if (baselineEmissions === 0) {
    if (alternativeEmissions === 0) {
      percentageDelta = 0;
    } else {
      // When baseline is 0 but alternative is not, return Infinity or 0
      // Using 0 for practical purposes as percentage is meaningless
      percentageDelta = 0;
    }
  } else {
    percentageDelta = (absoluteDelta / baselineEmissions) * 100;
  }

  return {
    scenarioId,
    scenarioName,
    emissions: alternativeEmissions,
    absoluteDelta,
    percentageDelta,
    direction: getDirection(absoluteDelta),
  };
}

/**
 * Calculates deltas for multiple scenarios compared to a baseline
 *
 * @param baselineEmissions - The baseline emissions value (reference point)
 * @param scenarios - Array of scenario data to compare
 * @returns Array of DeltaResult for each scenario
 */
export function calculateDeltas(
  baselineEmissions: number,
  scenarios: ScenarioData[]
): DeltaResult[] {
  return scenarios.map((scenario) =>
    calculateDelta(baselineEmissions, scenario.emissions, scenario.id, scenario.name)
  );
}
