/**
 * Scenarios Components
 *
 * Components for scenario comparison and visualization in the PCF Calculator.
 */

export { ScenarioComparison, type ScenarioComparisonProps } from './ScenarioComparison';
export { ScenarioPanel, type ScenarioPanelProps, type ComparisonDelta } from './ScenarioPanel';
export { DeltaVisualization, type DeltaVisualizationProps, type DeltaData } from './DeltaVisualization';
export { ComparisonHeader, type ComparisonHeaderProps } from './ComparisonHeader';
export { calculateDelta, calculateDeltas, type DeltaResult, type ScenarioData } from './deltaCalculation';
