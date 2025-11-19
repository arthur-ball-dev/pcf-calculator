/**
 * ResultsSummary Component
 *
 * Displays total CO2e emissions prominently with calculation timestamp.
 * Features large typography (48px) for visual impact and clear date formatting.
 *
 * TASK-FE-009: Results Dashboard - Summary Card
 */

import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

interface ResultsSummaryProps {
  totalCO2e: number;
  unit: string;
  calculatedAt: Date;
}

/**
 * Format date to human-readable string
 * Example: "Nov 8, 2024, 3:00 PM"
 */
function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

/**
 * ResultsSummary Component
 *
 * Displays calculation results summary with total CO2e and timestamp.
 *
 * @param totalCO2e - Total carbon footprint value
 * @param unit - Unit of measurement (kg, g, etc.)
 * @param calculatedAt - Timestamp when calculation was performed
 */
export default function ResultsSummary({ totalCO2e, unit, calculatedAt }: ResultsSummaryProps) {
  return (
    <Card data-testid="results-summary">
      <CardHeader>
        <CardTitle>Total Carbon Footprint</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-bold tabular-nums" data-testid="total-co2e">
            {totalCO2e.toFixed(2)}
          </span>
          <span className="text-2xl text-muted-foreground">
            {unit} CO₂e
          </span>
        </div>
        <div className="text-sm text-muted-foreground">
          Calculated at {formatDate(calculatedAt)}
        </div>
      </CardContent>
    </Card>
  );
}
