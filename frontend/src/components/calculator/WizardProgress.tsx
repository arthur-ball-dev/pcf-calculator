/**
 * WizardProgress Component
 *
 * Displays a visual progress indicator for the 4-step wizard workflow.
 * Shows current step, completed steps, and allows clicking on accessible steps.
 *
 * Features:
 * - Visual progress line connecting steps (enhanced prominence)
 * - Current step highlighted
 * - Completed steps marked with checkmark
 * - Inaccessible steps disabled
 * - Keyboard accessible
 * - ARIA labels for screen readers
 *
 * Props:
 * - steps: Array of step configurations
 * - currentStep: Current wizard step ID
 */

import React from 'react';
import { CheckCircle2, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWizardStore } from '@/store/wizardStore';
import type { StepConfig, WizardStep } from '@/types/store.types';

interface WizardProgressProps {
  steps: StepConfig[];
  currentStep: WizardStep;
}

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
    <div className="relative">
      {/* Progress line background - enhanced visual prominence */}
      <div
        className="absolute top-5 left-0 right-0 h-1 bg-muted rounded-full"
        aria-hidden="true"
      >
        {/* Progress line fill - enhanced with rounded corners and smooth animation */}
        <div
          className="h-full bg-primary rounded-full transition-all duration-300 ease-in-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Steps */}
      <ol
        className="relative flex justify-between"
        aria-label="Wizard progress steps"
      >
        {steps.map((step, index) => {
          const isActive = step.id === currentStep;
          const isComplete = completedSteps.includes(step.id);

          // A step is accessible if it's the first step, or all previous steps are complete
          const isAccessible =
            index === 0 ||
            steps.slice(0, index).every((s) => completedSteps.includes(s.id));

          return (
            <li key={step.id} className="flex flex-col items-center flex-1">
              <button
                type="button"
                onClick={() => isAccessible && setStep(step.id)}
                disabled={!isAccessible}
                className={cn(
                  'relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isActive &&
                    'border-primary bg-primary text-primary-foreground',
                  isComplete &&
                    !isActive &&
                    'border-primary bg-background text-primary',
                  !isComplete &&
                    !isActive &&
                    'border-muted bg-background text-muted-foreground',
                  !isAccessible && 'cursor-not-allowed opacity-50'
                )}
                aria-current={isActive ? 'step' : undefined}
                aria-label={`${step.label}${isComplete ? ' (completed)' : ''}${isActive ? ' (current)' : ''}`}
              >
                {isComplete && !isActive ? (
                  <CheckCircle2 className="w-5 h-5" aria-hidden="true" />
                ) : (
                  <Circle
                    className="w-5 h-5"
                    fill={isActive ? 'currentColor' : 'none'}
                    aria-hidden="true"
                  />
                )}
              </button>

              <span
                className={cn(
                  'mt-2 text-sm font-medium text-center',
                  isActive && 'text-foreground',
                  !isActive && 'text-muted-foreground'
                )}
                aria-hidden="true"
              >
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
