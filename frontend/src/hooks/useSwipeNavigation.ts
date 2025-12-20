/**
 * useSwipeNavigation Hook
 * TASK-FE-P7-011: Touch-Friendly Interactions
 *
 * Hook for swipe-based navigation, optimized for mobile wizard flows.
 * Uses react-swipeable for gesture detection.
 * Only active on mobile/tablet viewports.
 *
 * Features:
 * - Left swipe triggers onSwipeLeft callback (e.g., next step)
 * - Right swipe triggers onSwipeRight callback (e.g., previous step)
 * - Configurable threshold for swipe distance
 * - Prevention of swipe on form elements
 * - Viewport-aware activation (mobile/tablet only)
 */

import { useCallback, useRef } from 'react';
import { useSwipeable, SwipeEventData } from 'react-swipeable';
import { useBreakpoints } from './useBreakpoints';

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
  handlers: ReturnType<typeof useSwipeable> | Record<string, never>;
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
export function useSwipeNavigation({
  onSwipeLeft,
  onSwipeRight,
  threshold = 50,
  enabled = true,
  preventOnFormElements = true,
}: SwipeNavigationOptions = {}): SwipeNavigationResult {
  const { isMobile, isTablet } = useBreakpoints();
  const lastSwipeDirection = useRef<'left' | 'right' | null>(null);

  // Swipe is only active on mobile/tablet and when enabled
  const isSwipeActive = enabled && (isMobile || isTablet);

  /**
   * Check if swipe should be prevented based on target element
   * Prevents swipe when user is interacting with form elements
   */
  const shouldPreventSwipe = useCallback(
    (event: SwipeEventData): boolean => {
      if (!preventOnFormElements) return false;

      const target = event.event.target as HTMLElement;
      const formElements = ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'];

      // Check if target or any parent is a form element
      let element: HTMLElement | null = target;
      while (element) {
        if (formElements.includes(element.tagName)) return true;
        if (element.getAttribute('role') === 'slider') return true;
        if (element.getAttribute('contenteditable') === 'true') return true;
        element = element.parentElement;
      }

      return false;
    },
    [preventOnFormElements]
  );

  /**
   * Handle left swipe (typically for "next" navigation)
   */
  const handleSwipedLeft = useCallback(
    (eventData: SwipeEventData) => {
      if (!isSwipeActive) return;
      if (shouldPreventSwipe(eventData)) return;

      lastSwipeDirection.current = 'left';
      onSwipeLeft?.();
    },
    [isSwipeActive, shouldPreventSwipe, onSwipeLeft]
  );

  /**
   * Handle right swipe (typically for "previous" navigation)
   */
  const handleSwipedRight = useCallback(
    (eventData: SwipeEventData) => {
      if (!isSwipeActive) return;
      if (shouldPreventSwipe(eventData)) return;

      lastSwipeDirection.current = 'right';
      onSwipeRight?.();
    },
    [isSwipeActive, shouldPreventSwipe, onSwipeRight]
  );

  /**
   * Configure swipeable handlers using react-swipeable
   */
  const swipeableHandlers = useSwipeable({
    onSwipedLeft: handleSwipedLeft,
    onSwipedRight: handleSwipedRight,
    delta: threshold,
    preventScrollOnSwipe: false, // Allow vertical scrolling
    trackTouch: true,
    trackMouse: false, // Only track touch events
    rotationAngle: 0,
    swipeDuration: 500,
  });

  // Return empty handlers object when swipe is inactive
  // This allows safe spreading on elements without side effects
  const handlers: SwipeNavigationResult['handlers'] = isSwipeActive
    ? swipeableHandlers
    : {};

  return {
    handlers,
    lastSwipeDirection: lastSwipeDirection.current,
    isSwipeActive,
  };
}

export default useSwipeNavigation;
