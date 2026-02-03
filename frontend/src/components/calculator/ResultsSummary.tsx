/**
 * ResultsSummary Component
 *
 * Data-forward hero moment for PCF calculation results.
 * Features large, confident CO2e display that communicates precision and authority.
 *
 * Design Philosophy:
 * - This is the "result moment" - the memorable data visualization
 * - Large number (56px+) creates visual impact
 * - Tabular-nums ensure stable number rendering
 * - Subtle gradient background creates depth without distraction
 * - Warm cream paper feel aligns with ESG-authority aesthetic
 *
 * UI Redesign: ESG-Authority visual refresh
 * TASK-FE-009: Results Dashboard - Summary Card
 */

interface ResultsSummaryProps {
  totalCO2e: number;
  unit: string;
  calculatedAt: Date;
}

/**
 * Format number with thousand separators and fixed decimals
 * @param value - Number to format
 * @param decimals - Number of decimal places
 * @returns Formatted string with proper thousand separators
 */
function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format date to human-readable string with day name
 * Example: "29 Jan 2025 at 14:32"
 */
function formatDate(date: Date): string {
  const day = date.getDate();
  const month = new Intl.DateTimeFormat('en-US', { month: 'short' }).format(date);
  const year = date.getFullYear();
  const time = new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);

  return `${day} ${month} ${year} at ${time}`;
}

/**
 * ResultsSummary Component
 *
 * Hero display for calculation results with large CO2e value and timestamp.
 * Creates the memorable "result moment" in the wizard flow.
 *
 * @param totalCO2e - Total carbon footprint value
 * @param unit - Unit of measurement (kg, g, etc.)
 * @param calculatedAt - Timestamp when calculation was performed
 */
export default function ResultsSummary({ totalCO2e, unit, calculatedAt }: ResultsSummaryProps) {
  return (
    <div
      data-testid="results-summary"
      data-tour="results-summary"
      className="relative w-full overflow-hidden rounded-xl border bg-gradient-to-b from-card to-background shadow-sm"
    >
      {/* Subtle decorative gradient overlay */}
      <div
        className="absolute inset-0 bg-gradient-to-br from-primary/[0.02] to-transparent pointer-events-none"
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative px-6 py-10 sm:px-10 sm:py-14 text-center">
        {/* Label - small caps style */}
        <p className="text-xs sm:text-sm font-medium uppercase tracking-widest text-muted-foreground mb-4">
          Total Product Carbon Footprint
        </p>

        {/* Hero number - the main attraction */}
        <div className="flex flex-col items-center justify-center gap-1">
          <span
            className="text-5xl sm:text-6xl md:text-7xl font-bold tabular-nums text-foreground leading-none"
            data-testid="total-co2e"
          >
            {formatNumber(totalCO2e)}
          </span>
          <span className="text-lg sm:text-xl md:text-2xl font-medium text-muted-foreground mt-2">
            {unit} CO₂e
          </span>
        </div>

        {/* Timestamp - muted, secondary information */}
        <p className="mt-6 text-xs sm:text-sm text-muted-foreground">
          Calculated {formatDate(calculatedAt)}
        </p>
      </div>
    </div>
  );
}
