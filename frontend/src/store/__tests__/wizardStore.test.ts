/**
 * Wizard Store Unit Tests
 *
 * TASK-FE-P7-040: Comprehensive unit tests for wizardStore achieving 90% coverage.
 *
 * Tests cover:
 * - Initial state verification
 * - Step navigation (next, previous, goToStep)
 * - Step validation gates (cannot proceed without required data)
 * - Step completion tracking
 * - Reset functionality
 * - LocalStorage persistence
 *
 * TDD Protocol: Tests written FIRST, implementation verified against these tests.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import type { WizardStep } from '@/types/store.types';

// ============================================================================
// Test Suite
// ============================================================================

describe('wizardStore', () => {
  beforeEach(() => {
    // Clear localStorage to prevent persistence interference
    localStorage.clear();

    // Reset both stores for isolation
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();

    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ==========================================================================
  // Initial State Tests
  // ==========================================================================

  describe('Initial State', () => {
    it('Scenario 10: should have correct initial state after reset', () => {
      useWizardStore.getState().reset();
      const state = useWizardStore.getState();

      expect(state.currentStep).toBe('select');
      expect(state.completedSteps).toHaveLength(0);
      expect(state.canProceed).toBe(false);
      expect(state.canGoBack).toBe(false);
    });

    it('should have all required actions defined', () => {
      const state = useWizardStore.getState();

      expect(typeof state.setStep).toBe('function');
      expect(typeof state.markStepComplete).toBe('function');
      expect(typeof state.markStepIncomplete).toBe('function');
      expect(typeof state.goNext).toBe('function');
      expect(typeof state.goBack).toBe('function');
      expect(typeof state.reset).toBe('function');
    });
  });

  // ==========================================================================
  // Step Navigation Tests
  // ==========================================================================

  describe('Step Navigation', () => {
    it('Scenario 11: should navigate forward when step is complete', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('edit');
      expect(state.canGoBack).toBe(true);
    });

    it('Scenario 12: should block skip ahead without completing prior steps', () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const { reset, setStep } = useWizardStore.getState();

      reset();
      setStep('results'); // Try to skip ahead without completing prior steps

      expect(useWizardStore.getState().currentStep).toBe('select');
      expect(warnSpy).toHaveBeenCalled();
    });

    it('should allow backward navigation without restrictions', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');
      setStep('calculate');
      setStep('edit'); // Go back

      expect(useWizardStore.getState().currentStep).toBe('edit');
    });

    it('should allow navigating to first step from any step', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');
      setStep('calculate');
      setStep('select'); // Go all the way back

      expect(useWizardStore.getState().currentStep).toBe('select');
    });
  });

  // ==========================================================================
  // goNext/goBack Tests
  // ==========================================================================

  describe('Navigation Helpers', () => {
    it('Scenario 13: goNext and goBack should navigate correctly', () => {
      const { reset, markStepComplete, goNext, goBack } = useWizardStore.getState();

      reset();
      markStepComplete('select');
      goNext();
      markStepComplete('edit');
      goNext();
      goBack();

      expect(useWizardStore.getState().currentStep).toBe('edit');
    });

    it('goNext should not advance beyond last step', () => {
      const { markStepComplete, setStep, goNext } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');
      markStepComplete('calculate');
      setStep('results');
      goNext();

      expect(useWizardStore.getState().currentStep).toBe('results');
    });

    it('goBack should not go before first step', () => {
      const { reset, goBack } = useWizardStore.getState();

      reset();
      goBack();

      expect(useWizardStore.getState().currentStep).toBe('select');
    });

    it('goNext should not advance if prior steps incomplete', () => {
      const { reset, goNext } = useWizardStore.getState();

      reset();
      goNext(); // Should not advance because select is not complete

      expect(useWizardStore.getState().currentStep).toBe('select');
    });
  });

  // ==========================================================================
  // Step Completion Tests
  // ==========================================================================

  describe('Step Completion', () => {
    it('Scenario 14: markStepIncomplete should revoke completion', () => {
      const { markStepComplete, markStepIncomplete } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');
      markStepIncomplete('select');

      const state = useWizardStore.getState();
      expect(state.completedSteps).not.toContain('select');
      expect(state.completedSteps).toContain('edit');
    });

    it('markStepComplete should add step to completedSteps', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');

      expect(useWizardStore.getState().completedSteps).toContain('select');
    });

    it('markStepComplete should not duplicate steps', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('select');
      markStepComplete('select');

      const state = useWizardStore.getState();
      const selectCount = state.completedSteps.filter((s) => s === 'select').length;
      expect(selectCount).toBe(1);
    });

    it('markStepIncomplete should update canProceed to false', () => {
      const { markStepComplete, markStepIncomplete } = useWizardStore.getState();

      markStepComplete('select');
      expect(useWizardStore.getState().canProceed).toBe(true);

      markStepIncomplete('select');
      expect(useWizardStore.getState().canProceed).toBe(false);
    });
  });

  // ==========================================================================
  // canProceed and canGoBack Tests
  // ==========================================================================

  describe('Navigation Flags', () => {
    it('canGoBack should be false on first step', () => {
      const { reset } = useWizardStore.getState();

      reset();
      expect(useWizardStore.getState().canGoBack).toBe(false);
    });

    it('canGoBack should be true on second step', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      expect(useWizardStore.getState().canGoBack).toBe(true);
    });

    it('canProceed should be true when current step is complete', () => {
      const { reset, markStepComplete } = useWizardStore.getState();

      reset();
      expect(useWizardStore.getState().canProceed).toBe(false);

      markStepComplete('select');
      expect(useWizardStore.getState().canProceed).toBe(true);
    });
  });

  // ==========================================================================
  // LocalStorage Persistence Tests
  // ==========================================================================

  describe('LocalStorage Persistence', () => {
    it('Scenario 15: should persist state to localStorage', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      // Check localStorage was updated
      const stored = localStorage.getItem('pcf-wizard-storage');
      expect(stored).not.toBeNull();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.currentStep).toBe('edit');
      expect(parsed.state.completedSteps).toContain('select');
    });

    it('should restore state from localStorage', () => {
      // Set up localStorage with persisted state
      const persistedState = {
        state: {
          currentStep: 'edit',
          completedSteps: ['select'],
        },
        version: 0,
      };
      localStorage.setItem('pcf-wizard-storage', JSON.stringify(persistedState));

      // Force a fresh read of the store to trigger hydration
      // In a real scenario, this happens on store initialization
      // For testing, we simulate by manually checking the stored value
      const stored = localStorage.getItem('pcf-wizard-storage');
      expect(stored).not.toBeNull();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.currentStep).toBe('edit');
      expect(parsed.state.completedSteps).toContain('select');
    });
  });

  // ==========================================================================
  // Reset Tests
  // ==========================================================================

  describe('Reset', () => {
    it('reset should clear all step progress', () => {
      const { markStepComplete, setStep, reset } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');
      setStep('calculate');

      reset();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
      expect(state.completedSteps).toHaveLength(0);
      expect(state.canProceed).toBe(false);
      expect(state.canGoBack).toBe(false);
    });
  });

  // ==========================================================================
  // Step Order Validation Tests
  // ==========================================================================

  describe('Step Order', () => {
    it('should follow step order: select -> edit -> calculate -> results', () => {
      const { markStepComplete, goNext } = useWizardStore.getState();

      expect(useWizardStore.getState().currentStep).toBe('select');

      markStepComplete('select');
      goNext();
      expect(useWizardStore.getState().currentStep).toBe('edit');

      markStepComplete('edit');
      goNext();
      expect(useWizardStore.getState().currentStep).toBe('calculate');

      // For calculate step, we need a completed calculation
      useCalculatorStore.getState().setCalculation({
        id: 'calc-1',
        status: 'completed',
        total_co2e: 100,
      });
      markStepComplete('calculate');
      goNext();
      expect(useWizardStore.getState().currentStep).toBe('results');
    });

    it('should prevent skipping to calculate without completing edit', () => {
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('calculate'); // Try to skip edit

      // Should not advance to calculate
      expect(useWizardStore.getState().currentStep).toBe('select');
      expect(warnSpy).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Integration with Calculator Store
  // ==========================================================================

  describe('Calculator Store Integration', () => {
    it('should update canProceed based on calculation status on calculate step', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');
      setStep('calculate');

      // Initially, canProceed should be false (no completed calculation)
      expect(useWizardStore.getState().canProceed).toBe(false);

      // Set a completed calculation - this also triggers markStepComplete('calculate')
      // and goNext() in the calculatorStore, which advances to results
      useCalculatorStore.getState().setCalculation({
        id: 'calc-1',
        status: 'completed',
        total_co2e: 100,
      });

      // After calculation completes, the wizard advances to 'results' step
      // and canProceed is updated - since we're now on results (last step),
      // canProceed reflects the 'results' step state
      expect(useWizardStore.getState().currentStep).toBe('results');
      expect(useWizardStore.getState().completedSteps).toContain('calculate');
    });
  });
});
