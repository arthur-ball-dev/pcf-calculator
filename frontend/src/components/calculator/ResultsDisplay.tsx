/**
 * ResultsDisplay Component
 *
 * Final step (Step 4) of the wizard showing calculation results:
 * - ResultsSummary: Total CO2e with timestamp
 * - SankeyDiagram: Visual flow of emissions
 * - BreakdownTable: Detailed category breakdown
 * - Action buttons: New Calculation, CSV Export (future)
 *
 * TASK-FE-009: Results Dashboard Implementation
 */

import React from 'react';
import { useWizardStore } from '../../store/wizardStore';
import { useCalculatorStore } from '../../store/calculatorStore';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import ResultsSummary from './ResultsSummary';
import BreakdownTable from './BreakdownTable';
import SankeyDiagram from '../visualizations/SankeyDiagram';

/**
 * ResultsDisplay Component
 *
 * Displays calculation results with summary, visualization, and detailed breakdown.
 * Provides actions to start new calculation or export data.
 */
export default function ResultsDisplay() {
  const { reset: resetWizard } = useWizardStore();
  const { calculation, reset: resetCalculator } = useCalculatorStore();

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

  return (
    <div className="space-y-8" data-testid="results-display">
      {/* Summary Card */}
      <ResultsSummary
        totalCO2e={calculation.total_co2e_kg || 0}
        unit="kg"
        calculatedAt={new Date(calculation.created_at || new Date().toISOString())}
      />

      {/* Sankey Diagram */}
      <Card>
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
      <div className="flex gap-4">
        <Button onClick={handleNewCalculation} variant="outline" data-testid="new-calculation-action-button">
          New Calculation
        </Button>
        <Button variant="outline" disabled>
          Export CSV (Coming Soon)
        </Button>
      </div>
    </div>
  );
}
