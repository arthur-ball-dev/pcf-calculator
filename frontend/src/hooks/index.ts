/**
 * Hooks Index
 *
 * Centralized export for all custom React hooks used in the PCF Calculator.
 */

// Responsive Design Hooks
export { useMediaQuery } from './useMediaQuery';
export { useBreakpoints, BREAKPOINTS } from './useBreakpoints';
export type { BreakpointState } from './useBreakpoints';

// Accessibility Hooks
export { useAnnouncer } from './useAnnouncer';

// Data Hooks
export { useCalculation } from './useCalculation';
export { useDebounce } from './useDebounce';
export { useEmissionFactors } from './useEmissionFactors';
export { useProductSearch } from './useProductSearch';
export { useExport } from './useExport';

// Tour Hooks
export { useGuidedTour } from './useGuidedTour';
