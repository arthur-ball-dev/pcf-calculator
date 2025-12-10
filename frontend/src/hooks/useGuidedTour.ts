/**
 * useGuidedTour Hook
 *
 * TASK-UI-P5-002: Guided Tour Onboarding - Custom Hook
 *
 * Manages the state and behavior of the guided tour feature using react-joyride.
 * Handles localStorage persistence, step navigation, and tour lifecycle events.
 *
 * Features:
 * - Auto-starts tour for first-time users
 * - Persists completion status to localStorage
 * - Provides step navigation controls
 * - Handles Joyride callback events
 * - Stable function references for performance
 *
 * Usage:
 * ```typescript
 * const {
 *   isTourActive,
 *   currentStep,
 *   hasCompletedTour,
 *   startTour,
 *   stopTour,
 *   handleJoyrideCallback,
 * } = useGuidedTour();
 * ```
 */

import { useState, useCallback, useEffect } from 'react';
import type { CallBackProps, STATUS, ACTIONS, EVENTS } from 'react-joyride';

// Constants
export const TOUR_STORAGE_KEY = 'pcf-calculator-tour-completed';
const DEFAULT_TOTAL_STEPS = 8;

export interface UseGuidedTourOptions {
  /** Total number of tour steps (default: 8) */
  totalSteps?: number;
}

export interface UseGuidedTourReturn {
  /** Whether the tour is currently active/running */
  isTourActive: boolean;
  /** Current step index (0-based) */
  currentStep: number;
  /** Whether the user has completed the tour previously */
  hasCompletedTour: boolean;
  /** Start the tour from the beginning */
  startTour: () => void;
  /** Stop the tour without saving completion */
  stopTour: () => void;
  /** Reset tour state and start fresh */
  resetTour: () => void;
  /** Mark tour as completed and close */
  completeTour: () => void;
  /** Skip the tour and mark as completed */
  skipTour: () => void;
  /** Set current step to specific index */
  setCurrentStep: (step: number) => void;
  /** Advance to the next step */
  goToNextStep: () => void;
  /** Go back to the previous step */
  goToPreviousStep: () => void;
  /** Callback handler for Joyride events */
  handleJoyrideCallback: (data: CallBackProps) => void;
}

/**
 * Read completion status from localStorage
 */
function getStoredCompletionStatus(): boolean {
  try {
    const stored = localStorage.getItem(TOUR_STORAGE_KEY);
    return stored === 'true';
  } catch (error) {
    // localStorage may be unavailable (e.g., private browsing)
    console.error('Error reading tour completion status:', error);
    return false;
  }
}

/**
 * Save completion status to localStorage
 */
function saveCompletionStatus(completed: boolean): void {
  try {
    if (completed) {
      localStorage.setItem(TOUR_STORAGE_KEY, 'true');
    } else {
      localStorage.removeItem(TOUR_STORAGE_KEY);
    }
  } catch (error) {
    // localStorage may be unavailable (e.g., private browsing)
    console.error('Error saving tour completion status:', error);
  }
}

/**
 * Custom hook for managing the guided tour state
 */
export function useGuidedTour(
  options: UseGuidedTourOptions = {}
): UseGuidedTourReturn {
  const { totalSteps = DEFAULT_TOTAL_STEPS } = options;

  // Initialize state from localStorage
  const [hasCompletedTour, setHasCompletedTour] = useState<boolean>(() =>
    getStoredCompletionStatus()
  );
  const [isTourActive, setIsTourActive] = useState<boolean>(() => {
    // Start tour automatically for first-time users
    return !getStoredCompletionStatus();
  });
  const [currentStep, setCurrentStepState] = useState<number>(0);

  // Read from localStorage on mount (handles SSR)
  useEffect(() => {
    const completed = getStoredCompletionStatus();
    setHasCompletedTour(completed);
    if (!completed) {
      setIsTourActive(true);
    }
  }, []);

  /**
   * Set current step with bounds checking
   */
  const setCurrentStep = useCallback(
    (step: number) => {
      const clampedStep = Math.max(0, Math.min(step, totalSteps - 1));
      setCurrentStepState(clampedStep);
    },
    [totalSteps]
  );

  /**
   * Start the tour from the beginning
   */
  const startTour = useCallback(() => {
    setCurrentStepState(0);
    setIsTourActive(true);
  }, []);

  /**
   * Stop the tour without marking as completed
   */
  const stopTour = useCallback(() => {
    setIsTourActive(false);
  }, []);

  /**
   * Mark tour as completed and close
   */
  const completeTour = useCallback(() => {
    setIsTourActive(false);
    setHasCompletedTour(true);
    saveCompletionStatus(true);
  }, []);

  /**
   * Skip the tour and mark as completed
   */
  const skipTour = useCallback(() => {
    setIsTourActive(false);
    setHasCompletedTour(true);
    saveCompletionStatus(true);
  }, []);

  /**
   * Reset tour state and start fresh
   */
  const resetTour = useCallback(() => {
    saveCompletionStatus(false);
    setHasCompletedTour(false);
    setCurrentStepState(0);
    setIsTourActive(true);
  }, []);

  /**
   * Advance to the next step
   */
  const goToNextStep = useCallback(() => {
    setCurrentStepState((prev) => Math.min(prev + 1, totalSteps - 1));
  }, [totalSteps]);

  /**
   * Go back to the previous step
   */
  const goToPreviousStep = useCallback(() => {
    setCurrentStepState((prev) => Math.max(prev - 1, 0));
  }, []);

  /**
   * Handle Joyride callback events
   */
  const handleJoyrideCallback = useCallback(
    (data: CallBackProps) => {
      const { status, action, index, type } = data;

      // Type guards for status and action
      const finishedStatuses: string[] = ['finished', 'skipped'];
      const closeActions: string[] = ['close', 'skip'];

      // Handle tour completion
      if (finishedStatuses.includes(status as string)) {
        completeTour();
        return;
      }

      // Handle close/skip actions
      if (closeActions.includes(action as string)) {
        completeTour();
        return;
      }

      // Handle step navigation on step:after event
      if (type === 'step:after') {
        if (action === 'next') {
          // Advance to next step
          setCurrentStepState((prev) => Math.min(prev + 1, totalSteps - 1));
        } else if (action === 'prev') {
          // Go back to previous step
          setCurrentStepState((prev) => Math.max(prev - 1, 0));
        }
      }
    },
    [completeTour, totalSteps]
  );

  return {
    isTourActive,
    currentStep,
    hasCompletedTour,
    startTour,
    stopTour,
    resetTour,
    completeTour,
    skipTour,
    setCurrentStep,
    goToNextStep,
    goToPreviousStep,
    handleJoyrideCallback,
  };
}