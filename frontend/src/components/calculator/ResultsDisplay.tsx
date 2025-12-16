/**
 * ResultsDisplay Component
 *
 * Final step (Step 4) of the wizard showing calculation results:
 * - ResultsSummary: Total CO2e with timestamp
 * - SankeyDiagram: Visual flow of emissions with in-chart drill-down
 * - BreakdownTable: Detailed category breakdown with expandable items
 * - Action buttons: New Calculation, Export (CSV/Excel)
 *
 * TASK-FE-009: Results Dashboard Implementation
 * TASK-FE-P5-011: Integrated ExportButton component for CSV/Excel export
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization (in-chart expansion)
 * TASK-FE-P8-003: Pass breakdown data to BreakdownTable for expandable items
 */

import { useWizardStore } from '../../store/wizardStore';
import { useCalculatorStore } from '../../store/calculatorStore';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import ResultsSummary from './ResultsSummary';
import BreakdownTable from './BreakdownTable';
import SankeyDiagram from '../visualizations/SankeyDiagram';
import { ExportButton } from '../ExportButton';

/**
 * ResultsDisplay Component
 *
 * Displays calculation results with summary, visualization, and detailed breakdown.
 * Provides actions to start new calculation or export data.
 * Sankey diagram supports in-chart drill-down when clicking on category nodes.
 */
export default function ResultsDisplay() {
  const { reset: resetWizard } = useWizardStore();
  const { calculation, selectedProduct, reset: resetCalculator } = useCalculatorStore();

  /**
   * Handle New Calculation button click
   * Resets both wizard and calculator stores to start fresh
   */
  const handleNewCalculation = () => {
    resetWizard();
    resetCalculator();
  };

  // Show empty state if no calculation available
  if (!calculation || calculation.status !== 'completed') {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-muted-foreground">
        No calculation results available.
      </div>
    );
  }

  // Prepare calculation results for export
  // Map the Calculation type to the expected CalculationStatusResponse format
  const exportResults = {
    calculation_id: calculation.id,
    status: calculation.status,
    product_id: calculation.product_id ?? null,
    created_at: calculation.created_at ?? null,
    total_co2e_kg: calculation.total_co2e_kg,
    materials_co2e: calculation.materials_co2e,
    energy_co2e: calculation.energy_co2e,
    transport_co2e: calculation.transport_co2e,
    calculation_time_ms: calculation.calculation_time_ms,
  };

  return (
    <div className="space-y-8 bg-background" data-testid="results-display">
      {/* Summary Card */}
      <ResultsSummary
        totalCO2e={calculation.total_co2e_kg || 0}
        unit="kg"
        calculatedAt={new Date(calculation.created_at || new Date().toISOString())}
      />

      {/* Sankey Diagram with in-chart drill-down */}
      <Card data-tour="visualization-tabs" className="bg-card">
        <CardHeader>
          <CardTitle>Carbon Flow Visualization</CardTitle>
          <CardDescription>
            Click on a category to see detailed breakdown
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="min-h-[400px]">
            <SankeyDiagram calculation={calculation} />
          </div>
        </CardContent>
      </Card>

      {/* Breakdown Table with expandable items */}
      <Card className="bg-card">
        <CardHeader>
          <CardTitle>Detailed Breakdown</CardTitle>
          <CardDescription>
            Click on a category to expand and see individual items
          </CardDescription>
        </CardHeader>
        <CardContent>
          <BreakdownTable
            totalCO2e={calculation.total_co2e_kg || 0}
            materialsCO2e={calculation.materials_co2e}
            energyCO2e={calculation.energy_co2e}
            transportCO2e={calculation.transport_co2e}
            breakdown={calculation.breakdown}
          />
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex flex-wrap gap-4 items-start" data-tour="export-buttons">
        <Button onClick={handleNewCalculation} variant="outline" data-testid="new-calculation-action-button">
          New Calculation
        </Button>
        <ExportButton
          results={exportResults}
          productName={selectedProduct?.name || 'Unknown Product'}
          productCode={selectedProduct?.code || 'UNKNOWN'}
        />
      </div>
    </div>
  );
}