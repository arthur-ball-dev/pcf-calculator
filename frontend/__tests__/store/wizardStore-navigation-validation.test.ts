/**
 * Wizard Navigation Validation Tests
 *
 * TASK-FE-021: Test coverage for wizard navigation logic with calculation-complete requirement
 *
 * Tests validate:
 * - Users cannot skip calculation step until calculation completes
 * - Navigation logic correctly handles all calculation status states
 * - canProceed flag updates appropriately based on calculation status
 *
 * Test Protocol: Written test-first to validate Fix #8-9 from TASK-FE-013
 */

import { act } from '@testing-library/react';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';

describe('Wizard Navigation - Calculate Step Validation', () => {
  beforeEach(() => {
    // Reset stores to clean state
    useWizardStore.setState({
      currentStep: 'select',
      completedSteps: [],
      canProceed: false
    });
    useCalculatorStore.setState({
      calculation: null
    });
  });

  it('should allow proceeding from non-calculate steps without calculation', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();

    // Mark select step complete to allow navigation
    markStepComplete('select');

    // Navigate to BOM editor step
    setStep('edit');

    // Should be able to proceed (no calculation required yet)
    expect(useWizardStore.getState().canProceed).toBe(true);
  });

  it('should prevent proceeding from calculate step when no calculation exists', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();

    // Mark previous steps complete to allow navigation to calculate
    markStepComplete('select');
    markStepComplete('edit');

    // Navigate to calculate step
    setStep('calculate');

    // Verify canProceed is false (no calculation yet)
    expect(useWizardStore.getState().canProceed).toBe(false);
  });

  it('should prevent proceeding from calculate step when calculation is pending', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();
    const { setCalculation } = useCalculatorStore.getState();

    // Mark previous steps complete to allow navigation to calculate
    markStepComplete('select');
    markStepComplete('edit');

    // Navigate to calculate step
    setStep('calculate');

    // Set calculation to pending
    setCalculation({
      id: 'test-calc-123',
      status: 'pending',
      product_id: 'test-product-456'
    });

    // Should not be able to proceed (calculation not complete)
    expect(useWizardStore.getState().canProceed).toBe(false);
  });

  it('should prevent proceeding from calculate step when calculation is in_progress', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();
    const { setCalculation } = useCalculatorStore.getState();

    // Mark previous steps complete to allow navigation to calculate
    markStepComplete('select');
    markStepComplete('edit');

    setStep('calculate');

    // Set calculation to in_progress
    setCalculation({
      id: 'test-calc-123',
      status: 'in_progress',
      product_id: 'test-product-456'
    });

    expect(useWizardStore.getState().canProceed).toBe(false);
  });

  it('should allow proceeding from calculate step only when calculation is completed', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();
    const { setCalculation } = useCalculatorStore.getState();

    // Mark previous steps complete to allow navigation to calculate
    markStepComplete('select');
    markStepComplete('edit');

    setStep('calculate');

    // Set calculation to completed
    setCalculation({
      id: 'test-calc-123',
      status: 'completed',
      product_id: 'test-product-456',
      total_co2e_kg: 2.5,
      results: []
    });

    // Call setStep again to trigger canProceed recomputation
    setStep('calculate');

    // Now should be able to proceed
    expect(useWizardStore.getState().canProceed).toBe(true);
  });

  it('should prevent proceeding from calculate step when calculation failed', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();
    const { setCalculation } = useCalculatorStore.getState();

    // Mark previous steps complete to allow navigation to calculate
    markStepComplete('select');
    markStepComplete('edit');

    setStep('calculate');

    // Set calculation to failed
    setCalculation({
      id: 'test-calc-123',
      status: 'failed',
      product_id: 'test-product-456',
      error_message: 'Calculation error'
    });

    // Should not be able to proceed on failure
    expect(useWizardStore.getState().canProceed).toBe(false);
  });

  it('should update canProceed when calculation completes (integrated behavior)', () => {
    const { setStep, markStepComplete } = useWizardStore.getState();
    const { setCalculation } = useCalculatorStore.getState();

    // Mark previous steps complete to allow navigation to calculate
    markStepComplete('select');
    markStepComplete('edit');

    setStep('calculate');

    // Initially, canProceed should be false (no calculation yet)
    expect(useWizardStore.getState().canProceed).toBe(false);

    // Complete the calculation (this triggers markStepComplete and goNext)
    setCalculation({
      id: 'test-calc-123',
      status: 'completed',
      product_id: 'test-product-456',
      total_co2e_kg: 2.5,
      results: []
    });

    // Verify step was marked complete
    expect(useWizardStore.getState().completedSteps).toContain('calculate');
    // Verify wizard auto-advanced to results step
    expect(useWizardStore.getState().currentStep).toBe('results');
    // Verify canProceed is false on results step (it's the last step)
    expect(useWizardStore.getState().canProceed).toBe(false);
  });
});
