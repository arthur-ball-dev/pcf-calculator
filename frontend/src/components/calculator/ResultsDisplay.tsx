/**
 * ResultsDisplay Component
 *
 * Final step (Step 4) of the wizard showing calculation results:
 * - ResultsSummary: Total CO2e with timestamp
 * - SankeyDiagram: Visual flow of emissions
 * - BreakdownTable: Detailed category breakdown
 * - Action buttons: New Calculation, Export (CSV/Excel)
 *
 * TASK-FE-009: Results Dashboard Implementation
 * TASK-FE-P5-011: Integrated ExportButton component for CSV/Excel export
 */

import { useWizardStore } from '../../store/wizardStore';
import { useCalculatorStore } from '../../store/calculatorStore';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import ResultsSummary from './ResultsSummary';
import BreakdownTable from './BreakdownTable';
import SankeyDiagram from '../visualizations/SankeyDiagram';
import { ExportButton } from '../ExportButton';

/**
 * ResultsDisplay Component
 *
 * Displays calculation results with summary, visualization, and detailed breakdown.
 * Provides actions to start new calculation or export data.
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
    <div className="space-y-8" data-testid="results-display">
      {/* Summary Card */}
      <ResultsSummary
        totalCO2e={calculation.total_co2e_kg || 0}
        unit="kg"
        calculatedAt={new Date(calculation.created_at || new Date().toISOString())}
      />

      {/* Sankey Diagram */}
      <Card data-tour="visualization-tabs">
        <CardHeader>
          <CardTitle>Carbon Flow Visualization</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="min-h-[400px]">
            <SankeyDiagram calculation={calculation} />
          </div>
        </CardContent>
      </Card>

      {/* Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <BreakdownTable
            totalCO2e={calculation.total_co2e_kg || 0}
            materialsCO2e={calculation.materials_co2e}
            energyCO2e={calculation.energy_co2e}
            transportCO2e={calculation.transport_co2e}
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
