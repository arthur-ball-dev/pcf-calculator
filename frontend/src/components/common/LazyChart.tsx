/**
 * LazyChart Component
 * TASK-FE-P7-024: Bundle Optimization with Lazy Loading
 *
 * Provides a Suspense wrapper with skeleton fallback for lazy-loaded chart components.
 * Includes error boundary for handling load failures with retry functionality.
 *
 * @example
 * import { LazyChart } from '@/components/common/LazyChart';
 * import { LazySankeyDiagram } from '@/components/visualizations';
 *
 * <LazyChart height={400}>
 *   <LazySankeyDiagram calculation={calculation} />
 * </LazyChart>
 */

import { Suspense, Component, type ReactNode, type ErrorInfo } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCw } from 'lucide-react';

// =============================================================================
// ChartErrorBoundary - Error boundary for lazy component load failures
// =============================================================================

interface ChartErrorBoundaryProps {
  children: ReactNode;
  onRetry?: () => void;
  fallback?: ReactNode;
}

interface ChartErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
}

/**
 * Error boundary specifically designed for chart components.
 * Catches load failures and provides retry functionality.
 */
export class ChartErrorBoundary extends Component<
  ChartErrorBoundaryProps,
  ChartErrorBoundaryState
> {
  constructor(props: ChartErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ChartErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error for debugging/monitoring
    console.error('Chart loading error:', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  handleRetry = (): void => {
    this.setState((state) => ({
      hasError: false,
      error: null,
      retryCount: state.retryCount + 1,
    }));
    this.props.onRetry?.();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI with retry button
      return (
        <div
          data-testid="chart-error-ui"
          className="flex flex-col items-center justify-center p-6 bg-muted/50 rounded-lg border border-dashed border-muted-foreground/25 min-h-[200px]"
        >
          <AlertCircle className="h-10 w-10 text-muted-foreground mb-4" />
          <p className="text-muted-foreground text-center mb-4">
            Unable to load chart. Please try again.
          </p>
          <Button
            data-testid="retry-button"
            variant="outline"
            size="sm"
            onClick={this.handleRetry}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
          {this.state.retryCount > 0 && (
            <p className="text-xs text-muted-foreground mt-2">
              Retry attempts: {this.state.retryCount}
            </p>
          )}
        </div>
      );
    }

    return (
      <div key={this.state.retryCount}>
        {this.props.children}
      </div>
    );
  }
}

// =============================================================================
// ChartSkeleton - Loading skeleton for charts
// =============================================================================

interface ChartSkeletonProps {
  height?: number;
  className?: string;
}

/**
 * Skeleton loading state for chart components
 */
export function ChartSkeleton({ height = 400, className }: ChartSkeletonProps): ReactNode {
  return (
    <div
      data-testid="chart-skeleton"
      className={`flex items-center justify-center ${className || ''}`}
      style={{ height }}
    >
      <Skeleton className="w-full h-full rounded-lg" />
    </div>
  );
}

// =============================================================================
// LazyChart - Main wrapper component
// =============================================================================

interface LazyChartProps {
  children: ReactNode;
  height?: number;
  fallback?: ReactNode;
  onError?: () => void;
  className?: string;
}

/**
 * Wrapper component for lazy-loaded chart components.
 * Provides Suspense boundary with skeleton fallback and error boundary.
 *
 * @param children - The lazy-loaded chart component(s)
 * @param height - Height for the skeleton fallback (default: 400)
 * @param fallback - Custom fallback component (default: ChartSkeleton)
 * @param onError - Callback when chart fails to load
 * @param className - Additional CSS classes
 */
export function LazyChart({
  children,
  height = 400,
  fallback,
  onError,
  className,
}: LazyChartProps): ReactNode {
  const defaultFallback = (
    <ChartSkeleton height={height} className={className} />
  );

  return (
    <ChartErrorBoundary onRetry={onError}>
      <Suspense fallback={fallback || defaultFallback}>
        {children}
      </Suspense>
    </ChartErrorBoundary>
  );
}

export default LazyChart;
