/**
 * ResultsDisplayContent Component
 *
 * Displays PCF calculation results including:
 * - Total CO2e with unit (kg CO₂e)
 * - Breakdown by category (materials, energy, transport)
 * - Calculation metadata (ID, timestamp, calculation time)
 * - Empty/loading/error states
 *
 * TASK-FE-007: Calculate Flow with Polling
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { useCalculatorStore } from '@/store/calculatorStore';
import { EMISSION_CATEGORY_COLORS } from '@/constants/colors';
import { getUserFriendlyError } from '@/utils/errorMessages';

/**
 * Format number with 2 decimal places and thousands separator
 */
function formatNumber(value: number | undefined): string {
  if (value === undefined || value === null) {
    return '0.00';
  }
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Calculate percentage of total
 */
function calculatePercentage(part: number | undefined, total: number | undefined): string {
  if (!part || !total || total === 0) {
    return '0.0';
  }
  return ((part / total) * 100).toFixed(1);
}

/**
 * Format date for display
 */
function formatDate(dateString: string | undefined): string {
  if (!dateString) {
    return 'N/A';
  }
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function ResultsDisplayContent() {
  const { calculation } = useCalculatorStore();

  // No calculation available
  if (!calculation) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          No calculation results available. Please complete a calculation first.
        </AlertDescription>
      </Alert>
    );
  }

  // Pending or in progress
  if (calculation.status === 'pending' || calculation.status === 'in_progress') {
    return (
      <Alert>
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertDescription>
          Calculation in progress. Please wait...
        </AlertDescription>
      </Alert>
    );
  }

  // Failed
  if (calculation.status === 'failed') {
    const errorMessage = calculation.error_message || 'An error occurred during calculation.';
    const friendlyError = getUserFriendlyError(errorMessage);

    return (
      <Alert variant="destructive" role="alert">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          <strong>Calculation Failed</strong>
          <br />
          {friendlyError}
        </AlertDescription>
      </Alert>
    );
  }

  // Completed - display results
  const total = calculation.total_co2e_kg;
  const materials = calculation.materials_co2e;
  const energy = calculation.energy_co2e;
  const transport = calculation.transport_co2e;

  return (
    <div className="space-y-6">
      {/* Total CO2e Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-green-600" />
            Total Carbon Footprint
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center">
            <div className="text-6xl font-bold text-primary mb-2">
              {formatNumber(total)}
            </div>
            <div className="text-2xl text-muted-foreground">kg CO₂e</div>
          </div>
        </CardContent>
      </Card>

      {/* Breakdown by Category */}
      <Card>
        <CardHeader>
          <CardTitle>Emissions Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Materials */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">Materials</span>
                <span className="text-lg font-semibold">
                  {formatNumber(materials)} kg CO₂e
                </span>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${calculatePercentage(materials, total)}%`,
                    backgroundColor: EMISSION_CATEGORY_COLORS.materials,
                  }}
                />
              </div>
              <div className="text-sm text-muted-foreground text-right">
                {calculatePercentage(materials, total)}%
              </div>
            </div>

            <Separator />

            {/* Energy */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">Energy</span>
                <span className="text-lg font-semibold">
                  {formatNumber(energy)} kg CO₂e
                </span>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${calculatePercentage(energy, total)}%`,
                    backgroundColor: EMISSION_CATEGORY_COLORS.energy,
                  }}
                />
              </div>
              <div className="text-sm text-muted-foreground text-right">
                {calculatePercentage(energy, total)}%
              </div>
            </div>

            <Separator />

            {/* Transport */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-medium">Transport</span>
                <span className="text-lg font-semibold">
                  {formatNumber(transport)} kg CO₂e
                </span>
              </div>
              <div className="w-full bg-secondary h-2 rounded-full overflow-hidden">
                <div
                  className="h-full"
                  style={{
                    width: `${calculatePercentage(transport, total)}%`,
                    backgroundColor: EMISSION_CATEGORY_COLORS.transport,
                  }}
                />
              </div>
              <div className="text-sm text-muted-foreground text-right">
                {calculatePercentage(transport, total)}%
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Calculation Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Calculation Details</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                Calculation ID
              </dt>
              <dd className="text-sm font-mono">{calculation.id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">
                Calculated At
              </dt>
              <dd className="text-sm">{formatDate(calculation.created_at)}</dd>
            </div>
            {calculation.calculation_time_ms && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Calculation Time
                </dt>
                <dd className="text-sm">
                  {calculation.calculation_time_ms < 1000
                    ? `${calculation.calculation_time_ms} ms`
                    : `${(calculation.calculation_time_ms / 1000).toFixed(2)} s`}
                </dd>
              </div>
            )}
            {calculation.product_id && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">
                  Product ID
                </dt>
                <dd className="text-sm font-mono">{calculation.product_id}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>
    </div>
  );
}
