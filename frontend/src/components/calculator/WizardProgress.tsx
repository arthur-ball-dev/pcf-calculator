/**
 * WizardProgress Component
 *
 * Displays a visual progress indicator for the 3-step wizard workflow.
 * Shows current step, completed steps, and allows clicking on accessible steps.
 *
 * Features:
 * - Refined numbered badges (28px) with intentional visual hierarchy
 * - Progress line with 2px rounded caps and animated fill
 * - Compact badges maintain 44px touch hitbox invisibly
 * - Active step with subtle pulse animation on first render
 * - Typography uses tabular-nums for consistent number width
 * - Keyboard accessible with ARIA labels
 * - Mobile-responsive layout (TASK-FE-P7-009)
 *
 * UI Redesign: ESG-Authority visual refresh
 *
 * Props:
 * - steps: Array of step configurations
 * - currentStep: Current wizard step ID
 */

import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWizardStore } from '@/store/wizardStore';
import type { StepConfig, WizardStep } from '@/types/store.types';

interface WizardProgressProps {
  steps: StepConfig[];
  currentStep: WizardStep;
}

/**
 * Short labels for each step for accessibility and testing
 * (3-step wizard: select, edit, results)
 */
const STEP_SHORT_LABELS: Record<string, string> = {
  select: 'Select Product',
  edit: 'Edit BOM',
  results: 'Results',
};

export default function WizardProgress({
  steps,
  currentStep,
}: WizardProgressProps) {
  const { completedSteps, setStep } = useWizardStore();

  // Calculate progress percentage
  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);
  const progressPercent =
    steps.length > 1
      ? (currentStepIndex / (steps.length - 1)) * 100
      : 0;

  return (
    <div className="relative w-full py-2">
      {/* Progress line background - 2px with rounded caps */}
      <div
        className="absolute top-1/2 -translate-y-1/2 left-4 right-4 sm:left-6 sm:right-6 h-0.5 bg-border rounded-full"
        aria-hidden="true"
      >
        {/* Progress line fill - animated with smooth transition */}
        <div
          className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Steps */}
      <ol
        className="relative flex flex-row justify-between"
        aria-label="Wizard progress: 3 steps"
      >
        {steps.map((step, index) => {
          const isActive = step.id === currentStep;
          const isComplete = completedSteps.includes(step.id);

          // A step is accessible if it's the first step, or all previous steps are complete
          const isAccessible =
            index === 0 ||
            steps.slice(0, index).every((s) => completedSteps.includes(s.id));

          // Get short label for accessibility, fallback to step.label
          const shortLabel = STEP_SHORT_LABELS[step.id] || step.label;

          // Extract the display name from the label (e.g., "Step 1: Select Product" -> "Select Product")
          const displayName = step.label.includes(':')
            ? step.label.split(':').slice(1).join(':').trim()
            : step.label;

          return (
            <li key={step.id} className="flex flex-col items-center flex-1">
              {/* Invisible touch target wrapper - maintains 44px hitbox */}
              <div className="relative touch-target flex items-center justify-center">
                <button
                  type="button"
                  onClick={() => isAccessible && setStep(step.id)}
                  disabled={!isAccessible}
                  className={cn(
                    // Base styles - compact 28px badges (7 in Tailwind)
                    'relative z-10 flex items-center justify-center w-7 h-7 rounded-full transition-all duration-200',
                    'font-medium text-sm tabular-nums',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                    // Active state: Solid primary fill with subtle shadow and pulse
                    isActive && [
                      'bg-primary text-primary-foreground shadow-md',
                      'animate-pulse-once',
                    ],
                    // Complete state (not active): Check icon with success tint
                    isComplete &&
                      !isActive && [
                        'bg-primary/10 text-primary border-2 border-primary',
                      ],
                    // Pending state: Ghost outline
                    !isComplete &&
                      !isActive && [
                        'bg-background text-muted-foreground border-2 border-muted',
                      ],
                    // Disabled styling
                    !isAccessible && 'cursor-not-allowed opacity-50'
                  )}
                  aria-current={isActive ? 'step' : undefined}
                  aria-label={`Step ${index + 1} of 3: ${shortLabel}${isComplete ? ' (completed)' : ''}${isActive ? ' (current)' : ''}`}
                >
                  {isComplete && !isActive ? (
                    <Check className="w-4 h-4" strokeWidth={2.5} aria-hidden="true" />
                  ) : (
                    <span aria-hidden="true">{index + 1}</span>
                  )}
                </button>
              </div>

              {/* Step label - abbreviated on mobile, full on larger screens */}
              <span
                className={cn(
                  'mt-2 text-xs sm:text-sm font-medium text-center max-w-[70px] sm:max-w-none truncate sm:whitespace-normal',
                  isActive && 'text-foreground font-semibold',
                  isComplete && !isActive && 'text-primary',
                  !isComplete && !isActive && 'text-muted-foreground'
                )}
                aria-hidden="true"
              >
                {displayName}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
