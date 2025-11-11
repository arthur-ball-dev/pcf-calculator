/**
 * App Component - Root component for PCF Calculator application
 *
 * Renders the main CalculationWizard component which manages the 4-step
 * wizard flow for calculating product carbon footprints.
 */

import CalculationWizard from '@/components/calculator/CalculationWizard';
import './App.css';

function App() {
  return <CalculationWizard />;
}

export default App;
