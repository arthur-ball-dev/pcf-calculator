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
 */

import { TooltipProvider } from '@/components/ui/tooltip';
import { TourProvider } from '@/contexts/TourContext';
import { GuidedTour } from '@/components/Tour/GuidedTour';
import CalculationWizard from '@/components/calculator/CalculationWizard';
import './App.css';

function App() {
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
