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

import React from 'react';
import { ChevronLeft, ChevronRight, RotateCcw, Calculator, Loader2 } from 'lucide-react';
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

/**
 * Props for WizardNavigation
 */
interface WizardNavigationProps {
  /** Handler to trigger calculation - managed by parent for shared overlay */
  onCalculate?: () => void;
  /** Whether calculation is in progress */
  isCalculating?: boolean;
  /** Whether navigation transition is in progress (shared with top button) */
  isNavigating?: boolean;
  /** Setter for navigation state (shared with top button) */
  setIsNavigating?: (value: boolean) => void;
}

/**
 * WizardNavigation component
 */
const WizardNavigation: React.FC<WizardNavigationProps> = ({
  onCalculate,
  isCalculating: isCalculatingProp,
  isNavigating: isNavigatingProp,
  setIsNavigating: setIsNavigatingProp,
}) => {
  const { currentStep, canGoBack, canProceed, goBack, goNext, reset } =
    useWizardStore();
  const { isLoadingBOM } = useCalculatorStore();

  const isLastStep = currentStep === 'results';
  const isEditStep = currentStep === 'edit';
  const isCalculating = isCalculatingProp ?? false;
  const isNavigating = isNavigatingProp ?? false;
  const setIsNavigating = setIsNavigatingProp ?? (() => {});

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
   * On Select step, show loading indicator before heavy BOMEditor render
   */
  const handleNext = () => {
    if (isEditStep && onCalculate) {
      // Trigger calculation via parent handler (shows overlay at wizard level)
      onCalculate();
    } else {
      // Show loading state immediately, then navigate after browser paints
      // Double rAF ensures the browser actually renders the loading state
      // before React starts the heavy BOMEditor render
      setIsNavigating(true);
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          goNext();
          // Reset after navigation completes
          setTimeout(() => setIsNavigating(false), 100);
        });
      });
    }
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

  // Disable Next button during calculation, BOM loading, or navigation transition
  const isNextDisabled = !canProceed || isCalculating || isLoadingBOM || isNavigating;

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
                    aria-label={isLoadingBOM || isNavigating ? 'Loading...' : isEditStep ? 'Calculate carbon footprint' : 'Next step'}
                    data-testid="next-button"
                  >
                    {isLoadingBOM || isNavigating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        {getNextButtonText()}
                        {getNextButtonIcon()}
                      </>
                    )}
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
    </>
  );
};

export default WizardNavigation;
