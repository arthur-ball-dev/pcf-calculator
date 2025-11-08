/**
 * Wizard Store
 *
 * Manages wizard navigation state for the PCF Calculator's 4-step workflow.
 * Implements validation gates to prevent users from skipping ahead to incomplete steps.
 * Persists state to localStorage to survive browser refreshes.
 *
 * Features:
 * - Step navigation with validation gates
 * - Step completion tracking
 * - Navigation helpers (goNext, goBack)
 * - Browser refresh persistence
 * - DevTools integration for debugging
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { WizardState, WizardStep } from '../types/store.types';

// Step order defines the wizard flow
const STEP_ORDER: WizardStep[] = ['select', 'edit', 'calculate', 'results'];

export const useWizardStore = create<WizardState>()(
  devtools(
    persist(
      (set, get) => ({
        // ================================================================
        // Initial State
        // ================================================================
        currentStep: 'select',
        completedSteps: [],
        canProceed: false,
        canGoBack: false,

        // ================================================================
        // Step Navigation
        // ================================================================
        setStep: (step: WizardStep) => {
          const currentIndex = STEP_ORDER.indexOf(get().currentStep);
          const targetIndex = STEP_ORDER.indexOf(step);

          // Prevent skipping ahead to incomplete steps
          if (targetIndex > currentIndex) {
            const allPreviousComplete = STEP_ORDER.slice(0, targetIndex).every(
              (s) => get().completedSteps.includes(s)
            );

            if (!allPreviousComplete) {
              console.warn(
                `Cannot skip to ${step} - previous steps incomplete`
              );
              return;
            }
          }

          // Update current step and navigation flags
          set({
            currentStep: step,
            canGoBack: targetIndex > 0,
            canProceed:
              get().completedSteps.includes(step) ||
              targetIndex < STEP_ORDER.length - 1,
          });
        },

        // ================================================================
        // Step Completion
        // ================================================================
        markStepComplete: (step: WizardStep) => {
          set((state) => ({
            completedSteps: [...new Set([...state.completedSteps, step])],
            canProceed: true,
          }));
        },

        markStepIncomplete: (step: WizardStep) => {
          set((state) => ({
            completedSteps: state.completedSteps.filter((s) => s !== step),
            canProceed: false,
          }));
        },

        // ================================================================
        // Navigation Helpers
        // ================================================================
        goNext: () => {
          const currentIndex = STEP_ORDER.indexOf(get().currentStep);
          if (currentIndex < STEP_ORDER.length - 1) {
            get().setStep(STEP_ORDER[currentIndex + 1]);
          }
        },

        goBack: () => {
          const currentIndex = STEP_ORDER.indexOf(get().currentStep);
          if (currentIndex > 0) {
            get().setStep(STEP_ORDER[currentIndex - 1]);
          }
        },

        // ================================================================
        // Reset
        // ================================================================
        reset: () => {
          set({
            currentStep: 'select',
            completedSteps: [],
            canProceed: false,
            canGoBack: false,
          });
        },
      }),
      {
        name: 'pcf-wizard-storage', // localStorage key
        // Only persist essential state (not computed flags)
        partialize: (state) => ({
          currentStep: state.currentStep,
          completedSteps: state.completedSteps,
        }),
      }
    ),
    { name: 'WizardStore' } // DevTools name
  )
);
