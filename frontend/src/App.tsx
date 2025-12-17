/**
 * App Component - Root component for PCF Calculator application
 *
 * Renders the main CalculationWizard component which manages the 4-step
 * wizard flow for calculating product carbon footprints.
 *
 * TASK-FE-P5-012: Integrated GuidedTour for onboarding
 * - TourProvider wraps the app to provide tour context
 * - GuidedTour renders the react-joyride tour overlay
 * - Tour starts automatically for first-time users
 *
 * Always resets to Step 1 (Select Product) on app load.
 */

import { useEffect } from 'react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { TourProvider } from '@/contexts/TourContext';
import { GuidedTour } from '@/components/Tour/GuidedTour';
import CalculationWizard from '@/components/calculator/CalculationWizard';
import { useWizardStore } from '@/store/wizardStore';
import { useCalculatorStore } from '@/store/calculatorStore';
import './App.css';

function App() {
  // Reset wizard and calculator state on app load to always start at Step 1
  useEffect(() => {
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
  }, []);

  return (
    <TooltipProvider>
      <TourProvider>
        <CalculationWizard />
        <GuidedTour />
      </TourProvider>
    </TooltipProvider>
  );
}

export default App;
