import { useMemo } from 'react';
import { useMediaQuery } from './useMediaQuery';

/**
 * Tailwind CSS 4 breakpoint values
 * sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px
 */
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const;

export interface BreakpointState {
  /** True when viewport <= 640px (mobile phones) */
  isMobile: boolean;
  /** True when viewport is 641px-1023px (tablets) */
  isTablet: boolean;
  /** True when viewport >= 1024px (desktops) */
  isDesktop: boolean;
  /** True when viewport >= 1280px (large desktops) */
  isLargeDesktop: boolean;
  /** Current breakpoint name */
  breakpoint: 'mobile' | 'tablet' | 'desktop' | 'largeDesktop';
}

/**
 * Convenience hook that provides named breakpoint states.
 * Follows Tailwind CSS 4 breakpoint conventions.
 *
 * @returns BreakpointState object with boolean flags and current breakpoint name
 *
 * @example
 * const { isMobile, isTablet, isDesktop, breakpoint } = useBreakpoints();
 *
 * return (
 *   <div className={isMobile ? 'p-4' : 'p-8'}>
 *     {isMobile && <MobileNav />}
 *     {isDesktop && <DesktopNav />}
 *   </div>
 * );
 */
export function useBreakpoints(): BreakpointState {
  const isMobile = useMediaQuery(`(max-width: ${BREAKPOINTS.sm}px)`);
  const isTabletOrSmaller = useMediaQuery(`(max-width: ${BREAKPOINTS.lg - 1}px)`);
  const isDesktopOrSmaller = useMediaQuery(`(max-width: ${BREAKPOINTS.xl - 1}px)`);

  return useMemo(() => {
    const isTablet = !isMobile && isTabletOrSmaller;
    const isDesktop = !isTabletOrSmaller;
    const isLargeDesktop = !isDesktopOrSmaller;

    let breakpoint: BreakpointState['breakpoint'];
    if (isMobile) breakpoint = 'mobile';
    else if (isTablet) breakpoint = 'tablet';
    else if (!isLargeDesktop) breakpoint = 'desktop';
    else breakpoint = 'largeDesktop';

    return {
      isMobile,
      isTablet,
      isDesktop,
      isLargeDesktop,
      breakpoint,
    };
  }, [isMobile, isTabletOrSmaller, isDesktopOrSmaller]);
}

export default useBreakpoints;
