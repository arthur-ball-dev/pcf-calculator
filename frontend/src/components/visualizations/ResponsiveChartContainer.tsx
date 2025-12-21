/**
 * ResponsiveChartContainer Component
 * TASK-FE-P7-013: Visualization Responsiveness
 *
 * Responsive container for Nivo charts that handles:
 * - Viewport-based height adjustments (300px mobile, 400px tablet, 500px desktop)
 * - Horizontal scrolling for complex charts on mobile
 * - Aspect ratio maintenance
 * - Loading states with skeleton
 * - Scroll indicator for touch devices
 *
 * @example
 * <ResponsiveChartContainer
 *   minHeight={500}
 *   mobileHeight={300}
 *   tabletHeight={400}
 *   enableScroll
 *   minWidth={600}
 * >
 *   <ResponsiveSankey data={data} />
 * </ResponsiveChartContainer>
 */

import { useRef, useEffect, useState, type ReactNode } from 'react';
import { useBreakpoints, BREAKPOINTS } from '@/hooks/useBreakpoints';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

/**
 * Default responsive heights per spec:
 * - Mobile (<=640px): 300px
 * - Tablet (641px-1023px): 400px
 * - Desktop (>=1024px): 500px
 */
const DEFAULT_HEIGHTS = {
  mobile: 300,
  tablet: 400,
  desktop: 500,
} as const;

interface ResponsiveChartContainerProps {
  children: ReactNode;
  /** Minimum height in pixels (desktop default) */
  minHeight?: number;
  /** Height on mobile viewports (default: 300px) */
  mobileHeight?: number;
  /** Height on tablet viewports (default: 400px or minHeight) */
  tabletHeight?: number;
  /** Minimum width before horizontal scroll (0 = no scroll) */
  minWidth?: number;
  /** Enable horizontal scroll when content exceeds viewport */
  enableScroll?: boolean;
  /** Maintain aspect ratio (e.g., 16/9) - takes precedence over fixed heights */
  aspectRatio?: number;
  /** Show loading skeleton */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Accessible label for the chart container */
  'aria-label'?: string;
}

/**
 * Get current viewport breakpoint state
 * Uses window.matchMedia for accurate detection with fallback to desktop defaults
 */
function getViewportState() {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return { isMobile: false, isTablet: false };
  }

  // Use matchMedia if available for accurate detection
  const isMobile = window.matchMedia(`(max-width: ${BREAKPOINTS.sm}px)`).matches;
  const isTabletOrSmaller = window.matchMedia(`(max-width: ${BREAKPOINTS.lg - 1}px)`).matches;

  return {
    isMobile,
    isTablet: !isMobile && isTabletOrSmaller,
  };
}

/**
 * Responsive container for Nivo charts
 *
 * Provides responsive height adjustments, horizontal scrolling for complex
 * charts on mobile, aspect ratio maintenance, and loading states.
 */
export function ResponsiveChartContainer({
  children,
  minHeight = DEFAULT_HEIGHTS.desktop,
  mobileHeight = DEFAULT_HEIGHTS.mobile,
  tabletHeight,
  minWidth = 0,
  enableScroll = false,
  aspectRatio,
  isLoading = false,
  className,
  'aria-label': ariaLabel,
}: ResponsiveChartContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  // Use the breakpoints hook for reactive updates (triggers re-render on viewport change)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _breakpoints = useBreakpoints();

  // Get current viewport state directly from matchMedia for immediate accuracy
  // This ensures correct behavior on rerender even if the hook hasn't updated yet
  // The hook is kept for reactive updates, but we use getViewportState() for calculations
  const currentViewport = getViewportState();

  // Track container width for aspect ratio calculations
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Calculate height based on viewport and aspect ratio
  const calculateHeight = (): number => {
    // Aspect ratio takes precedence when provided and width is known
    if (aspectRatio && containerWidth > 0) {
      return containerWidth / aspectRatio;
    }

    // Viewport-based heights - use direct viewport check for reliability
    if (currentViewport.isMobile) return mobileHeight;
    if (currentViewport.isTablet) return tabletHeight ?? DEFAULT_HEIGHTS.tablet;
    return minHeight;
  };

  const height = calculateHeight();
  const needsScroll = enableScroll && minWidth > 0 && currentViewport.isMobile;

  // Loading state with skeleton
  if (isLoading) {
    return (
      <div
        ref={containerRef}
        data-testid="responsive-chart-container"
        className={cn('relative', className)}
        style={{ height }}
        aria-label={ariaLabel}
        aria-busy="true"
        role="img"
      >
        <Skeleton
          data-testid="chart-loading-skeleton"
          className="w-full h-full rounded-lg"
        />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      data-testid="responsive-chart-container"
      className={cn(
        'relative',
        needsScroll && 'overflow-x-auto overflow-y-hidden',
        className
      )}
      style={{ height }}
      role="img"
      aria-label={ariaLabel}
    >
      {needsScroll ? (
        <div style={{ minWidth, height: '100%' }}>
          {children}
        </div>
      ) : (
        children
      )}

      {/* Scroll indicator for mobile when scroll is enabled */}
      {needsScroll && (
        <div
          className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1 items-center"
          aria-hidden="true"
        >
          <span className="text-xs text-muted-foreground">
            Swipe to explore
          </span>
          <svg
            className="w-4 h-4 text-muted-foreground animate-bounce-x"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 5l7 7m0 0l-7 7m7-7H3"
            />
          </svg>
        </div>
      )}
    </div>
  );
}

export default ResponsiveChartContainer;
