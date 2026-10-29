/**
 * GuidedTour Component
 *
 * TASK-UI-P5-002: Guided Tour Onboarding - Main Component
 *
 * Renders the react-joyride tour with custom styling and configuration.
 * Uses the TourContext to manage tour state and handle callbacks.
 *
 * Features:
 * - 7 tour steps covering main features
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

import { useState, useEffect } from 'react';
import Joyride, { type TooltipRenderProps, type Props as JoyrideProps } from 'react-joyride';
import { useTour } from '@/contexts/TourContext';
import { TOUR_STEPS, TOUR_STEP_IDS } from '@/config/tourSteps';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

/** How often to look for data-tour targets while the page is still loading */
const ANCHOR_POLL_INTERVAL_MS = 150;

/** Give up waiting for data-tour targets after this long (covers slow first loads) */
const ANCHOR_WAIT_TIMEOUT_MS = 30000;

/**
 * Custom tooltip component for consistent styling
 */
function CustomTooltip({
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
      className="relative bg-white border border-gray-200 rounded-lg shadow-xl p-5 max-w-sm z-[10001]"
      style={{ backgroundColor: 'white' }}
    >
      {/* Close button - better positioned */}
      <button
        {...closeProps}
        aria-label="Close tour"
        className="absolute top-3 right-3 p-1.5 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <X className="h-4 w-4 text-gray-600" />
      </button>

      {/* Step content */}
      <div id="tour-step-content" className="pr-8">
        {step.content}
      </div>

      {/* Progress indicator */}
      <div className="mt-3 text-xs text-gray-500">
        {size > 1 ? `${index + 1} of ${size} on this page` : 'Tip for this step'}
      </div>

      {/* Navigation buttons */}
      <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-100 gap-2">
        {/* Skip button */}
        <Button
          {...skipProps}
          variant="ghost"
          size="sm"
          className="text-gray-500 hover:text-gray-700"
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
            className="bg-blue-600 hover:bg-blue-700 text-white"
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
  const { isTourActive, handleJoyrideCallback } = useTour();
  const [validSteps, setValidSteps] = useState<typeof TOUR_STEPS>([]);
  const [isReady, setIsReady] = useState(false);

  // Filter steps to only include those with valid targets in the DOM.
  // Targets can render late (e.g. ProductList shows a skeleton while data loads),
  // so keep checking until at least one target exists or the wait times out.
  useEffect(() => {
    if (!isTourActive) {
      setValidSteps([]);
      setIsReady(false);
      return;
    }

    const findValidSteps = () =>
      TOUR_STEPS.filter((_, index) => {
        const targetId = TOUR_STEP_IDS[index];
        return document.querySelector(`[data-tour="${targetId}"]`) !== null;
      });

    const startedAt = Date.now();
    const intervalId = setInterval(() => {
      const filtered = findValidSteps();
      if (filtered.length > 0 || Date.now() - startedAt >= ANCHOR_WAIT_TIMEOUT_MS) {
        clearInterval(intervalId);
        setValidSteps(filtered);
        setIsReady(true);
      }
    }, ANCHOR_POLL_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, [isTourActive]);

  // Don't render until we've checked for valid steps
  if (!isTourActive || !isReady || validSteps.length === 0) {
    return null;
  }

  // Joyride props with disableBeacon (valid prop but not in older types)
  const joyrideProps: JoyrideProps & { disableBeacon?: boolean } = {
    steps: validSteps,
    run: isTourActive,
    continuous: true,
    showProgress: true,
    showSkipButton: true,
    scrollToFirstStep: true,
    disableBeacon: true,
    disableOverlayClose: false,
    disableScrollParentFix: true,
    spotlightClicks: false,
    callback: handleJoyrideCallback,
    tooltipComponent: CustomTooltip,
    locale: {
      back: 'Previous',
      close: 'Close',
      last: 'Finish',
      next: 'Next',
      skip: 'Skip tour',
    },
    styles: {
      options: {
        zIndex: 10000,
        arrowColor: 'white',
      },
      overlay: {
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
      },
      spotlight: {
        backgroundColor: 'transparent',
        borderRadius: 8,
      },
    },
    floaterProps: {
      placement: 'bottom',
      styles: {
        floater: {
          filter: 'none',
        },
      },
    },
  };

  return (
    <Joyride {...joyrideProps} />
  );
}
