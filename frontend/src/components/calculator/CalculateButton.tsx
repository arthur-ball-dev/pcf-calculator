/**
 * CalculateButton Component
 *
 * Primary action button that triggers PCF calculation.
 * Features:
 * - Submit calculation on click
 * - Loading state with progress indicator
 * - Error display with retry button
 * - Cancel button during calculation
 * - Disabled when BOM invalid or empty
 * - Accessible with proper ARIA attributes
 *
 * TASK-FE-007: Calculate Flow with Polling
 */

import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, AlertCircle } from 'lucide-react';
import { useCalculation } from '@/hooks/useCalculation';
import { useCalculatorStore } from '@/store/calculatorStore';
import { getUserFriendlyError } from '@/utils/errorMessages';

export function CalculateButton() {
  const { isCalculating, error, elapsedSeconds, startCalculation, stopPolling } =
    useCalculation();
  const { selectedProductId, bomItems } = useCalculatorStore();

  // Determine if button should be disabled
  const isDisabled = !selectedProductId || bomItems.length === 0 || isCalculating;

  // Get appropriate button text
  const getButtonText = () => {
    if (isCalculating) {
      return 'Calculating...';
    }
    return 'Calculate PCF';
  };

  // Handle button click
  const handleClick = () => {
    if (!isDisabled) {
      startCalculation();
    }
  };

  // Handle retry
  const handleRetry = () => {
    startCalculation();
  };

  // Handle cancel
  const handleCancel = () => {
    stopPolling();
  };

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {error && !isCalculating && (
        <Alert variant="destructive" role="alert" data-testid="calculation-error">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{getUserFriendlyError(error)}</AlertDescription>
        </Alert>
      )}

      {/* Main Action Card */}
      <div className="border rounded-lg p-8 bg-card shadow-sm">
        <div className="flex flex-col items-center justify-center space-y-6">
          {/* Instruction Text */}
          <div className="text-center space-y-2">
            <h3 className="text-lg font-semibold">Ready to Calculate</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Click the button below to run the Product Carbon Footprint calculation based on your Bill of Materials.
            </p>
          </div>

          {/* Button Group */}
          <div className="flex gap-3">
            {/* Main Calculate Button */}
            {!isCalculating && !error && (
              <Button
                onClick={handleClick}
                disabled={isDisabled}
                aria-disabled={isDisabled}
                aria-busy="false"
                className="min-w-[250px] px-8 py-6 text-lg font-bold cursor-pointer hover:scale-105 transition-transform shadow-lg"
                size="lg"
                data-testid="calculate-button"
              >
                {getButtonText()}
              </Button>
            )}

            {/* Calculating State with Cancel */}
            {isCalculating && (
              <>
                <Button
                  disabled
                  aria-busy="true"
                  className="min-w-[250px] px-8 py-6 text-lg font-bold shadow-lg"
                  size="lg"
                  data-testid="calculating-button"
                >
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" data-testid="loading-spinner" />
                  {getButtonText()}
                </Button>
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  size="lg"
                  className="px-6 py-6 text-lg font-semibold cursor-pointer hover:bg-destructive hover:text-destructive-foreground transition-colors"
                  data-testid="cancel-button"
                >
                  Cancel
                </Button>
              </>
            )}

            {/* Retry Button */}
            {error && !isCalculating && (
              <Button
                onClick={handleRetry}
                variant="default"
                size="lg"
                className="min-w-[250px] px-8 py-6 text-lg font-bold cursor-pointer hover:scale-105 transition-transform shadow-lg"
                data-testid="retry-calculation-button"
              >
                Retry
              </Button>
            )}
          </div>

          {/* Elapsed Time Indicator */}
          {isCalculating && elapsedSeconds > 0 && (
            <div
              className="text-sm text-muted-foreground"
              aria-live="polite"
              aria-atomic="true"
              data-testid="elapsed-time"
            >
              Calculating... {elapsedSeconds}s elapsed
            </div>
          )}

          {/* Helper Text */}
          {isDisabled && !isCalculating && !error && (
            <p className="text-sm text-muted-foreground text-center">
              {!selectedProductId
                ? 'Please select a product to calculate PCF'
                : bomItems.length === 0
                ? 'Please add components to the Bill of Materials'
                : ''}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
