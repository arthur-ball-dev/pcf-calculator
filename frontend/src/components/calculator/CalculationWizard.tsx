/**
 * CalculationWizard Component
 *
 * Main wizard orchestrator for the PCF Calculator's 3-step workflow:
 * 1. Select Product - Choose product for calculation
 * 2. Edit BOM - Review and modify Bill of Materials (triggers calculation on Next)
 * 3. Results - View calculation results
 *
 * Features:
 * - Progress indicator showing current step and completion status
 * - Next/Previous navigation buttons (disabled based on validation)
 * - Validation gates (cannot proceed until step valid)
 * - Keyboard shortcuts (Alt+← Previous, Alt+→ Next)
 * - Start Over button with confirmation dialog
 * - Auto-advance to Results when calculation completes
 * - State persistence across browser refreshes
 * - Focus management for accessibility
 * - Screen reader announcements for step changes
 * - Mobile-responsive layout (TASK-FE-P7-009)
 * - Swipe gesture navigation on mobile/tablet (TASK-FE-P7-011)
 *
 * Emerald Night (5B) UI Rebuild - Phase 2:
 * - New header: AppLogo left, TourControls + StepProgress right
 * - InfoSection: collapsible disclaimer & attributions
 * - ContextBar: selected product context with step-specific actions
 * - Dark theme layout with glass-card styling
 *
 * Integration:
 * - wizardStore: Navigation state and step completion
 * - calculatorStore: Product selection, BOM data, calculation results
 * - WIZARD_STEPS: Step configuration with components and validation
 * - useAnnouncer: Screen reader announcements
 * - useSwipeNavigation: Touch gesture navigation
 * - useBreakpoints: JS-based responsive breakpoints for dynamic class switching
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { ArrowRight, Calculator } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useAnnouncer } from '@/hooks/useAnnouncer';
import { useSwipeNavigation } from '@/hooks/useSwipeNavigation';
import { useCalculation } from '@/hooks/useCalculation';
import { useBreakpoints } from '@/hooks/useBreakpoints';
import { WIZARD_STEPS } from '@/config/wizardSteps';
import { TourControls } from '@/components/Tour/TourControls';
import AppLogo from '@/components/common/AppLogo';
import StepProgress from '@/components/calculator/StepProgress';
import InfoSection from '@/components/common/InfoSection';
import ContextBar from '@/components/common/ContextBar';
import WizardNavigation from './WizardNavigation';
import { CalculationOverlay } from './CalculationOverlay';

/**
 * Main CalculationWizard component
 */
