/**
 * Wizard Steps Configuration
 *
 * Defines the 3-step wizard flow for the PCF Calculator:
 * 1. Select Product - Choose product for calculation
 * 2. Edit BOM - Review and modify Bill of Materials
 * 3. Results - View calculation results
 *
 * Note: Calculation now happens automatically when advancing from BOM step
 * via the CalculationOverlay modal.
 *
 * Each step includes:
 * - id: Unique identifier matching WizardStep type
 * - label: Display name
 * - description: Help text shown below heading
 * - component: React component to render for this step
 * - validate: Optional async function to check step completion
 */

import ProductSelector from '@/components/calculator/ProductSelector';
import BOMEditor from '@/components/forms/BOMEditor';
import ResultsDisplay from '@/components/calculator/ResultsDisplay';
import { useCalculatorStore } from '@/store/calculatorStore';
import type { StepConfig } from '@/types/store.types';

export const WIZARD_STEPS: StepConfig[] = [
  {
    id: 'select',
    label: 'Step 1: Select Product',
    progressLabel: 'Select Product',
    description: 'Choose a product to calculate its carbon footprint',
    component: ProductSelector,
    validate: async () => {
      // Check if product is selected
      const selectedProductId = useCalculatorStore.getState().selectedProductId;
      return selectedProductId !== null;
    },
  },
  {
    id: 'edit',
    label: 'Step 2: Edit Bill of Materials (BOM)',
    progressLabel: 'Edit BOM',
    description: 'Review and modify the Bill of Materials',
    component: BOMEditor,
    validate: async () => {
      // Check if BOM has at least one valid item
      const bomItems = useCalculatorStore.getState().bomItems;
      return (
        bomItems.length > 0 &&
        bomItems.every((item) => item.name && item.quantity > 0)
      );
    },
  },
  {
    id: 'results',
    label: 'Step 3: Results',
    progressLabel: 'Results',
    description: 'View carbon footprint results',
    component: ResultsDisplay,
    // No validation needed for final step
  },
];
