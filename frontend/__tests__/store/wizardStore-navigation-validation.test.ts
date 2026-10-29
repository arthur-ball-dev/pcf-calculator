/**
 * Wizard Navigation Validation Tests
 *
 * UPDATED: UI Redesign - 3-step wizard (select → edit → results)
 * The 'calculate' step was removed; calculation now happens via overlay
 * when transitioning from 'edit' to 'results'.
 *
 * Tests validate:
 * - Navigation guards work correctly for 3-step wizard
 * - canProceed flag updates appropriately based on step completion
 * - Transition from edit to results works with calculation
 */

import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';

describe('Wizard Navigation - 3-Step Wizard Validation', () => {
  beforeEach(() => {
    // Reset stores to clean state
    useWizardStore.setState({
      currentStep: 'select',
      completedSteps: [],
      canProceed: false,
    });
    useCalculatorStore.setState({
      calculation: null,
    });
  });

  describe('Step Progression', () => {
    it('should start on select step', () => {
      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    it('should allow proceeding from select step when complete', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');

      expect(useWizardStore.getState().canProceed).toBe(true);
      expect(useWizardStore.getState().completedSteps).toContain('select');
    });

    it('should navigate from select to edit', () => {
      const { setStep, markStepComplete } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      expect(useWizardStore.getState().currentStep).toBe('edit');
    });

    it('should allow proceeding from edit step when complete', () => {
      const { setStep, markStepComplete } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');
      markStepComplete('edit');

      expect(useWizardStore.getState().canProceed).toBe(true);
      expect(useWizardStore.getState().completedSteps).toContain('edit');
    });

    it('should navigate from edit to results', () => {
      const { setStep, markStepComplete } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');
      markStepComplete('edit');
      setStep('results');

      expect(useWizardStore.getState().currentStep).toBe('results');
    });
  });

  describe('Navigation Guards', () => {
    it('should prevent navigation to edit without completing select', () => {
      const { setStep } = useWizardStore.getState();

      // Try to skip to edit
      setStep('edit');

      // Should remain on select
      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    it('should prevent navigation to results without completing previous steps', () => {
      const { setStep } = useWizardStore.getState();

      // Try to skip to results
      setStep('results');

      // Should remain on select
      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    it('should prevent navigation to results when only select is complete', () => {
      const { setStep, markStepComplete } = useWizardStore.getState();

      markStepComplete('select');
      setStep('results');

      // Should remain on select (can't skip edit)
      expect(useWizardStore.getState().currentStep).toBe('select');
    });
  });

  describe('Calculation Integration', () => {
    it('should auto-advance to results when calculation completes', () => {
      const { setStep, markStepComplete } = useWizardStore.getState();
      const { setCalculation } = useCalculatorStore.getState();

      // Navigate to edit step
      markStepComplete('select');
      setStep('edit');
      markStepComplete('edit');

      // Simulate calculation completion (this triggers auto-advance)
      setCalculation({
        id: 'test-calc-123',
        status: 'completed',
        product_id: 'test-product-456',
        total_co2e_kg: 2.5,
      });

      // Calculation completion should advance to results
      expect(useWizardStore.getState().currentStep).toBe('results');
    });

    it('should not allow going back from results on last step', () => {
      const { setStep, markStepComplete } = useWizardStore.getState();

      // Complete all steps
      markStepComplete('select');
      setStep('edit');
      markStepComplete('edit');
      setStep('results');

      // Results is the last step, canProceed should be false
      expect(useWizardStore.getState().canProceed).toBe(false);
    });
  });
});
