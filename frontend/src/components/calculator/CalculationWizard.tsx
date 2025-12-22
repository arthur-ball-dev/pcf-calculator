/**
 * CalculationWizard Component
 *
 * Main wizard orchestrator for the PCF Calculator's 4-step workflow:
 * 1. Select Product - Choose product for calculation
 * 2. Edit BOM - Review and modify Bill of Materials
 * 3. Calculate - Run PCF calculation
 * 4. Results - View calculation results
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
 * Integration:
 * - wizardStore: Navigation state and step completion
 * - calculatorStore: Product selection, BOM data, calculation results
 * - WIZARD_STEPS: Step configuration with components and validation
 * - useAnnouncer: Screen reader announcements
 * - useSwipeNavigation: Touch gesture navigation
 *
 * TASK-FE-P5-012: Added TourControls button to header for guided tour
 * TASK-FE-P7-009: Added mobile responsive layouts
 * TASK-FE-P7-011: Added swipe gesture navigation for mobile/tablet
 */

import React, { useEffect, useRef } from 'react';
import { CheckCircle2, Package } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useAnnouncer } from '@/hooks/useAnnouncer';
import { useBreakpoints } from '@/hooks/useBreakpoints';
import { useSwipeNavigation } from '@/hooks/useSwipeNavigation';
import { WIZARD_STEPS } from '@/config/wizardSteps';
import { TourControls } from '@/components/Tour/TourControls';
import WizardProgress from './WizardProgress';
import WizardNavigation from './WizardNavigation';
import { DataSourceAttributions } from '@/components/DataSourceAttributions';

/**
 * Main CalculationWizard component
 */
const CalculationWizard: React.FC = () => {
  const { currentStep, completedSteps, markStepComplete, markStepIncomplete, goNext, goBack } =
    useWizardStore();
  const { selectedProduct } = useCalculatorStore();
  const { announce } = useAnnouncer();
  const { isMobile, isTablet, isDesktop } = useBreakpoints();
  const hasValidatedRef = useRef(false);
  const headingRef = useRef<HTMLHeadingElement>(null);

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

  // Determine padding class based on viewport
  // Mobile: p-4 (16px), Tablet: p-6 (24px), Desktop: p-8 (32px)
  // Using both breakpoint-aware and CSS responsive classes for robustness
  const mainPaddingClass = cn(
    'flex-1 bg-background w-full max-w-full overflow-x-hidden',
    // Dynamic classes based on useBreakpoints hook
    isMobile && 'p-4',
    isTablet && 'p-6',
    isDesktop && 'p-8 lg:p-8',
    // CSS-only responsive fallback classes
    'sm:p-6 md:p-8'
  );

  // Step indicator layout class based on viewport
  const stepIndicatorClass = cn(
    'flex',
    isMobile && 'flex-col',
    !isMobile && 'flex-row',
    // CSS responsive fallback
    'sm:flex-row'
  );

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header with title and progress indicator */}
      <header className="border-b bg-white sticky top-0 z-50 shadow-sm" role="banner">
        <div className="container mx-auto px-4 sm:px-6 md:px-8 py-3 sm:py-4">
          <div className="flex items-center justify-between mb-3 sm:mb-4">
            <h1 className="text-xl sm:text-2xl font-semibold">PCF Calculator</h1>
            <TourControls />
          </div>
          {/* Step indicator with responsive layout */}
          <div data-testid="step-indicator" className={stepIndicatorClass}>
            <WizardProgress steps={WIZARD_STEPS} currentStep={currentStep} />
          </div>
        </div>
      </header>

      {/* Main content area - renders current step component */}
      {/* Swipe handlers are applied for mobile/tablet navigation */}
      <main
        {...swipeHandlers}
        data-testid="wizard-container"
        data-swipe-active={isSwipeActive}
        className={mainPaddingClass}
        role="main"
      >
        <div className="container mx-auto max-w-[1800px]">
          {/* Selected product indicator - shown when product is selected */}
          {selectedProduct && currentStep !== 'select' && (
            <div className="mb-3 sm:mb-4 p-2 sm:p-3 bg-muted/50 rounded-lg flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-3">
              <Package className="w-5 h-5 text-primary flex-shrink-0" />
              <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                <span className="text-xs sm:text-sm text-muted-foreground">Selected Product:</span>
                <span className="font-medium text-sm sm:text-base">{selectedProduct.name}</span>
                <span className="text-xs sm:text-sm text-muted-foreground">({selectedProduct.code})</span>
              </div>
            </div>
          )}

          {/* Step heading and description with completion indicator */}
          <div className="mb-4 sm:mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-4">
              <div>
                {/* Heading with mobile-first responsive text sizes: text-xl sm:text-2xl md:text-3xl */}
                <h2
                  ref={headingRef}
                  className="text-xl sm:text-2xl md:text-3xl font-semibold"
                  tabIndex={-1}
                >
                  {currentStepConfig.label}
                </h2>
                <p className="text-sm sm:text-base text-muted-foreground mt-1">
                  {currentStepConfig.description}
                </p>
              </div>
              {completedSteps.includes(currentStep) && (
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Complete</span>
                </div>
              )}
            </div>
          </div>

          {/* Current step component with responsive grid */}
          <div className="mb-6 sm:mb-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              <div className="md:col-span-2 lg:col-span-3">
                <CurrentStepComponent />
              </div>
            </div>
          </div>

          {/* Navigation controls - follows content instead of fixed footer */}
          <div className="border-t pt-4 sm:pt-6 mt-6 sm:mt-8">
            <WizardNavigation />
          </div>
        </div>
      </main>

      {/* Data source attributions footer */}
      <footer role="contentinfo" id="attributions" className="flex flex-col sm:flex-row gap-2 sm:gap-4">
        <DataSourceAttributions variant="footer" />
      </footer>
    </div>
  );
};

export default CalculationWizard;
