/**
 * Integration Tests - Complete Wizard Workflow
 * TASK-FE-011: Frontend Integration Testing
 *
 * Test-Driven Development (TDD Protocol)
 * Written BEFORE any workflow modifications
 *
 * Test Scenarios:
 * 1. Complete PCF Calculation Workflow (Step 1 → 2 → 3 → 4)
 * 2. State Persistence Across Steps
 * 3. Navigation Guards and Validation
 * 4. Error Handling and Recovery
 * 5. Cross-Component Interactions
 * 6. Store Synchronization
 *
 * This is the FINAL integration test for Phase 3.
 * Validates end-to-end functionality of the entire calculator application.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { screen, waitFor, within } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { render } from '../testUtils';
import { server } from '../../__mocks__/server';
import { rest } from 'msw';
import CalculationWizard from '../../src/components/calculator/CalculationWizard';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';

describe('Integration: Complete Wizard Workflow', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset all stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();

    // Clear all mocks
    vi.clearAllMocks();
  });

  describe('Scenario 1: Complete PCF Calculation Workflow', () => {
    test('completes full workflow from product selection to results', async () => {
      render(<CalculationWizard />);

      // =====================================================================
      // STEP 1: Select Product
      // =====================================================================

      // Wait for wizard to load on Step 1
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
      });

      // Verify we're on step 1
      expect(useWizardStore.getState().currentStep).toBe('select');

      // Verify Next button is disabled (no product selected)
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      // Wait for products to load (from MSW)
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      // Select a product by clicking on it
      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      // Verify product selected in store
      await waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.selectedProductId).toBe('prod-001');
      });

      // Verify step marked complete
      expect(useWizardStore.getState().isStepComplete('select')).toBe(true);

      // Verify Next button is enabled
      expect(nextButton).toBeEnabled();

      // Click Next to go to Step 2
      await user.click(nextButton);

      // =====================================================================
      // STEP 2: Edit BOM
      // =====================================================================

      // Verify we're on Step 2
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /edit.*bom/i })).toBeInTheDocument();
      });

      expect(useWizardStore.getState().currentStep).toBe('edit');

      // Wait for BOM to load
      await waitFor(() => {
        expect(screen.getByText(/organic cotton fabric/i)).toBeInTheDocument();
      });

      // Verify BOM items loaded
      const state = useCalculatorStore.getState();
      expect(state.bomItems.length).toBeGreaterThan(0);

      // Optionally edit a quantity (modify first component)
      const quantityInputs = screen.getAllByRole('spinbutton');
      if (quantityInputs.length > 0) {
        await user.clear(quantityInputs[0]);
        await user.type(quantityInputs[0], '0.75');
      }

      // Verify BOM is valid
      await waitFor(() => {
        expect(useCalculatorStore.getState().isValid).toBe(true);
      });

      // Click Next to go to Step 3
      const nextButtonStep2 = screen.getByRole('button', { name: /next/i });
      await user.click(nextButtonStep2);

      // =====================================================================
      // STEP 3: Calculate
      // =====================================================================

      // Verify we're on Step 3
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /calculate/i })).toBeInTheDocument();
      });

      expect(useWizardStore.getState().currentStep).toBe('calculate');

      // Find and click the Calculate button
      const calculateButton = screen.getByRole('button', { name: /calculate pcf/i });
      expect(calculateButton).toBeInTheDocument();
      expect(calculateButton).toBeEnabled();

      await user.click(calculateButton);

      // =====================================================================
      // STEP 4: Results (Auto-advance after calculation completes)
      // =====================================================================

      // Wait for calculation to complete and auto-advance to results
      await waitFor(
        () => {
          expect(screen.getByRole('heading', { name: /results/i })).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Verify we're on Step 4
      expect(useWizardStore.getState().currentStep).toBe('results');

      // Verify results are displayed
      await waitFor(() => {
        // Total emissions should be visible
        expect(screen.getByText(/kg co₂e/i)).toBeInTheDocument();
      });

      // Verify calculation completed in store
      const finalState = useCalculatorStore.getState();
      expect(finalState.calculation).toBeTruthy();
      expect(finalState.calculation?.status).toBe('completed');
      expect(finalState.calculation?.total_emissions).toBeGreaterThan(0);

      // Verify all steps marked complete
      expect(useWizardStore.getState().isStepComplete('select')).toBe(true);
      expect(useWizardStore.getState().isStepComplete('edit')).toBe(true);
      expect(useWizardStore.getState().isStepComplete('calculate')).toBe(true);
      expect(useWizardStore.getState().isStepComplete('results')).toBe(true);
    });
  });

  describe('Scenario 2: State Persistence Across Steps', () => {
    test('preserves product selection when navigating back from Step 2', async () => {
      render(<CalculationWizard />);

      // Step 1: Select product
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      await waitFor(() => {
        expect(useCalculatorStore.getState().selectedProductId).toBe('prod-001');
      });

      // Go to Step 2
      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Go back to Step 1
      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('select');
      });

      // Verify product still selected
      expect(useCalculatorStore.getState().selectedProductId).toBe('prod-001');
      expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
    });

    test('preserves BOM edits when navigating back from Step 3', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText(/organic cotton fabric/i)).toBeInTheDocument();
      });

      // Edit quantity
      const quantityInputs = screen.getAllByRole('spinbutton');
      const originalValue = quantityInputs[0].getAttribute('value');
      await user.clear(quantityInputs[0]);
      await user.type(quantityInputs[0], '0.99');

      // Go to Step 3
      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('calculate');
      });

      // Go back to Step 2
      await user.click(screen.getByRole('button', { name: /back/i }));

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Verify edited quantity persisted
      const newQuantityInputs = screen.getAllByRole('spinbutton');
      expect(newQuantityInputs[0].getAttribute('value')).toBe('0.99');
    });
  });

  describe('Scenario 3: Navigation Guards and Validation', () => {
    test('prevents advancing to Step 2 without product selection', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
      });

      // Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      // Try to navigate programmatically
      useWizardStore.getState().setStep('edit');

      // Should remain on select step
      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    test('prevents advancing with invalid BOM data', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText(/organic cotton fabric/i)).toBeInTheDocument();
      });

      // Clear quantity to make invalid
      const quantityInputs = screen.getAllByRole('spinbutton');
      await user.clear(quantityInputs[0]);

      // Wait for validation
      await waitFor(() => {
        expect(useCalculatorStore.getState().isValid).toBe(false);
      });

      // Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });
  });

  describe('Scenario 4: Error Handling and Recovery', () => {
    test('handles product loading error gracefully', async () => {
      // Override MSW to return error
      server.use(
        rest.get('http://localhost:8000/api/v1/products', (req, res, ctx) => {
          return res(
            ctx.status(500),
            ctx.json({
              error: {
                code: 'INTERNAL_SERVER_ERROR',
                message: 'Database connection failed',
              },
            })
          );
        })
      );

      render(<CalculationWizard />);

      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/unable to load data/i)).toBeInTheDocument();
      });
    });

    test('handles calculation failure gracefully', async () => {
      // Override MSW to return failed calculation
      server.use(
        rest.get('http://localhost:8000/api/v1/calculations/:id', (req, res, ctx) => {
          return res(
            ctx.status(200),
            ctx.json({
              calculation_id: 'calc-123',
              status: 'failed',
              error_message: 'Invalid emission factors',
            })
          );
        })
      );

      render(<CalculationWizard />);

      // Navigate through steps
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText(/organic cotton fabric/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /next/i }));

      // Click Calculate
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /calculate pcf/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /calculate pcf/i }));

      // Should display error
      await waitFor(
        () => {
          expect(screen.getByText(/invalid emission factors/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Should remain on calculate step
      expect(useWizardStore.getState().currentStep).toBe('calculate');
    });
  });

  describe('Scenario 5: Cross-Component Interactions', () => {
    test('wizard progress updates as steps complete', async () => {
      render(<CalculationWizard />);

      // Initially on step 1
      await waitFor(() => {
        const step1Indicator = screen.getByLabelText(/select product.*step 1/i);
        expect(step1Indicator).toHaveAttribute('aria-current', 'step');
      });

      // Select product
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      // Move to step 2
      await user.click(screen.getByRole('button', { name: /next/i }));

      // Progress should update
      await waitFor(() => {
        const step2Indicator = screen.getByLabelText(/edit bom.*step 2/i);
        expect(step2Indicator).toHaveAttribute('aria-current', 'step');
      });
    });
  });

  describe('Scenario 6: Store Synchronization', () => {
    test('wizard store and calculator store stay synchronized', async () => {
      render(<CalculationWizard />);

      // Select product
      await waitFor(() => {
        expect(screen.getByText(/cotton t-shirt/i)).toBeInTheDocument();
      });

      const productCard = screen.getByText(/cotton t-shirt/i).closest('div');
      if (productCard) {
        await user.click(productCard);
      }

      // Verify synchronization
      await waitFor(() => {
        expect(useCalculatorStore.getState().selectedProductId).toBe('prod-001');
        expect(useWizardStore.getState().isStepComplete('select')).toBe(true);
      });

      // Move to step 2
      await user.click(screen.getByRole('button', { name: /next/i }));

      // Verify step synchronized
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
        expect(useCalculatorStore.getState().bomItems.length).toBeGreaterThan(0);
      });
    });
  });
});
