/**
 * Tour Context
 *
 * TASK-UI-P5-002: Guided Tour Onboarding - Context Provider
 *
 * Provides tour state and actions to all components in the application.
 * Uses the useGuidedTour hook internally and exposes its values via context.
 *
 * Usage:
 * ```tsx
 * // Wrap your app with TourProvider
 * <TourProvider>
 *   <App />
 * </TourProvider>
 *
 * // Use the hook in any component
 * const { isTourActive, startTour } = useTour();
 * ```
 */

import {
  createContext,
  useContext,
  type ReactNode,
} from 'react';
import {
  useGuidedTour,
  type UseGuidedTourReturn,
} from '@/hooks/useGuidedTour';

/**
 * Tour context type - extends the hook return type
 */
type TourContextType = UseGuidedTourReturn;

/**
 * Tour context with undefined as default to detect usage outside provider
 */
const TourContext = createContext<TourContextType | undefined>(undefined);

/**
 * Props for TourProvider component
 */
interface TourProviderProps {
  children: ReactNode;
}

/**
 * Tour Provider Component
 *
 * Wraps the application and provides tour state to all children.
 * Must be placed high in the component tree for all components
 * that need tour functionality.
 */
export function TourProvider({ children }: TourProviderProps) {
  const tourState = useGuidedTour();

  return (
    <TourContext.Provider value={tourState}>
      {children}
    </TourContext.Provider>
  );
}

/**
 * Custom hook to access tour context
 *
 * @throws Error if used outside of TourProvider
 * @returns Tour context value with state and actions
 */
export function useTour(): TourContextType {
  const context = useContext(TourContext);

  if (context === undefined) {
    throw new Error('useTour must be used within a TourProvider');
  }

  return context;
}

// Export context for testing purposes
export { TourContext };