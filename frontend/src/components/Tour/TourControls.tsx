/**
 * TourControls Component
 *
 * TASK-UI-P5-002: Guided Tour Onboarding - Help Button
 *
 * Provides a help button in the application header that allows users
 * to start or restart the guided tour.
 *
 * Features:
 * - HelpCircle icon button
 * - Tooltip with contextual text (Start/Restart)
 * - Ghost variant for minimal visual footprint
 * - Accessible with proper ARIA labels
 *
 * Usage:
 * ```tsx
 * <header>
 *   <TourControls />
 * </header>
 * ```
 */

import { HelpCircle } from 'lucide-react';
import { useTour } from '@/contexts/TourContext';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

/**
 * TourControls Component
 *
 * Renders a help button that starts or restarts the guided tour.
 * Uses TourContext to access tour state and actions.
 */
export function TourControls() {
  const { hasCompletedTour, resetTour, isTourActive } = useTour();

  // Don't show restart button while tour is active
  const tooltipText = hasCompletedTour
    ? 'Restart guided tour'
    : 'Start guided tour';

  const handleClick = () => {
    resetTour();
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleClick}
          data-testid="tour-restart-button"
          aria-label={tooltipText}
          className="h-9"
        >
          <HelpCircle className="h-5 w-5" />
          <span className="sr-only">{tooltipText}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltipText}</p>
      </TooltipContent>
    </Tooltip>
  );
}