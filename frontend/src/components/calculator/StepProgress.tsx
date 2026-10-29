/**
 * StepProgress Component
 *
 * Pill-style step indicators for the Emerald Night wizard design.
 * Replaces the numbered-circle WizardProgress with a compact pill layout.
 *
 * Visual design (from prototype):
 * - Three pills: "1. Select Product", "2. Edit BOM", "3. Results"
 * - Active: emerald dim background, emerald text, pulsing dot
 * - Completed: emerald text, emerald dot (no background)
 * - Inactive: dim text, gray dot
 * - 24px divider lines between steps
 *
 * Accessibility:
 * - <nav> with aria-label="Wizard progress"
 * - Each step has aria-current for active
 * - Clickable when accessible (first step or all previous completed)
 * - WCAG 2.5.5: min-h-11 touch targets (44px)
 *
 * Props match the existing WizardProgress pattern for easy swap-in.
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { useWizardStore } from '@/store/wizardStore';
import type { StepConfig, WizardStep } from '@/types/store.types';

interface StepProgressProps {
  steps: StepConfig[];
  currentStep: WizardStep;
}

const StepProgress: React.FC<StepProgressProps> = ({ steps, currentStep }) => {
  const { completedSteps, setStep } = useWizardStore();

  return (
    <nav
      className="flex items-center gap-1"
      aria-label="Wizard progress"
    >
      {steps.map((step, index) => {
        const isActive = step.id === currentStep;
        const isComplete = completedSteps.includes(step.id) && !isActive;

        // A step is accessible if it's the first step, or all previous steps are complete
        const isAccessible =
          index === 0 ||
          steps.slice(0, index).every((s) => completedSteps.includes(s.id));

        // Display label: "1. Select Product", "2. Edit BOM", "3. Results"
        const displayLabel = `${index + 1}. ${step.progressLabel || step.label}`;

        const handleClick = () => {
          if (isAccessible) {
            setStep(step.id);
          }
        };

        return (
          <React.Fragment key={step.id}>
            {/* Divider line between steps */}
            {index > 0 && (
              <div
                className="w-6 h-px bg-[#475569] flex-shrink-0"
                aria-hidden="true"
              />
            )}

            {/* Step pill - min-h-11 for WCAG 2.5.5 touch target compliance */}
            <button
              type="button"
              onClick={handleClick}
              disabled={!isAccessible}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-full min-h-11',
                'text-[0.8125rem] font-medium whitespace-nowrap',
                'transition-colors duration-200',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                // Active state
                isActive && 'bg-[var(--accent-emerald-dim)] text-[var(--accent-emerald)]',
                // Completed state (not active)
                isComplete && 'text-[var(--accent-emerald)] cursor-pointer',
                // Inactive state
                !isActive && !isComplete && 'text-[var(--text-dim)]',
                // Disabled
                !isAccessible && 'cursor-default',
                isAccessible && !isActive && 'cursor-pointer'
              )}
              aria-current={isActive ? 'step' : undefined}
              aria-label={`Step ${index + 1} of ${steps.length}: ${step.progressLabel || step.label}${isComplete ? ' (completed)' : ''}${isActive ? ' (current)' : ''}`}
            >
              {/* Dot indicator */}
              <span
                className={cn(
                  'w-2 h-2 rounded-full flex-shrink-0',
                  // Active: emerald with pulse glow
                  isActive && 'bg-[var(--accent-emerald)] animate-pulse-dot',
                  // Completed: solid emerald
                  isComplete && 'bg-[var(--accent-emerald)]',
                  // Inactive: gray
                  !isActive && !isComplete && 'bg-[#475569]'
                )}
                aria-hidden="true"
              />

              {/* Label text */}
              <span>{displayLabel}</span>
            </button>
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default StepProgress;
