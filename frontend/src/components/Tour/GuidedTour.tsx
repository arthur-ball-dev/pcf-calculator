/**
 * GuidedTour Component
 *
 * TASK-UI-P5-002: Guided Tour Onboarding - Main Component
 *
 * Renders the react-joyride tour with custom styling and configuration.
 * Uses the TourContext to manage tour state and handle callbacks.
 *
 * Features:
 * - 8 tour steps covering main features
 * - Custom tooltip styling matching app theme
 * - Keyboard navigation support (Escape to close)
 * - Skip and restart functionality
 * - Accessibility support (ARIA labels, focus management)
 *
 * Usage:
 * ```tsx
 * <TourProvider>
 *   <App />
 *   <GuidedTour />
 * </TourProvider>
 * ```
 */

import Joyride, { type TooltipRenderProps } from 'react-joyride';
import { useTour } from '@/contexts/TourContext';
import { TOUR_STEPS } from '@/config/tourSteps';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

/**
 * Custom tooltip component for consistent styling
 */
function CustomTooltip({
  continuous,
  index,
  step,
  backProps,
  closeProps,
  primaryProps,
  skipProps,
  tooltipProps,
  isLastStep,
  size,
}: TooltipRenderProps) {
  return (
    <div
      {...tooltipProps}
      role="tooltip"
      aria-describedby="tour-step-content"
      className="bg-background border rounded-lg shadow-lg p-4 max-w-sm z-[10001]"
    >
      {/* Close button */}
      <button
        {...closeProps}
        aria-label="Close tour"
        className="absolute top-2 right-2 p-1 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
      >
        <X className="h-4 w-4" />
      </button>

      {/* Step content */}
      <div id="tour-step-content" className="pr-6">
        {step.content}
      </div>

      {/* Progress indicator */}
      <div className="mt-4 text-xs text-muted-foreground">
        {index + 1} of {size}
      </div>

      {/* Navigation buttons */}
      <div className="flex justify-between items-center mt-4 gap-2">
        {/* Skip button */}
        <Button
          {...skipProps}
          variant="ghost"
          size="sm"
        >
          Skip tour
        </Button>

        <div className="flex gap-2">
          {/* Back button - hidden on first step */}
          {index > 0 && (
            <Button
              {...backProps}
              variant="outline"
              size="sm"
            >
              Previous
            </Button>
          )}

          {/* Next/Finish button */}
          <Button
            {...primaryProps}
            size="sm"
          >
            {isLastStep ? 'Finish' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * GuidedTour Component
 *
 * Renders the Joyride tour overlay with custom configuration.
 * Connects to TourContext for state management.
 */
export function GuidedTour() {
  const { isTourActive, currentStep, handleJoyrideCallback } = useTour();

  return (
    <Joyride
      steps={TOUR_STEPS}
      run={isTourActive}
      stepIndex={currentStep}
      continuous
      showProgress
      showSkipButton
      scrollToFirstStep
      disableOverlayClose={false}
      spotlightClicks={false}
      callback={handleJoyrideCallback}
      tooltipComponent={CustomTooltip}
      locale={{
        back: 'Previous',
        close: 'Close',
        last: 'Finish',
        next: 'Next',
        skip: 'Skip tour',
      }}
      styles={{
        options: {
          zIndex: 10000,
          arrowColor: 'hsl(var(--background))',
        },
        overlay: {
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
        },
        spotlight: {
          backgroundColor: 'transparent',
        },
      }}
      floaterProps={{
        styles: {
          floater: {
            filter: 'none',
          },
        },
      }}
    />
  );
}