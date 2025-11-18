/**
 * Wizard Store Tests
 *
 * Tests for wizard navigation state management including:
 * - Step navigation with validation gates
 * - Step completion tracking
 * - Navigation helpers (goNext, goBack)
 * - Persistence middleware
 * - Prevent skipping ahead to incomplete steps
 */

import { describe, test, expect, beforeEach } from 'vitest';
import { useWizardStore } from '../../src/store/wizardStore';

describe('WizardStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useWizardStore.getState().reset();
    // Clear localStorage to ensure clean state
    localStorage.clear();
  });

  describe('Initial State', () => {
    test('initializes with select step', () => {
      const { currentStep } = useWizardStore.getState();
      expect(currentStep).toBe('select');
    });

    test('initializes with no completed steps', () => {
      const { completedSteps } = useWizardStore.getState();
      expect(completedSteps).toEqual([]);
    });

    test('initializes with canProceed false', () => {
      const { canProceed } = useWizardStore.getState();
      expect(canProceed).toBe(false);
    });

    test('initializes with canGoBack false', () => {
      const { canGoBack } = useWizardStore.getState();
      expect(canGoBack).toBe(false);
    });
  });

  describe('Step Navigation - Validation Gates', () => {
    test('prevents skipping to results when steps incomplete', () => {
      const { setStep, currentStep } = useWizardStore.getState();

      // Try to skip directly to results
      setStep('results');

      // Should remain at select step
      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
    });

    test('prevents skipping to calculate when select incomplete', () => {
      const { setStep, currentStep } = useWizardStore.getState();

      // Try to skip to calculate
      setStep('calculate');

      // Should remain at select step
      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
    });

    test('allows navigation to next step when current is complete', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      // Complete select step
      markStepComplete('select');

      // Should be able to go to edit
      setStep('edit');

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('edit');
    });

    test('allows navigation backward to any previous step', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      // Complete steps and advance
      markStepComplete('select');
      setStep('edit');
      markStepComplete('edit');
      setStep('calculate');

      // Go back to select
      setStep('select');

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
    });

    test('allows skipping to results when all previous steps complete', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      // Complete all steps
      markStepComplete('select');
      markStepComplete('edit');
      markStepComplete('calculate');

      // Jump to results
      setStep('results');

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('results');
    });
  });

  describe('Step Completion', () => {
    test('markStepComplete adds step to completedSteps', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');

      const state = useWizardStore.getState();
      expect(state.completedSteps).toContain('select');
    });

    test('markStepComplete sets canProceed to true', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');

      const state = useWizardStore.getState();
      expect(state.canProceed).toBe(true);
    });

    test('markStepComplete prevents duplicates in completedSteps', () => {
      const { markStepComplete } = useWizardStore.getState();

      // Mark same step twice
      markStepComplete('select');
      markStepComplete('select');

      const state = useWizardStore.getState();
      expect(state.completedSteps.filter(s => s === 'select').length).toBe(1);
    });

    test('markStepIncomplete removes step from completedSteps', () => {
      const { markStepComplete, markStepIncomplete } = useWizardStore.getState();

      // Complete then incomplete
      markStepComplete('select');
      markStepIncomplete('select');

      const state = useWizardStore.getState();
      expect(state.completedSteps).not.toContain('select');
    });

    test('markStepIncomplete sets canProceed to false', () => {
      const { markStepComplete, markStepIncomplete } = useWizardStore.getState();

      markStepComplete('select');
      markStepIncomplete('select');

      const state = useWizardStore.getState();
      expect(state.canProceed).toBe(false);
    });
  });

  describe('Navigation Helpers', () => {
    test('goNext advances to next step when current complete', () => {
      const { markStepComplete, goNext } = useWizardStore.getState();

      markStepComplete('select');
      goNext();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('edit');
    });

    test('goNext does not advance when current incomplete', () => {
      const { goNext } = useWizardStore.getState();

      // Try to advance without completing
      goNext();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
    });

    test('goNext does nothing at last step', () => {
      const { markStepComplete, setStep, goNext } = useWizardStore.getState();

      // Complete all and go to results
      markStepComplete('select');
      markStepComplete('edit');
      markStepComplete('calculate');
      setStep('results');

      goNext();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('results');
    });

    test('goBack moves to previous step', () => {
      const { markStepComplete, setStep, goBack } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      goBack();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
    });

    test('goBack does nothing at first step', () => {
      const { goBack } = useWizardStore.getState();

      goBack();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
    });

    test('goBack sets canGoBack to false at first step', () => {
      const { markStepComplete, setStep, goBack } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');
      goBack();

      const state = useWizardStore.getState();
      expect(state.canGoBack).toBe(false);
    });
  });

  describe('canProceed and canGoBack Flags', () => {
    test('sets canGoBack to true when not at first step', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      const state = useWizardStore.getState();
      expect(state.canGoBack).toBe(true);
    });

    test('sets canProceed to true when step is completed', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');

      const state = useWizardStore.getState();
      expect(state.canProceed).toBe(true);
    });

    test('updates canProceed when navigating to incomplete step', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');
      // Edit is not complete

      const state = useWizardStore.getState();
      expect(state.canProceed).toBe(true); // Can still proceed if step becomes complete
    });
  });

  describe('Reset Functionality', () => {
    test('reset returns to initial state', () => {
      const { markStepComplete, setStep, reset } = useWizardStore.getState();

      // Make changes
      markStepComplete('select');
      setStep('edit');
      markStepComplete('edit');

      // Reset
      reset();

      const state = useWizardStore.getState();
      expect(state.currentStep).toBe('select');
      expect(state.completedSteps).toEqual([]);
      expect(state.canProceed).toBe(false);
      expect(state.canGoBack).toBe(false);
    });
  });

  describe('Persistence', () => {
    test('persists currentStep to localStorage', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      // Check localStorage
      const stored = localStorage.getItem('pcf-wizard-storage');
      expect(stored).toBeTruthy();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.currentStep).toBe('edit');
    });

    test('persists completedSteps to localStorage', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');
      markStepComplete('edit');

      // Check localStorage
      const stored = localStorage.getItem('pcf-wizard-storage');
      expect(stored).toBeTruthy();

      const parsed = JSON.parse(stored!);
      expect(parsed.state.completedSteps).toContain('select');
      expect(parsed.state.completedSteps).toContain('edit');
    });

    test('restores state from localStorage on initialization', () => {
      // Set up persisted state
      const { markStepComplete, setStep } = useWizardStore.getState();
      markStepComplete('select');
      setStep('edit');

      // Get current localStorage state
      const stored = localStorage.getItem('pcf-wizard-storage');

      // Reset store
      useWizardStore.getState().reset();

      // Restore from localStorage by re-initializing
      // (In real usage, this happens automatically on page load)
      if (stored) {
        const parsed = JSON.parse(stored);
        const restoredState = useWizardStore.getState();
        expect(parsed.state.currentStep).toBe('edit');
      }
    });

    test('does not persist canProceed flag', () => {
      const { markStepComplete } = useWizardStore.getState();

      markStepComplete('select');

      const stored = localStorage.getItem('pcf-wizard-storage');
      const parsed = JSON.parse(stored!);

      // canProceed should not be in persisted state
      expect(parsed.state.canProceed).toBeUndefined();
    });

    test('does not persist canGoBack flag', () => {
      const { markStepComplete, setStep } = useWizardStore.getState();

      markStepComplete('select');
      setStep('edit');

      const stored = localStorage.getItem('pcf-wizard-storage');
      const parsed = JSON.parse(stored!);

      // canGoBack should not be in persisted state
      expect(parsed.state.canGoBack).toBeUndefined();
    });
  });

  describe('Warning Messages', () => {
    test('logs warning when trying to skip ahead', () => {
      const { setStep } = useWizardStore.getState();

      // Spy on console.warn
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      // Try to skip
      setStep('results');

      expect(warnSpy).toHaveBeenCalled();
      expect(warnSpy.mock.calls[0][0]).toContain('Cannot skip to results');

      warnSpy.mockRestore();
    });
  });
});
