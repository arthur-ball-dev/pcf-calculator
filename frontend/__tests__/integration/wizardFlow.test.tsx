/**
 * Integration Tests - Complete Wizard Workflow
 * TASK-FE-011: Frontend Integration Testing
 *
 * Test Scenarios:
 * 1. Complete PCF Calculation Workflow (Step 1 -> 2 -> 3)
 * 2. State Persistence Across Steps
 * 3. Navigation Guards and Validation
 * 4. Error Handling and Recovery
 * 5. Cross-Component Interactions
 * 6. Store Synchronization
 *
 * UPDATED for Emerald Night UI rebuild:
 * - ProductSelector replaced by ProductList (full-page list, no combobox/dropdown)
 * - ProductList uses productsAPI.search (not productsAPI.list)
 * - Products are rendered as clickable rows with data-testid="product-row-{id}"
 * - BOM filter is a toggle switch with data-testid="bom-toggle-switch"
 * - Search input has data-testid="product-search-input"
 * - Loading skeleton has data-testid="product-list-skeleton"
 * - StepProgress buttons have aria-label="Step N of 3: Label (current/completed)"
 * - ResultsHero replaces ResultsSummary
 * - WizardNavigation buttons: data-testid="next-button" and "previous-button"
 * - On edit step, Next button text is "Calculate" (aria-label="Calculate carbon footprint")
 *
 * NOTE: Uses fireEvent instead of userEvent to avoid JSDOM event loop
 * accumulation causing test timeouts in heavy integration scenarios.
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '../testUtils';
import { server } from '../../__mocks__/server';
import { rest } from 'msw';
import CalculationWizard from '../../src/components/calculator/CalculationWizard';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';

// Mock product data for search endpoint (matches getById mock for prod-001)
const mockSearchProducts = [
  {
    id: 'prod-001',
    code: 'TSHIRT-001',
    name: 'Cotton T-Shirt',
    category: 'apparel',
    unit: 'unit',
    is_finished_product: true,
    created_at: '2024-01-01T00:00:00Z',
    bom_count: 4,
  },
  {
    id: 'prod-002',
    code: 'BOTTLE-001',
    name: 'Water Bottle (500ml)',
    category: 'other',
    unit: 'unit',
    is_finished_product: true,
    created_at: '2024-01-01T00:00:00Z',
    bom_count: 2,
  },
];

// Integration tests render full wizard with MSW + progressive rendering.
// Extended timeout for all tests in this suite.
describe('Integration: Complete Wizard Workflow', { timeout: 30000 }, () => {
  beforeEach(async () => {
    // Clear localStorage FIRST to prevent persist rehydration
    localStorage.clear();

    // Reset all stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();

    // Clear all mocks
    vi.clearAllMocks();

    // Override MSW product search to return consistent test data
    server.use(
      rest.get('http://localhost:8000/api/v1/products/search', (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            items: mockSearchProducts,
            total: mockSearchProducts.length,
            limit: 50,
            offset: 0,
            has_more: false,
          })
        );
      })
    );

    // Wait a tick for persist middleware to settle
    await new Promise((resolve) => setTimeout(resolve, 0));
  });

  /**
   * Helper: Get Next button via data-testid (reliable across all steps).
   */
  function getNextButton() {
    return screen.getByTestId('next-button');
  }

  /**
   * Helper: Get Previous button via data-testid.
   */
  function getPreviousButton() {
    return screen.getByTestId('previous-button');
  }

  /**
   * Helper: Wait for products to load and select Cotton T-Shirt.
   */
  async function selectProduct() {
    await waitFor(() => {
      expect(screen.getByText('Cotton T-Shirt')).toBeInTheDocument();
    }, { timeout: 10000 });

    fireEvent.click(screen.getByText('Cotton T-Shirt'));

    await waitFor(() => {
      expect(useCalculatorStore.getState().selectedProductId).toBe('prod-001');
    });
  }

  /**
   * Helper: Navigate from Step 1 to Step 2 (select product + click Next).
   */
  async function navigateToStep2() {
    await selectProduct();

    await waitFor(() => {
      expect(getNextButton()).toBeEnabled();
    }, { timeout: 10000 });

    fireEvent.click(getNextButton());

    await waitFor(() => {
      expect(useWizardStore.getState().currentStep).toBe('edit');
    }, { timeout: 10000 });
  }

  describe('Scenario 1: Complete PCF Calculation Workflow', () => {
    test('completes full workflow from product selection to results', async () => {
      render(<CalculationWizard />);

      // STEP 1: Select Product
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
      });

      expect(useWizardStore.getState().currentStep).toBe('select');
      expect(getNextButton()).toBeDisabled();

      // Wait for products and select
      await selectProduct();

      // Verify step marked complete
      expect(useWizardStore.getState().completedSteps.includes('select')).toBe(true);

      await waitFor(() => {
        expect(getNextButton()).toBeEnabled();
      });

      // Click Next to go to Step 2
      fireEvent.click(getNextButton());

      // STEP 2: Edit BOM
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /edit.*bom/i })).toBeInTheDocument();
      });

      expect(useWizardStore.getState().currentStep).toBe('edit');

      // Wait for BOM to load
      await waitFor(() => {
        expect(useCalculatorStore.getState().bomItems.length).toBeGreaterThan(0);
      });

      // BOMEditor marks step complete when form is valid
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps.includes('edit')).toBe(true);
      });

      // Click Calculate
      await waitFor(() => {
        expect(getNextButton()).toBeEnabled();
      });
      fireEvent.click(getNextButton());

      // STEP 3: Results
      await waitFor(
        () => {
          expect(screen.getByRole('heading', { name: /results/i })).toBeInTheDocument();
        },
        { timeout: 15000 }
      );

      expect(useWizardStore.getState().currentStep).toBe('results');

      // Verify results displayed
      await waitFor(() => {
        const co2Elements = screen.getAllByText(/kg co/i);
        expect(co2Elements.length).toBeGreaterThan(0);
      });

      const finalState = useCalculatorStore.getState();
      expect(finalState.calculation).toBeTruthy();
      expect(finalState.calculation?.status).toBe('completed');
      expect(finalState.calculation?.total_co2e_kg).toBeGreaterThan(0);

      expect(useWizardStore.getState().completedSteps.includes('select')).toBe(true);
      expect(useWizardStore.getState().completedSteps.includes('edit')).toBe(true);
    });
  });

  describe('Scenario 2: State Persistence Across Steps', () => {
    test('preserves product selection when navigating back from Step 2', async () => {
      render(<CalculationWizard />);

      await navigateToStep2();

      // Go back to Step 1
      fireEvent.click(getPreviousButton());

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('select');
      });

      // Verify product still selected
      expect(useCalculatorStore.getState().selectedProductId).toBe('prod-001');
    });

    test('preserves BOM data when navigating back from Step 3', async () => {
      render(<CalculationWizard />);

      await navigateToStep2();

      // Wait for BOM to load
      await waitFor(() => {
        expect(useCalculatorStore.getState().bomItems.length).toBeGreaterThan(0);
      }, { timeout: 10000 });

      const bomItemsCount = useCalculatorStore.getState().bomItems.length;

      // Wait for edit step complete
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps.includes('edit')).toBe(true);
      }, { timeout: 10000 });

      // Click Calculate
      await waitFor(() => {
        expect(getNextButton()).toBeEnabled();
      }, { timeout: 10000 });
      fireEvent.click(getNextButton());

      // Wait for results step
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('results');
      }, { timeout: 15000 });

      // Go back to Step 2
      fireEvent.click(getPreviousButton());

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Verify BOM data persisted
      expect(useCalculatorStore.getState().bomItems.length).toBe(bomItemsCount);
    });
  });

  describe('Scenario 3: Navigation Guards and Validation', () => {
    test('prevents advancing to Step 2 without product selection', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
      });

      expect(getNextButton()).toBeDisabled();

      // Try to navigate programmatically
      await act(async () => {
        useWizardStore.getState().setStep('edit');
      });

      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    test('validates navigation requires all previous steps complete', async () => {
      render(<CalculationWizard />);

      // Try to skip to results
      await act(async () => {
        useWizardStore.getState().setStep('results');
      });
      expect(useWizardStore.getState().currentStep).toBe('select');

      // Mark select complete - still can't skip edit
      await act(async () => {
        useWizardStore.getState().markStepComplete('select');
        useWizardStore.getState().setStep('results');
      });
      expect(useWizardStore.getState().currentStep).toBe('select');

      // Mark edit complete - now can go to results
      await act(async () => {
        useWizardStore.getState().markStepComplete('edit');
        useWizardStore.getState().setStep('results');
      });
      expect(useWizardStore.getState().currentStep).toBe('results');
    });
  });

  describe('Scenario 4: Error Handling and Recovery', () => {
    test('handles product loading error gracefully', async () => {
      server.use(
        rest.get('http://localhost:8000/api/v1/products/search', (_req, res, ctx) => {
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

      await waitFor(() => {
        expect(screen.getByText(/unable to load products/i)).toBeInTheDocument();
      });
    });

    test('handles calculation failure gracefully', async () => {
      server.use(
        rest.get('http://localhost:8000/api/v1/calculations/:id', (_req, res, ctx) => {
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

      await navigateToStep2();

      // Wait for BOM to load and edit step to complete
      await waitFor(() => {
        expect(useCalculatorStore.getState().bomItems.length).toBeGreaterThan(0);
      });
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps.includes('edit')).toBe(true);
      });
      await waitFor(() => {
        expect(getNextButton()).toBeEnabled();
      });

      // Click Calculate
      fireEvent.click(getNextButton());

      // Should display error in overlay
      await waitFor(
        () => {
          expect(screen.getByText(/missing emission data/i)).toBeInTheDocument();
        },
        { timeout: 15000 }
      );

      // Should remain on edit step
      expect(useWizardStore.getState().currentStep).toBe('edit');
    });
  });

  describe('Scenario 5: Cross-Component Interactions', () => {
    test('wizard progress updates as steps complete', async () => {
      render(<CalculationWizard />);

      // Initially on step 1
      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        const step1Button = buttons.find(
          (btn) => btn.getAttribute('aria-label')?.toLowerCase().includes('select product')
        );
        expect(step1Button).toHaveAttribute('aria-current', 'step');
      });

      // Select product and navigate to step 2
      await navigateToStep2();

      // Progress should update
      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        const step2Button = buttons.find(
          (btn) => btn.getAttribute('aria-label')?.toLowerCase().includes('edit bom')
        );
        expect(step2Button).toHaveAttribute('aria-current', 'step');
      });
    });
  });

  describe('Scenario 6: Store Synchronization', () => {
    test('wizard store and calculator store stay synchronized', async () => {
      render(<CalculationWizard />);

      await selectProduct();

      // Verify step is marked complete
      expect(useWizardStore.getState().completedSteps.includes('select')).toBe(true);

      // Navigate to edit step
      await waitFor(() => {
        expect(getNextButton()).toBeEnabled();
      });
      fireEvent.click(getNextButton());

      // Verify we're on edit step and BOM is loaded
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
        expect(useCalculatorStore.getState().bomItems.length).toBeGreaterThan(0);
      });
    });
  });
});
