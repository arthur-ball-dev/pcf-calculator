/**
 * Tour Steps Configuration
 *
 * TASK-UI-P5-002: Guided Tour Onboarding - Step Definitions
 *
 * Defines the 8 tour steps for the PCF Calculator guided tour.
 * Each step targets a specific element with data-tour attribute
 * and provides contextual help for that feature.
 *
 * Steps:
 * 1. Product Selection - Choose a product to calculate
 * 2. Bill of Materials - Review and edit BOM items
 * 3. Calculate - Run PCF calculation
 * 4. View Results - See carbon footprint results
 * 5. Visualizations - Explore charts and graphs
 * 6. Export - Download results
 * 7. Scenario Comparison - Compare different scenarios
 */

import type { Step } from 'react-joyride';

/**
 * Step IDs corresponding to data-tour attributes
 */
export const TOUR_STEP_IDS = [
  'product-select',
  'bom-table',
  'calculate-button',
  'results-summary',
  'visualization-tabs',
  'export-buttons',
  'scenario-compare',
] as const;

export type TourStepId = (typeof TOUR_STEP_IDS)[number];

/**
 * Step content component for consistent styling
 */
interface StepContentProps {
  title: string;
  description: string;
}

function StepContent({ title, description }: StepContentProps) {
  return (
    <div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

/**
 * Tour steps configuration for react-joyride
 * Each step includes:
 * - target: CSS selector for the element to highlight
 * - content: React content to display in tooltip
 * - placement: Position of tooltip relative to target
 * - disableBeacon: Whether to show pulsing beacon (disabled on first step)
 */
export const TOUR_STEPS: Step[] = [
  {
    target: '[data-tour="product-select"]',
    content: (
      <StepContent
        title="Step 1: Select a Product"
        description="Start by searching for and selecting the product you want to calculate the carbon footprint for. You can search by name or product code."
      />
    ),
    placement: 'bottom',
    disableBeacon: true,
  },
  {
    target: '[data-tour="bom-table"]',
    content: (
      <StepContent
        title="Step 2: Review Bill of Materials"
        description="Review and modify the Bill of Materials. You can edit quantities, add new components, or remove items to customize your calculation."
      />
    ),
    placement: 'top',
    disableBeacon: true,
  },
  {
    target: '[data-tour="calculate-button"]',
    content: (
      <StepContent
        title="Step 3: Calculate"
        description="Click Calculate to run the PCF calculation. This uses emission factors from EPA and DEFRA databases to compute the carbon footprint."
      />
    ),
    placement: 'top',
    disableBeacon: true,
  },
  {
    target: '[data-tour="results-summary"]',
    content: (
      <StepContent
        title="Step 4: View Results"
        description="View your product's total carbon footprint in kg CO2 equivalent. The breakdown shows contributions from each material and process."
      />
    ),
    placement: 'left',
    disableBeacon: true,
  },
  {
    target: '[data-tour="visualization-tabs"]',
    content: (
      <StepContent
        title="Explore Visualizations"
        description="The Sankey diagram shows how emissions flow from materials and processes to the total carbon footprint. The breakdown table lets you drill into each category."
      />
    ),
    placement: 'bottom',
    disableBeacon: true,
  },
  {
    target: '[data-tour="export-buttons"]',
    content: (
      <StepContent
        title="Export Results"
        description="Download your results in CSV or Excel format for reporting, analysis, or sharing with stakeholders."
      />
    ),
    placement: 'left',
    disableBeacon: true,
  },
  {
    target: '[data-tour="scenario-compare"]',
    content: (
      <StepContent
        title="Compare Scenarios"
        description="Compare how changes in materials impact the carbon footprint. Save different scenarios and see side-by-side comparisons."
      />
    ),
    placement: 'bottom',
    disableBeacon: true,
  },
];
