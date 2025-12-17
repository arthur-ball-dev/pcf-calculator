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
  const { calculation, selectedProduct, bomItems, reset: resetCalculator } = useCalculatorStore();

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
  const totalCO2e = calculation.total_co2e_kg || 0;

  // Build category breakdown from individual category values (without Scope for cleaner export)
  const categoryBreakdown = [
    {
      scope: 'Scope 3',
      category: 'Materials',
      emissions: calculation.materials_co2e || 0,
      percentage: totalCO2e > 0 ? ((calculation.materials_co2e || 0) / totalCO2e) * 100 : 0,
    },
    {
      scope: 'Scope 2',
      category: 'Energy',
      emissions: calculation.energy_co2e || 0,
      percentage: totalCO2e > 0 ? ((calculation.energy_co2e || 0) / totalCO2e) * 100 : 0,
    },
    {
      scope: 'Scope 3',
      category: 'Transport',
      emissions: calculation.transport_co2e || 0,
      percentage: totalCO2e > 0 ? ((calculation.transport_co2e || 0) / totalCO2e) * 100 : 0,
    },
  ].filter(item => item.emissions > 0);

  // Build BOM details with emission values from breakdown
  // Use normalized lookup since breakdown keys may have different casing/formatting
  // e.g., breakdown has "transport_ship" but BOM has "Transport Ship"
  const breakdown = calculation.breakdown || {};

  // Normalize string for comparison: lowercase, replace spaces/underscores/hyphens
  const normalize = (s: string) => s.toLowerCase().replace(/[\s_-]+/g, '');

  const bomDetails = bomItems.map(item => {
    // Try exact match first
    let emissions = breakdown[item.name];
    if (emissions === undefined) {
      // Normalized lookup - handles case, spaces, underscores, hyphens
      const normalizedName = normalize(item.name);
      const key = Object.keys(breakdown).find(
        k => normalize(k) === normalizedName
      );
      emissions = key ? breakdown[key] : 0;
    }
    // Calculate emission factor from emissions and quantity
    const emissionFactor = item.quantity > 0 ? emissions / item.quantity : 0;
    return {
      component_name: item.name,
      category: item.category,
      quantity: item.quantity,
      unit: item.unit,
      emission_factor: emissionFactor,
      emissions: emissions,
    };
  });

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
    category_breakdown: categoryBreakdown,
    bom_details: bomDetails,
  };

  return (
    <div className="space-y-8 bg-background" data-testid="results-display">
      {/* Summary Card */}
      <ResultsSummary
        totalCO2e={calculation.total_co2e_kg || 0}
        unit="kg"
        calculatedAt={new Date(calculation.created_at || new Date().toISOString())}
      />

      {/* Two-column layout: Sankey left, Breakdown right */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sankey Diagram with in-chart drill-down */}
        <Card data-tour="visualization-tabs" className="bg-card overflow-hidden">
          <CardHeader>
            <CardTitle>Carbon Flow: {selectedProduct?.name || 'Product'}</CardTitle>
            <CardDescription>
              Click on a category to see detailed breakdown
            </CardDescription>
          </CardHeader>
          <CardContent className="overflow-hidden">
            <div className="h-[400px] w-full">
              <SankeyDiagram calculation={calculation} />
            </div>
          </CardContent>
        </Card>

        {/* Breakdown Table with expandable items */}
        <Card className="bg-card overflow-hidden">
          <CardHeader>
            <CardTitle>Detailed Breakdown: {selectedProduct?.name || 'Product'}</CardTitle>
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
      </div>

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