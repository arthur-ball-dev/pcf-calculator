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
 * - completedByComponent: The step's component marks completion itself; the wizard skips it
 *
 * Updated Phase 9: Replaced ProductSelector with ProductList (Emerald Night 5B)
 */

import ProductList from '@/components/calculator/ProductList';
import BOMEditor from '@/components/forms/BOMEditor';
import ResultsDisplay from '@/components/calculator/ResultsDisplay';
import { useCalculatorStore } from '@/store/calculatorStore';
import type { StepConfig } from '@/types/store.types';

export const WIZARD_STEPS: StepConfig[] = [
  {
    id: 'select',
    label: 'Select Product',
    progressLabel: 'Select Product',
    description: 'Choose a product to calculate its cradle-to-gate carbon footprint',
    component: ProductList,
    validate: async () => {
      // Check if product is selected
      const selectedProductId = useCalculatorStore.getState().selectedProductId;
      return selectedProductId !== null;
    },
  },
  {
    id: 'edit',
    label: 'Edit Bill of Materials',
    progressLabel: 'Edit BOM',
    description: 'Review and modify the Bill of Materials',
    component: BOMEditor,
    // BOMEditor completes the step from its form validation (the full BOM schema, including
    // unique names). A separate wizard check here accepted BOMs the form rejects and raced the
    // editor on entry, so the Calculate button flickered enabled -> disabled -> enabled (#133).
    completedByComponent: true,
  },
  {
    id: 'results',
    label: 'Results',
    progressLabel: 'Results',
    description: 'View carbon footprint results',
    component: ResultsDisplay,
    // No validation needed for final step
  },
];
