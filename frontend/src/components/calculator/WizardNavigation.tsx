/**
 * WizardNavigation Component
 *
 * Provides navigation controls for the wizard workflow:
 * - Previous button (enabled when canGoBack is true)
 * - Next button (enabled when canProceed is true, with tooltip when disabled)
 * - Start Over button (shown on steps 2-4, with confirmation dialog, destructive variant)
 * - New Calculation button (shown on final step)
 *
 * Features:
 * - Integration with wizardStore and calculatorStore
 * - Confirmation dialog for reset action
 * - Keyboard accessible
 * - ARIA labels for screen readers
 * - Visual feedback for disabled states (tooltips)
 */

import React from 'react';
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';
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
 * WizardNavigation component
 */
const WizardNavigation: React.FC = () => {
  const { currentStep, canGoBack, canProceed, goBack, goNext, reset } =
    useWizardStore();
  const isLastStep = currentStep === 'results';

  /**
   * Handle reset action - resets both wizard and calculator stores
   */
  const handleReset = () => {
    reset();
    useCalculatorStore.getState().reset();
  };

  return (
    <div className="flex items-center justify-between">
      {/* Previous button */}
      <Button
        variant="outline"
        onClick={goBack}
        disabled={!canGoBack}
        className="gap-2"
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
            <Button variant="destructive" size="sm" className="gap-2" data-testid="start-over-button">
              <RotateCcw className="w-4 h-4" />
              Start Over
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Reset Calculator?</AlertDialogTitle>
              <AlertDialogDescription>
                This will clear all your current selections and progress. This
                action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleReset}>Reset</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {/* Next button (or New Calculation on last step) with tooltip */}
      {!isLastStep ? (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-block">
                <Button
                  onClick={goNext}
                  disabled={!canProceed}
                  className="gap-2"
                  aria-label="Next step"
                  data-testid="next-button"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
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
          className="gap-2"
          aria-label="Start new calculation"
          data-testid="new-calculation-button"
        >
          <RotateCcw className="w-4 h-4" />
          New Calculation
        </Button>
      )}
    </div>
  );
};

export default WizardNavigation;
