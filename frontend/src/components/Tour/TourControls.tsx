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
 * - Emerald Night dark theme styling
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
  const { hasCompletedTour, resetTour } = useTour();

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
          variant="outline"
          size="sm"
          onClick={handleClick}
          data-testid="tour-restart-button"
          aria-label={tooltipText}
          className="h-9 gap-2 border-white/20 text-emerald-400 hover:bg-white/10 hover:text-emerald-300"
        >
          <HelpCircle className="h-4 w-4" />
          <span className="text-sm font-medium">Tour</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltipText}</p>
      </TooltipContent>
    </Tooltip>
  );
}
