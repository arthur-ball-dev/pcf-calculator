/**
 * CalculationWizard Component
 *
 * Main wizard orchestrator for the PCF Calculator's 4-step workflow:
 * 1. Select Product - Choose product for calculation
 * 2. Edit BOM - Review and modify Bill of Materials
 * 3. Calculate - Run PCF calculation
 * 4. Results - View calculation results
 *
 * Features:
 * - Progress indicator showing current step and completion status
 * - Next/Previous navigation buttons (disabled based on validation)
 * - Validation gates (cannot proceed until step valid)
 * - Keyboard shortcuts (Alt+← Previous, Alt+→ Next)
 * - Start Over button with confirmation dialog
 * - Auto-advance to Results when calculation completes
 * - State persistence across browser refreshes
 * - Focus management for accessibility
 * - Screen reader announcements for step changes
 *
 * Integration:
 * - wizardStore: Navigation state and step completion
 * - calculatorStore: Product selection, BOM data, calculation results
 * - WIZARD_STEPS: Step configuration with components and validation
 * - useAnnouncer: Screen reader announcements
 */

import React, { useEffect, useRef } from 'react';
import { CheckCircle2 } from 'lucide-react';
import { useWizardStore } from '@/store/wizardStore';
import { useAnnouncer } from '@/hooks/useAnnouncer';
import { WIZARD_STEPS } from '@/config/wizardSteps';
import WizardProgress from './WizardProgress';
import WizardNavigation from './WizardNavigation';

/**
 * Main CalculationWizard component
 */
const CalculationWizard: React.FC = () => {
  const { currentStep, completedSteps, markStepComplete, markStepIncomplete } =
    useWizardStore();
  const { announce } = useAnnouncer();
  const hasValidatedRef = useRef(false);
  const headingRef = useRef<HTMLHeadingElement>(null);

  // Find current step configuration
  const currentStepConfig = WIZARD_STEPS.find((s) => s.id === currentStep);
  const CurrentStepComponent = currentStepConfig?.component;

  /**
   * Focus heading and announce step change for screen readers
   * WCAG 2.1 AA requirement - focus management and announcements on dynamic content
   */
  useEffect(() => {
    if (headingRef.current && currentStepConfig) {
      headingRef.current.focus();

      // Announce step change to screen readers
      const stepIndex = WIZARD_STEPS.findIndex((s) => s.id === currentStep);
      const stepNumber = stepIndex + 1;
      const totalSteps = WIZARD_STEPS.length;
      const announcement = `Step ${stepNumber} of ${totalSteps}: ${currentStepConfig.label}`;
      announce(announcement);
    }
  }, [currentStep, currentStepConfig, announce]);

  /**
   * Validate current step when step changes
   * Skip validation if step is already marked complete (allows tests to manually control)
   */
  useEffect(() => {
    // Reset validation flag when step changes
    hasValidatedRef.current = false;

    const validateStep = async () => {
      // Skip validation if already validated or if step is already complete
      if (hasValidatedRef.current || completedSteps.includes(currentStep)) {
        return;
      }

      hasValidatedRef.current = true;

      if (currentStepConfig?.validate) {
        const isValid = await currentStepConfig.validate();
        if (isValid) {
          markStepComplete(currentStep);
        } else {
          markStepIncomplete(currentStep);
        }
      } else {
        // Steps without validation are always complete
        markStepComplete(currentStep);
      }
    };

    validateStep();
  }, [currentStep, currentStepConfig, completedSteps, markStepComplete, markStepIncomplete]);

  /**
   * Keyboard shortcuts for navigation
   * Alt+← : Navigate to previous step
   * Alt+→ : Navigate to next step
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey) {
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          useWizardStore.getState().goBack();
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          useWizardStore.getState().goNext();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  /**
   * Error fallback if step not found
   */
  if (!CurrentStepComponent) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-2">
          <p className="text-destructive font-semibold">Error: Step not found</p>
          <p className="text-sm text-muted-foreground">
            Current step: {currentStep}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header with title and progress indicator */}
      <header className="border-b bg-background" role="banner">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-semibold mb-4">PCF Calculator</h1>
          <WizardProgress steps={WIZARD_STEPS} currentStep={currentStep} />
        </div>
      </header>

      {/* Main content area - renders current step component */}
      <main className="flex-1 overflow-auto" role="main">
        <div className="container mx-auto px-4 py-8 max-w-4xl">
          {/* Step heading and description with completion indicator */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2
                  ref={headingRef}
                  className="text-xl font-semibold"
                  tabIndex={-1}
                >
                  {currentStepConfig.label}
                </h2>
                <p className="text-muted-foreground">
                  {currentStepConfig.description}
                </p>
              </div>
              {completedSteps.includes(currentStep) && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Complete</span>
                </div>
              )}
            </div>
          </div>

          {/* Current step component */}
          <div className="mb-8">
            <CurrentStepComponent />
          </div>
        </div>
      </main>

      {/* Footer with navigation controls */}
      <footer className="border-t bg-background" role="contentinfo">
        <div className="container mx-auto px-4 py-4">
          <WizardNavigation />
        </div>
      </footer>
    </div>
  );
};

export default CalculationWizard;
