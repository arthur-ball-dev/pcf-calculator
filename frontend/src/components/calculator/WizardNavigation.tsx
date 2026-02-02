/**
 * WizardNavigation Component
 *
 * Provides navigation controls for the wizard workflow:
 * - Previous button (enabled when canGoBack is true)
 * - Next button (enabled when canProceed is true, with tooltip when disabled)
 * - Start Over button (shown on steps 2-3, with confirmation dialog, destructive variant)
 * - New Calculation button (shown on final step)
 *
 * Features:
 * - Integration with wizardStore and calculatorStore
 * - Triggers calculation when advancing from BOM step
 * - CalculationOverlay for progress feedback
 * - Confirmation dialog for reset action
 * - Keyboard accessible
 * - ARIA labels for screen readers
 * - Visual feedback for disabled states (tooltips)
 * - Mobile-responsive layout (TASK-FE-P7-009)
 *   - Full-width buttons on mobile
 *   - Auto-width buttons on tablet/desktop
 *   - Minimum touch target size (44px)
 */

import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, RotateCcw, Calculator } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useCalculation } from '@/hooks/useCalculation';
import { CalculationOverlay } from './CalculationOverlay';

/**
 * WizardNavigation component
 */
const WizardNavigation: React.FC = () => {
  const { currentStep, canGoBack, canProceed, goBack, goNext, reset } =
    useWizardStore();
  const { calculation } = useCalculatorStore();
  const { isCalculating, error, elapsedSeconds, startCalculation, stopPolling } =
    useCalculation();

  const [showOverlay, setShowOverlay] = useState(false);
  const isLastStep = currentStep === 'results';
  const isEditStep = currentStep === 'edit';

  /**
   * Close overlay when calculation completes successfully
   * (The hook auto-advances to results, so we just close the overlay)
   */
  useEffect(() => {
    if (calculation?.status === 'completed' && showOverlay && !isCalculating) {
      setShowOverlay(false);
    }
  }, [calculation?.status, showOverlay, isCalculating]);

  /**
   * Handle reset action - resets both wizard and calculator stores
   */
  const handleReset = () => {
    reset();
    useCalculatorStore.getState().reset();
  };

  /**
   * Handle Next button click
   * On BOM step, trigger calculation instead of direct navigation
   */
  const handleNext = () => {
    if (isEditStep) {
      // Start calculation and show overlay
      setShowOverlay(true);
      startCalculation();
    } else {
      goNext();
    }
  };

  /**
   * Handle calculation cancel
   */
  const handleCancel = () => {
    stopPolling();
    setShowOverlay(false);
  };

  /**
   * Handle retry after error
   */
  const handleRetry = () => {
    startCalculation();
  };

  /**
   * Get appropriate Next button text
   */
  const getNextButtonText = () => {
    if (isEditStep) {
      return 'Calculate';
    }
    return 'Next';
  };

  /**
   * Get appropriate Next button icon
   */
  const getNextButtonIcon = () => {
    if (isEditStep) {
      return <Calculator className="w-4 h-4" />;
    }
    return <ChevronRight className="w-4 h-4" />;
  };

  // Disable Next button during calculation
  const isNextDisabled = !canProceed || isCalculating;

  return (
    <>
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 sm:gap-4">
        {/* Previous button - full width on mobile, auto on larger screens */}
        <Button
          variant="outline"
          onClick={goBack}
          disabled={!canGoBack || isCalculating}
          className="w-full sm:w-auto gap-2 min-h-11 py-3 px-4 sm:px-6"
          aria-label="Previous step"
          data-testid="previous-button"
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </Button>

        {/* Center: Start Over button (hidden on first step) */}
        {currentStep !== 'select' && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="destructive"
                size="sm"
                className="w-full sm:w-auto gap-2 min-h-11 py-3"
                disabled={isCalculating}
                data-testid="start-over-button"
              >
                <RotateCcw className="w-4 h-4" />
                Start Over
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="mx-4 sm:mx-0">
              <AlertDialogHeader>
                <AlertDialogTitle>Reset Calculator?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will clear all your current selections and progress. This
                  action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter className="flex-col sm:flex-row gap-2 sm:gap-0">
                <AlertDialogCancel className="min-h-11">Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleReset} className="min-h-11">Reset</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}

        {/* Next button (or New Calculation on last step) with tooltip */}
        {!isLastStep ? (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="inline-block w-full sm:w-auto">
                  <Button
                    onClick={handleNext}
                    disabled={isNextDisabled}
                    className="w-full sm:w-auto gap-2 min-h-11 py-3 px-4 sm:px-6"
                    aria-label={isEditStep ? 'Calculate carbon footprint' : 'Next step'}
                    data-testid="next-button"
                  >
                    {getNextButtonText()}
                    {getNextButtonIcon()}
                  </Button>
                </span>
              </TooltipTrigger>
              {!canProceed && (
                <TooltipContent>
                  <p>Complete this step to continue</p>
                </TooltipContent>
              )}
            </Tooltip>
          </TooltipProvider>
        ) : (
          <Button
            variant="outline"
            onClick={handleReset}
            className="w-full sm:w-auto gap-2 min-h-11 py-3 px-4 sm:px-6"
            aria-label="Start new calculation"
            data-testid="new-calculation-button"
          >
            <RotateCcw className="w-4 h-4" />
            New Calculation
          </Button>
        )}
      </div>

      {/* Calculation overlay */}
      <CalculationOverlay
        isOpen={showOverlay}
        isCalculating={isCalculating}
        elapsedSeconds={elapsedSeconds}
        error={error}
        onCancel={handleCancel}
        onRetry={handleRetry}
      />
    </>
  );
};

export default WizardNavigation;
