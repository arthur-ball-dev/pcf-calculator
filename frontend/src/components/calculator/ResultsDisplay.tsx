/**
 * ResultsDisplay Component
 *
 * Final step (Step 3) of the wizard showing calculation results.
 * Emerald Night 5B vertical stack layout:
 * 1. ResultsHero - Large PCF value with radial glow and rating badges
 * 2. Sankey section - Full-width glassmorphic card with "Carbon Flow Analysis" header
 * 3. Breakdown section - Full-width glassmorphic card with "Emission Breakdown" header
 * 4. Export row - Horizontal button row (New Calculation, CSV, Excel)
 * 5. LicenseFooter - Data source attribution
 *
 * Design Source: frontend/prototypes/approach-5b-single-card/03-results.html
 *
 * Note: Disclaimer and ResultsDataCallout are removed from this component
 * because the InfoSection in the wizard shell already handles disclaimer
 * and attribution display at the page level.
 *
 * TASK-FE-009: Results Dashboard Implementation
 * TASK-FE-P5-011: Integrated ExportButton component for CSV/Excel export
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization
 * TASK-FE-P8-003: Pass breakdown data to BreakdownTable for expandable items
 * TASK-FE-P8-006: Wire LicenseFooter into ResultsDisplay
 * Emerald Night 5B Rebuild: Vertical stack, hero section, glass cards
 */

import { useWizardStore } from '../../store/wizardStore';
import { useCalculatorStore } from '../../store/calculatorStore';
import { Button } from '../ui/button';
import ResultsHero from './ResultsHero';
import BreakdownTable from './BreakdownTable';
import SankeyDiagram from '../visualizations/SankeyDiagram';
import { ExportButton } from '../ExportButton';
import { LicenseFooter } from '../attribution/LicenseFooter';
import { classifyComponent } from '../../utils/classifyComponent';
import { RotateCcw } from 'lucide-react';

/**
 * ResultsDisplay Component
 *
 * Displays calculation results with hero summary, visualization, and detailed breakdown.
 * Provides actions to start new calculation or export data.
 * Sankey diagram supports in-chart drill-down when clicking on category nodes.
 * Includes LicenseFooter for data source attribution.
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
  const totalCO2e = calculation.total_co2e_kg || 0;

  // Calculate category totals from breakdown items for consistent classification
  const breakdown = calculation.breakdown || {};
  const categoryTotals = { materials: 0, energy: 0, transport: 0, combustion: 0, other: 0 };

  if (Object.keys(breakdown).length > 0) {
    Object.entries(breakdown).forEach(([componentName, co2e]) => {
      const category = classifyComponent(componentName);
      categoryTotals[category] += co2e;
    });
  } else {
    categoryTotals.materials = calculation.materials_co2e || 0;
    categoryTotals.energy = calculation.energy_co2e || 0;
    categoryTotals.transport = calculation.transport_co2e || 0;
  }

  // Build category breakdown with consistent totals
  const categoryBreakdown = [
    {
      scope: 'Scope 3',
      category: 'Materials',
      emissions: categoryTotals.materials,
      percentage: totalCO2e > 0 ? (categoryTotals.materials / totalCO2e) * 100 : 0,
    },
    {
      scope: 'Scope 2',
      category: 'Energy',
      emissions: categoryTotals.energy,
      percentage: totalCO2e > 0 ? (categoryTotals.energy / totalCO2e) * 100 : 0,
    },
    {
      scope: 'Scope 3',
      category: 'Transport',
      emissions: categoryTotals.transport,
      percentage: totalCO2e > 0 ? (categoryTotals.transport / totalCO2e) * 100 : 0,
    },
    {
      scope: 'Scope 1',
      category: 'Combustion',
      emissions: categoryTotals.combustion,
      percentage: totalCO2e > 0 ? (categoryTotals.combustion / totalCO2e) * 100 : 0,
    },
    {
      scope: 'Scope 3',
      category: 'Processing/Other',
      emissions: categoryTotals.other,
      percentage: totalCO2e > 0 ? (categoryTotals.other / totalCO2e) * 100 : 0,
    },
  ].filter(item => item.emissions > 0);

  // Build BOM details with emission values from breakdown
  const normalize = (s: string) => s.toLowerCase().replace(/[\s_-]+/g, '');

  const bomDetails = bomItems.map(item => {
    let emissions = breakdown[item.name];
    if (emissions === undefined) {
      const normalizedName = normalize(item.name);
      const key = Object.keys(breakdown).find(
        k => normalize(k) === normalizedName
      );
      emissions = key ? breakdown[key] : 0;
    }
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

  // Derive a simple data quality rating from available data
  // If we have breakdown data, that's higher quality than just totals
  const dataQualityRating = Object.keys(breakdown).length > 0 ? 3.5 : 2.5;

  return (
    <div className="space-y-10" data-testid="results-display">
      {/* 1. Hero Section - Large PCF value with badges */}
      <ResultsHero
        totalCO2e={totalCO2e}
        dataQualityRating={dataQualityRating}
        componentCount={bomItems.length}
        productName={selectedProduct?.name || 'Product'}
      />

      {/* 2. Sankey Diagram Section - Full-width glass card */}
      <section
        data-tour="visualization-tabs"
        className="glass-card p-4 sm:p-6 animate-fadeInUp"
        style={{ animationDelay: '0.1s' }}
      >
        <div className="mb-5">
          <h3 className="font-heading text-lg font-semibold text-[var(--text-primary)]">
            Carbon Flow Analysis
          </h3>
          <p className="text-[0.8125rem] text-[var(--text-dim)] mt-1">
            Emission flow from BOM components through categories to total PCF
          </p>
        </div>
        <SankeyDiagram calculation={calculation} />
      </section>

      {/* 3. Breakdown Table Section - Full-width glass card */}
      <section
        className="glass-card overflow-hidden animate-fadeInUp"
        style={{ animationDelay: '0.2s' }}
      >
        <div className="px-6 py-5 border-b border-[var(--card-border)]">
          <h3 className="font-heading text-base font-semibold text-[var(--text-primary)]">
            Category Breakdown
          </h3>
        </div>
        <BreakdownTable
          totalCO2e={calculation.total_co2e_kg || 0}
          materialsCO2e={calculation.materials_co2e}
          energyCO2e={calculation.energy_co2e}
          transportCO2e={calculation.transport_co2e}
          breakdown={calculation.breakdown}
        />
      </section>

      {/* 4. Export Row - Horizontal button row */}
      <div
        className="flex flex-col sm:flex-row flex-wrap items-stretch sm:items-center gap-3 animate-fadeInUp"
        style={{ animationDelay: '0.3s' }}
        data-tour="export-buttons"
      >
        <ExportButton
          results={exportResults}
          productName={selectedProduct?.name || 'Unknown Product'}
          productCode={selectedProduct?.code || 'UNKNOWN'}
        />
        <div className="flex-1" />
        <Button
          onClick={handleNewCalculation}
          variant="outline"
          data-testid="new-calculation-action-button"
          className="border-[var(--card-border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-white/[0.03]"
        >
          <RotateCcw className="w-4 h-4 mr-2" />
          New Calculation
        </Button>
      </div>

      {/* 5. License Footer for attribution compliance */}
      <LicenseFooter className="mt-8" />
    </div>
  );
}
