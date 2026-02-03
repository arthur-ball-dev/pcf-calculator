/**
 * CalculationOverlay Component
 *
 * Modal overlay displayed during PCF calculation.
 * Shows progress spinner, elapsed time, and allows cancellation.
 *
 * Features:
 * - Centered modal with backdrop
 * - Animated spinner
 * - Elapsed time counter
 * - Cancel button
 * - Error display with retry option
 * - Accessible with ARIA attributes
 */

import { Loader2, AlertCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { getUserFriendlyError } from '@/utils/errorMessages';

interface CalculationOverlayProps {
  isOpen: boolean;
  isCalculating: boolean;
  elapsedSeconds: number;
  error: string | null;
  onCancel: () => void;
  onRetry: () => void;
}

/**
 * CalculationOverlay Component
 *
 * Displays a modal overlay during calculation with progress feedback.
 */
export function CalculationOverlay({
  isOpen,
  isCalculating,
  elapsedSeconds,
  error,
  onCancel,
  onRetry,
}: CalculationOverlayProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="calculation-overlay-title"
      data-testid="calculation-overlay"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        aria-hidden="true"
      />

      {/* Modal content */}
      <div className="relative z-10 w-full max-w-md mx-4 bg-background rounded-xl shadow-2xl border p-8">
        {/* Calculating state */}
        {isCalculating && !error && (
          <div className="flex flex-col items-center space-y-6">
            {/* Spinner */}
            <div className="relative">
              <div className="w-20 h-20 rounded-full border-4 border-muted" />
              <Loader2
                className="absolute inset-0 w-20 h-20 text-primary animate-spin"
                data-testid="overlay-spinner"
              />
            </div>

            {/* Title */}
            <h2
              id="calculation-overlay-title"
              className="text-xl font-semibold text-center"
            >
              Calculating Carbon Footprint
            </h2>

            {/* Description */}
            <p className="text-sm text-muted-foreground text-center">
              Analyzing your Bill of Materials and calculating emissions...
            </p>

            {/* Elapsed time */}
            {elapsedSeconds > 0 && (
              <div
                className="text-sm text-muted-foreground tabular-nums"
                aria-live="polite"
                aria-atomic="true"
                data-testid="overlay-elapsed-time"
              >
                {elapsedSeconds}s elapsed
              </div>
            )}

            {/* Cancel button */}
            <Button
              variant="outline"
              onClick={onCancel}
              className="mt-4"
              data-testid="overlay-cancel-button"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Cancel
            </Button>
          </div>
        )}

        {/* Error state */}
        {error && !isCalculating && (
          <div className="flex flex-col items-center space-y-6">
            {/* Error icon */}
            <div className="w-20 h-20 rounded-full bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="w-10 h-10 text-destructive" />
            </div>

            {/* Title */}
            <h2
              id="calculation-overlay-title"
              className="text-xl font-semibold text-center"
            >
              Calculation Failed
            </h2>

            {/* Error message */}
            <Alert variant="destructive" className="w-full">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription data-testid="overlay-error-message">
                {getUserFriendlyError(error)}
              </AlertDescription>
            </Alert>

            {/* Action buttons */}
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={onCancel}
                data-testid="overlay-close-button"
              >
                Close
              </Button>
              <Button
                onClick={onRetry}
                data-testid="overlay-retry-button"
              >
                Try Again
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
