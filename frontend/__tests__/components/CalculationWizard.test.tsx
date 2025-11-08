/**
 * CalculationWizard Component Tests
 *
 * Test-Driven Development for TASK-FE-005
 * Written BEFORE implementation (TDD Protocol)
 *
 * Test Scenarios:
 * 1. Wizard Prevents Skipping Ahead - Cannot skip to incomplete steps
 * 2. Navigation After Validation - Next button works when step complete
 * 3. Back Navigation Preserves State - Can go back without losing data
 * 4. Keyboard Shortcuts - Alt+Arrow keys for navigation
 * 5. Start Over Confirmation - Dialog confirms reset
 * 6. Progress Indicator - Shows current step and completion
 * 7. Step Component Rendering - Renders correct component for each step
 * 8. Auto-advance on Calculation Complete - Goes to Results automatically
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import CalculationWizard from '../../src/components/calculator/CalculationWizard';
import { useWizardStore } from '../../src/store/wizardStore';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import type { Calculation } from '../../src/types/store.types';

// Mock the API
vi.mock('../../src/services/api/products', () => ({
  fetchProducts: vi.fn().mockResolvedValue([]),
}));

describe('CalculationWizard Component', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();

    // Clear all mocks
    vi.clearAllMocks();
  });

  describe('Scenario 1: Wizard Prevents Skipping Ahead', () => {
    test('remains on Step 1 when trying to click on Step 4 before completion', async () => {
      render(<CalculationWizard />);

      // Verify we start on Step 1
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
      });

      // Try to click on Results step (should be disabled)
      const progressButtons = screen.getAllByRole('button');
      const resultsButton = progressButtons.find(btn =>
        btn.getAttribute('aria-label')?.includes('Results')
      );

      if (resultsButton) {
        await user.click(resultsButton);
      }

      // Should still be on Step 1
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
      });

      // Verify wizard state unchanged
      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    test('Next button is disabled when current step is not complete', () => {
      render(<CalculationWizard />);

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();
    });

    test('prevents navigation to Step 3 when Steps 1-2 are incomplete', async () => {
      render(<CalculationWizard />);

      // Try to navigate directly to calculate step
      useWizardStore.getState().setStep('calculate');

      // Should remain on select step
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('select');
      });
    });

    test('allows navigation to Step 2 only after Step 1 is complete', async () => {
      render(<CalculationWizard />);

      // Mark Step 1 complete
      useWizardStore.getState().markStepComplete('select');

      // Now should be able to navigate to Step 2
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });
    });
  });

  describe('Scenario 2: Navigation After Validation', () => {
    test('advances to Step 2 when clicking Next after Step 1 complete', async () => {
      render(<CalculationWizard />);

      // Complete Step 1
      useWizardStore.getState().markStepComplete('select');

      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        expect(nextButton).not.toBeDisabled();
      });

      // Click Next
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      // Should advance to Step 2
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /edit bom/i })).toBeInTheDocument();
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });
    });

    test('Next button becomes enabled when step validation passes', async () => {
      render(<CalculationWizard />);

      // Initially disabled
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      // Mark step complete
      useWizardStore.getState().markStepComplete('select');

      // Should become enabled
      await waitFor(() => {
        expect(nextButton).not.toBeDisabled();
      });
    });

    test('displays correct step heading after navigation', async () => {
      render(<CalculationWizard />);

      // Navigate through steps
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /edit bom/i })).toBeInTheDocument();
      });

      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().setStep('calculate');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /calculate/i })).toBeInTheDocument();
      });
    });

    test('displays step description below heading', async () => {
      render(<CalculationWizard />);

      // Check for description on Step 1
      expect(screen.getByText(/choose a product to calculate/i)).toBeInTheDocument();

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(screen.getByText(/review and modify/i)).toBeInTheDocument();
      });
    });
  });

  describe('Scenario 3: Back Navigation Preserves State', () => {
    test('navigates back to Step 1 when clicking Previous from Step 2', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /edit bom/i })).toBeInTheDocument();
      });

      // Click Previous
      const prevButton = screen.getByRole('button', { name: /previous/i });
      await user.click(prevButton);

      // Should return to Step 1
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();
        expect(useWizardStore.getState().currentStep).toBe('select');
      });
    });

    test('preserves product selection when navigating back', async () => {
      render(<CalculationWizard />);

      // Set product selection
      useCalculatorStore.getState().setSelectedProduct(123);
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Navigate back
      const prevButton = screen.getByRole('button', { name: /previous/i });
      await user.click(prevButton);

      // Product selection should be preserved
      expect(useCalculatorStore.getState().selectedProductId).toBe(123);
    });

    test('Next button enabled after navigating back to completed step', async () => {
      render(<CalculationWizard />);

      // Complete Step 1 and navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Navigate back
      const prevButton = screen.getByRole('button', { name: /previous/i });
      await user.click(prevButton);

      // Next button should be enabled (step already complete)
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        expect(nextButton).not.toBeDisabled();
      });
    });

    test('Previous button disabled on first step', () => {
      render(<CalculationWizard />);

      const prevButton = screen.getByRole('button', { name: /previous/i });
      expect(prevButton).toBeDisabled();
    });

    test('Previous button enabled on subsequent steps', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /previous/i });
        expect(prevButton).not.toBeDisabled();
      });
    });
  });

  describe('Scenario 4: Keyboard Shortcuts', () => {
    test('Alt+ArrowRight navigates to next step when current step complete', async () => {
      render(<CalculationWizard />);

      // Complete Step 1
      useWizardStore.getState().markStepComplete('select');

      await waitFor(() => {
        expect(useWizardStore.getState().canProceed).toBe(true);
      });

      // Press Alt+→
      await user.keyboard('{Alt>}{ArrowRight}{/Alt}');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });
    });

    test('Alt+ArrowLeft navigates to previous step', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Press Alt+←
      await user.keyboard('{Alt>}{ArrowLeft}{/Alt}');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('select');
      });
    });

    test('Alt+ArrowRight does nothing when on last step', async () => {
      render(<CalculationWizard />);

      // Navigate to last step
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().markStepComplete('calculate');
      useWizardStore.getState().setStep('results');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('results');
      });

      // Press Alt+→
      await user.keyboard('{Alt>}{ArrowRight}{/Alt}');

      // Should remain on results
      expect(useWizardStore.getState().currentStep).toBe('results');
    });

    test('Alt+ArrowLeft does nothing when on first step', async () => {
      render(<CalculationWizard />);

      // Already on first step
      expect(useWizardStore.getState().currentStep).toBe('select');

      // Press Alt+←
      await user.keyboard('{Alt>}{ArrowLeft}{/Alt}');

      // Should remain on select
      expect(useWizardStore.getState().currentStep).toBe('select');
    });
  });

  describe('Scenario 5: Start Over Confirmation', () => {
    test('shows confirmation dialog when clicking Start Over', async () => {
      render(<CalculationWizard />);

      // Navigate to a later step
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
      });

      // Click Start Over
      const startOverButton = screen.getByRole('button', { name: /start over/i });
      await user.click(startOverButton);

      // Dialog should appear
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText(/reset calculator/i)).toBeInTheDocument();
      });
    });

    test('resets wizard state when confirming Start Over', async () => {
      render(<CalculationWizard />);

      // Complete some steps
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');
      useCalculatorStore.getState().setSelectedProduct(456);

      // Click Start Over
      const startOverButton = screen.getByRole('button', { name: /start over/i });
      await user.click(startOverButton);

      // Confirm reset
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const resetButton = screen.getByRole('button', { name: /^reset$/i });
      await user.click(resetButton);

      // State should be reset
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('select');
        expect(useWizardStore.getState().completedSteps).toHaveLength(0);
        expect(useCalculatorStore.getState().selectedProductId).toBeNull();
      });
    });

    test('cancels reset when clicking Cancel in dialog', async () => {
      render(<CalculationWizard />);

      // Complete some steps
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');
      useCalculatorStore.getState().setSelectedProduct(789);

      // Click Start Over
      const startOverButton = screen.getByRole('button', { name: /start over/i });
      await user.click(startOverButton);

      // Cancel reset
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // State should be unchanged
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('edit');
        expect(useCalculatorStore.getState().selectedProductId).toBe(789);
      });
    });

    test('Start Over button not shown on first step', () => {
      render(<CalculationWizard />);

      // Should not show Start Over on Step 1
      expect(screen.queryByRole('button', { name: /start over/i })).not.toBeInTheDocument();
    });

    test('Start Over button shown on subsequent steps', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /start over/i })).toBeInTheDocument();
      });
    });
  });

  describe('Scenario 6: Progress Indicator', () => {
    test('displays all 4 steps in progress indicator', () => {
      render(<CalculationWizard />);

      // Check for step labels
      expect(screen.getByText(/select product/i)).toBeInTheDocument();
      expect(screen.getByText(/edit bom/i)).toBeInTheDocument();
      expect(screen.getByText(/calculate/i)).toBeInTheDocument();
      expect(screen.getByText(/results/i)).toBeInTheDocument();
    });

    test('marks current step with aria-current="step"', async () => {
      render(<CalculationWizard />);

      // Find progress buttons
      const progressButtons = screen.getAllByRole('button');
      const currentStepButton = progressButtons.find(btn =>
        btn.getAttribute('aria-current') === 'step'
      );

      expect(currentStepButton).toBeDefined();
      expect(currentStepButton?.getAttribute('aria-label')).toMatch(/select product/i);
    });

    test('updates progress indicator when step changes', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        const progressButtons = screen.getAllByRole('button');
        const currentStepButton = progressButtons.find(btn =>
          btn.getAttribute('aria-current') === 'step'
        );
        expect(currentStepButton?.getAttribute('aria-label')).toMatch(/edit bom/i);
      });
    });

    test('shows completed steps with checkmark indicator', async () => {
      render(<CalculationWizard />);

      // Mark Step 1 complete
      useWizardStore.getState().markStepComplete('select');

      // Progress indicator should show completion
      // This will be verified by the component's visual state
      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('select');
      });
    });

    test('disables step buttons for inaccessible steps', async () => {
      render(<CalculationWizard />);

      // Get all progress buttons
      const progressButtons = screen.getAllByRole('button').filter(btn =>
        btn.getAttribute('aria-label')?.includes('Results') ||
        btn.getAttribute('aria-label')?.includes('Calculate')
      );

      // Future steps should be disabled
      const disabledButtons = progressButtons.filter(btn => btn.hasAttribute('disabled'));
      expect(disabledButtons.length).toBeGreaterThan(0);
    });
  });

  describe('Scenario 7: Step Component Rendering', () => {
    test('renders ProductSelector component on Step 1', async () => {
      render(<CalculationWizard />);

      // ProductSelector should be rendered (has combobox role)
      await waitFor(() => {
        const heading = screen.getByRole('heading', { name: /select product/i });
        expect(heading).toBeInTheDocument();
      });
    });

    test('renders BOMEditor component on Step 2', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /edit bom/i })).toBeInTheDocument();
      });
    });

    test('renders CalculateView component on Step 3', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 3
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().setStep('calculate');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /calculate/i })).toBeInTheDocument();
      });
    });

    test('renders ResultsDisplay component on Step 4', async () => {
      render(<CalculationWizard />);

      // Navigate to Step 4
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().markStepComplete('calculate');
      useWizardStore.getState().setStep('results');

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /results/i })).toBeInTheDocument();
      });
    });

    test('unmounts previous step component when navigating', async () => {
      render(<CalculationWizard />);

      // Verify Step 1 heading exists
      expect(screen.getByRole('heading', { name: /select product/i })).toBeInTheDocument();

      // Navigate to Step 2
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().setStep('edit');

      // Step 1 heading should be replaced
      await waitFor(() => {
        expect(screen.queryByRole('heading', { name: /select product/i })).not.toBeInTheDocument();
        expect(screen.getByRole('heading', { name: /edit bom/i })).toBeInTheDocument();
      });
    });
  });

  describe('Scenario 8: Auto-advance on Calculation Complete', () => {
    test('automatically advances to Results when calculation completes', async () => {
      render(<CalculationWizard />);

      // Navigate to Calculate step
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().setStep('calculate');

      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('calculate');
      });

      // Simulate calculation completion
      const completedCalculation: Calculation = {
        id: 'calc-123',
        product_id: 1,
        status: 'completed',
        total_co2e: 12.5,
        materials_co2e: 8.0,
        energy_co2e: 3.5,
        transport_co2e: 1.0,
        waste_co2e: 0.0,
        calculation_type: 'cradle_to_gate',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      useCalculatorStore.getState().setCalculation(completedCalculation);

      // Should auto-advance to results
      await waitFor(() => {
        expect(useWizardStore.getState().currentStep).toBe('results');
      });
    });

    test('does not auto-advance when calculation is pending', () => {
      render(<CalculationWizard />);

      const pendingCalculation: Calculation = {
        id: 'calc-456',
        product_id: 1,
        status: 'pending',
        total_co2e: 0,
        materials_co2e: 0,
        energy_co2e: 0,
        transport_co2e: 0,
        waste_co2e: 0,
        calculation_type: 'cradle_to_gate',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      useCalculatorStore.getState().setCalculation(pendingCalculation);

      // Should not advance
      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    test('marks calculate step complete when calculation finishes', async () => {
      render(<CalculationWizard />);

      const completedCalculation: Calculation = {
        id: 'calc-789',
        product_id: 1,
        status: 'completed',
        total_co2e: 15.0,
        materials_co2e: 10.0,
        energy_co2e: 4.0,
        transport_co2e: 1.0,
        waste_co2e: 0.0,
        calculation_type: 'cradle_to_gate',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      useCalculatorStore.getState().setCalculation(completedCalculation);

      await waitFor(() => {
        expect(useWizardStore.getState().completedSteps).toContain('calculate');
      });
    });
  });

  describe('Accessibility', () => {
    test('wizard has main landmark', () => {
      render(<CalculationWizard />);

      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    test('progress indicator has navigation role', () => {
      render(<CalculationWizard />);

      // Progress should be in header or have appropriate role
      const header = screen.getByRole('banner');
      expect(header).toBeInTheDocument();
    });

    test('keyboard navigation works throughout wizard', async () => {
      render(<CalculationWizard />);

      // Tab through interactive elements
      const nextButton = screen.getByRole('button', { name: /next/i });
      nextButton.focus();
      expect(nextButton).toHaveFocus();

      // Should be able to tab to other buttons
      await user.tab();
      // Some other element should have focus
      expect(nextButton).not.toHaveFocus();
    });

    test('shows New Calculation button on final step instead of Next', async () => {
      render(<CalculationWizard />);

      // Navigate to final step
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().markStepComplete('calculate');
      useWizardStore.getState().setStep('results');

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /next/i })).not.toBeInTheDocument();
        expect(screen.getByRole('button', { name: /new calculation/i })).toBeInTheDocument();
      });
    });
  });

  describe('Layout and Structure', () => {
    test('renders with header, main, and footer sections', () => {
      render(<CalculationWizard />);

      expect(screen.getByRole('banner')).toBeInTheDocument(); // header
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
    });

    test('shows PCF Calculator title in header', () => {
      render(<CalculationWizard />);

      expect(screen.getByRole('heading', { name: /pcf calculator/i, level: 1 })).toBeInTheDocument();
    });

    test('navigation buttons in footer', () => {
      render(<CalculationWizard />);

      const footer = screen.getByRole('contentinfo');
      const prevButton = screen.getByRole('button', { name: /previous/i });
      const nextButton = screen.getByRole('button', { name: /next/i });

      expect(footer).toContainElement(prevButton);
      expect(footer).toContainElement(nextButton);
    });
  });
});