const CalculationWizard: React.FC = () => {
  const { currentStep, completedSteps, markStepComplete, markStepIncomplete, goNext, goBack, canProceed: wizardCanProceed } =
    useWizardStore();
  const { selectedProduct, calculation, isLoadingBOM, bomItems } = useCalculatorStore();
  const { announce } = useAnnouncer();
  const { isCalculating, error, elapsedSeconds, startCalculation, stopPolling } = useCalculation();
  const { isMobile, isTablet } = useBreakpoints();
  const hasValidatedRef = useRef(false);
  const headingRef = useRef<HTMLHeadingElement>(null);

  // Shared overlay state for both top and bottom Calculate buttons
  const [showOverlay, setShowOverlay] = useState(false);
  // Shared navigation loading state for both buttons
  const [isNavigating, setIsNavigating] = useState(false);

  // Handle calculation trigger (used by both buttons)
  const handleCalculate = useCallback(() => {
    setShowOverlay(true);
    startCalculation();
  }, [startCalculation]);

  // Handle calculation cancel
  const handleCancelCalculation = useCallback(() => {
    stopPolling();
    setShowOverlay(false);
  }, [stopPolling]);

  // Handle retry after error
  const handleRetryCalculation = useCallback(() => {
    startCalculation();
  }, [startCalculation]);

  // Close overlay when calculation completes
  useEffect(() => {
    if (calculation?.status === 'completed' && showOverlay && !isCalculating) {
      setShowOverlay(false);
    }
  }, [calculation?.status, showOverlay, isCalculating]);

  // Find current step configuration
  const currentStepConfig = WIZARD_STEPS.find((s) => s.id === currentStep);
  const CurrentStepComponent = currentStepConfig?.component;

  // Determine if we can proceed to next step (for swipe navigation)
  const canProceed = completedSteps.includes(currentStep);
  const currentStepIndex = WIZARD_STEPS.findIndex((s) => s.id === currentStep);
  const canGoBack = currentStepIndex > 0;
  const canGoForward = currentStepIndex < WIZARD_STEPS.length - 1 && canProceed;

  /**
   * Swipe navigation for mobile/tablet
   * TASK-FE-P7-011: Touch-Friendly Interactions
   */
  const { handlers: swipeHandlers, isSwipeActive } = useSwipeNavigation({
    onSwipeLeft: () => {
      if (canGoForward) {
        goNext();
      }
    },
    onSwipeRight: () => {
      if (canGoBack) {
        goBack();
      }
    },
    threshold: 50,
    enabled: true,
    preventOnFormElements: true,
  });

  /**
   * Scroll to top of page on initial load
   * Prevents browser from restoring scroll position on refresh
   */
  useEffect(() => {
    // Disable browser's automatic scroll restoration
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
    // Scroll to top immediately and after a short delay (for browser compatibility)
    window.scrollTo(0, 0);
    requestAnimationFrame(() => {
      window.scrollTo(0, 0);
    });
  }, []);

  /**
   * Focus heading and announce step change for screen readers
   * WCAG 2.1 AA requirement - focus management and announcements on dynamic content
   */
  useEffect(() => {
    if (headingRef.current && currentStepConfig) {
      headingRef.current.focus();

      // Announce step change to screen readers
      const stepIndex = WIZARD_STEPS.findIndex((s) => s.id === currentStep);
      const stepNumber = stepIndex + 1;
      const totalSteps = WIZARD_STEPS.length;
      const announcement = `Step ${stepNumber} of ${totalSteps}: ${currentStepConfig.label}`;
      announce(announcement);
    }
  }, [currentStep, currentStepConfig, announce]);

  /**
   * Validate current step when step changes
   * Skip validation if step is already marked complete (allows tests to manually control)
   */
  useEffect(() => {
    // Reset validation flag when step changes
    hasValidatedRef.current = false;

    const validateStep = async () => {
      // Skip validation if already validated or if step is already complete
      if (hasValidatedRef.current || completedSteps.includes(currentStep)) {
        return;
      }

      hasValidatedRef.current = true;

      if (currentStepConfig?.validate) {
        const isValid = await currentStepConfig.validate();
        if (isValid) {
          markStepComplete(currentStep);
        } else {
          markStepIncomplete(currentStep);
        }
      } else {
        // Steps without validation are always complete
        markStepComplete(currentStep);
      }
    };

    validateStep();
  }, [currentStep, currentStepConfig]); // markStepComplete/markStepIncomplete removed from deps to prevent infinite loop

  /**
   * Keyboard shortcuts for navigation
   * Alt+← : Navigate to previous step
   * Alt+→ : Navigate to next step
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey) {
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          useWizardStore.getState().goBack();
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          useWizardStore.getState().goNext();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  /**
   * Error fallback if step not found
   */
  if (!CurrentStepComponent) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-2">
          <p className="text-destructive font-semibold">Error: Step not found</p>
          <p className="text-sm text-muted-foreground">
            Current step: {currentStep}
          </p>
        </div>
      </div>
    );
  }

  /**
   * Extract display name from step label
   * Maps step IDs to display headings for the h2 element
   * Uses progressLabel for concise display (e.g. "Edit BOM" instead of "Edit Bill of Materials")
   */
  const getStepHeading = (): string => {
    switch (currentStep) {
      case 'select':
        return 'Select Product';
      case 'edit':
        return 'Edit BOM';
      case 'results':
        return 'Results';
      default:
        return currentStepConfig?.label || '';
    }
  };

  /**
   * Determine ContextBar props based on current step
   */
  const getContextBarProps = () => {
    if (!selectedProduct) return null;

    switch (currentStep) {
      case 'select':
        return {
          productName: selectedProduct.name,
          productCode: selectedProduct.code,
          actionLabel: `Continue with ${selectedProduct.name}`,
          actionIcon: <ArrowRight className="w-[15px] h-[15px]" />,
          onAction: goNext,
          disabled: !wizardCanProceed,
        };
      case 'edit':
        return {
          productName: selectedProduct.name,
          productCode: selectedProduct.code,
          badge: `${bomItems.length} component${bomItems.length !== 1 ? 's' : ''}`,
          actionLabel: 'Calculate PCF',
          actionIcon: <Calculator className="w-[15px] h-[15px]" />,
          onAction: handleCalculate,
          disabled: !wizardCanProceed || isCalculating || isLoadingBOM,
        };
      case 'results':
        // No context bar on results - hero section shows the info
        return null;
      default:
        return null;
    }
  };

  const contextBarProps = getContextBarProps();

  /**
   * Dynamic responsive classes via JS-based breakpoints.
   * These work with JSDOM tests where CSS media queries don't apply.
   * Static Tailwind responsive prefixes (sm:, md:, lg:) are also included
   * for real browser CSS behavior.
   *
   * Note: Using template strings (not cn/tailwind-merge) to preserve all classes
   * since both static responsive prefixes and dynamic overrides must coexist.
   */
  const mainPadding = isMobile ? 'p-4' : isTablet ? 'p-6' : 'p-8';
  const headingSize = isMobile ? 'text-xl' : isTablet ? 'text-2xl' : 'text-3xl';
  const stepIndicatorDirection = isMobile ? 'flex-col' : 'flex-row';

  return (
    <div className="min-h-screen flex flex-col">
      {/* Page wrapper */}
      <div
        {...swipeHandlers}
        data-testid="wizard-container"
        data-swipe-active={isSwipeActive}
        className="max-w-[1280px] mx-auto w-full px-4 sm:px-8 flex-1 flex flex-col"
      >
        {/* Header: AppLogo left, TourControls + StepProgress right */}
        <header
          className={cn(
            'py-6 flex items-center justify-between',
            'border-b border-[var(--card-border)] mb-8',
            // Mobile: stack vertically
            'max-[768px]:flex-col max-[768px]:gap-4 max-[768px]:items-start'
          )}
          role="banner"
        >
          <AppLogo />
          <div className="flex items-center gap-4">
            <TourControls />
            <div
              data-testid="step-indicator"
              className={`${stepIndicatorDirection} flex items-center`}
            >
              <StepProgress steps={WIZARD_STEPS} currentStep={currentStep} />
            </div>
          </div>
        </header>

        {/* Main content area - responsive padding and overflow control */}
        {/* Template string preserves both static Tailwind responsive prefixes and JS-dynamic classes */}
        <main
          role="main"
          className={`flex-1 w-full overflow-x-hidden p-4 ${mainPadding} sm:p-6 md:p-8 lg:p-8`}
        >
          {/* InfoSection - collapsible disclaimer & attributions */}
          <InfoSection />

          {/* ContextBar - shown when product selected, content varies by step */}
          {contextBarProps && (
            <ContextBar
              productName={contextBarProps.productName}
              productCode={contextBarProps.productCode}
              badge={contextBarProps.badge}
              actionLabel={contextBarProps.actionLabel}
              actionIcon={contextBarProps.actionIcon}
              onAction={contextBarProps.onAction}
              disabled={contextBarProps.disabled}
            />
          )}

          {/* Step heading and description */}
          <div className="mb-6">
            <h2
              ref={headingRef}
              className={`font-heading font-bold tracking-tight text-[var(--text-primary)] text-xl ${headingSize} sm:text-2xl md:text-3xl`}
              tabIndex={-1}
            >
              {getStepHeading()}
            </h2>
            <p className="text-[var(--text-muted)] text-[0.9375rem]">
              {currentStepConfig.description}
            </p>
          </div>

          {/* Current step component */}
          <div className="mb-6 sm:mb-8">
            <CurrentStepComponent />
          </div>

          {/* Navigation controls */}
          <div className="border-t border-[var(--card-border)] pt-4 sm:pt-6 mt-6 sm:mt-8 pb-8">
            <WizardNavigation
              onCalculate={handleCalculate}
              isCalculating={isCalculating}
              isNavigating={isNavigating}
              setIsNavigating={setIsNavigating}
            />
          </div>
        </main>

        {/* Footer - semantic structure with responsive layout */}
        <footer
          role="contentinfo"
          className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 py-4 border-t border-[var(--card-border)]"
        >
          <p className="text-xs text-[var(--text-dim)]">
            PCF Calculator - Product Carbon Footprint
          </p>
        </footer>

        {/* Calculation overlay - managed at wizard level for both buttons */}
        <CalculationOverlay
          isOpen={showOverlay}
          isCalculating={isCalculating}
          elapsedSeconds={elapsedSeconds}
          error={error}
          onCancel={handleCancelCalculation}
          onRetry={handleRetryCalculation}
        />
      </div>
    </div>
  );
};

export default CalculationWizard;
