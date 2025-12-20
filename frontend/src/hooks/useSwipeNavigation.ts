/**
 * useSwipeNavigation Hook
 * TASK-FE-P7-011: Touch-Friendly Interactions
 *
 * STUB FILE - Implementation pending.
 * This stub exists to allow tests to run and fail properly.
 *
 * TODO: Implement swipe gesture navigation using react-swipeable
 */

// This is a stub that will cause tests to fail
// The real implementation will use react-swipeable and useBreakpoints

export interface SwipeNavigationOptions {
  /** Called when user swipes left (next) */
  onSwipeLeft?: () => void;
  /** Called when user swipes right (previous) */
  onSwipeRight?: () => void;
  /** Minimum swipe distance in pixels (default: 50) */
  threshold?: number;
  /** Whether swipe is currently enabled (default: true) */
  enabled?: boolean;
  /** Prevent swipe when touching form elements (default: true) */
  preventOnFormElements?: boolean;
}

export interface SwipeNavigationResult {
  /** Spread these handlers on the swipeable container */
  handlers: Record<string, unknown>;
  /** Direction of last swipe (null if none) */
  lastSwipeDirection: 'left' | 'right' | null;
  /** Whether swipe navigation is active */
  isSwipeActive: boolean;
}

/**
 * Hook for swipe-based navigation, optimized for mobile wizard flows.
 * Only active on mobile/tablet viewports.
 *
 * @param options Configuration options
 * @returns Swipe handlers and state
 *
 * @example
 * const { handlers } = useSwipeNavigation({
 *   onSwipeLeft: () => goToNextStep(),
 *   onSwipeRight: () => goToPreviousStep(),
 * });
 *
 * return <div {...handlers}>Swipeable Content</div>;
 */
export function useSwipeNavigation(
  _options: SwipeNavigationOptions = {}
): SwipeNavigationResult {
  // STUB: This will cause tests to fail
  // Real implementation should use react-swipeable and useBreakpoints
  throw new Error('useSwipeNavigation not implemented');
}

export default useSwipeNavigation;
