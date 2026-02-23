/**
 * ResultsHero Component
 *
 * Emerald Night 5B hero section for PCF calculation results.
 * Features a large PCF value display with radial emerald glow,
 * rating badges (Data Quality, ISO 14067, component count), and
 * product name context.
 *
 * Design Source: frontend/prototypes/approach-5b-single-card/03-results.html
 *
 * Replaces the previous ResultsSummary component with the Emerald Night
 * aesthetic: centered hero value, radial glow effect, glassmorphic badge pills.
 *
 * Accessibility:
 * - data-tour="results-summary" for guided tour (step 5)
 * - data-testid="results-hero" for testing
 * - Semantic heading structure
 * - Screen reader text for units and ratings
 */

interface ResultsHeroProps {
  /** Total PCF value in kg CO2e */
  totalCO2e: number;
  /** Data quality rating on 1-5 scale */
  dataQualityRating: number;
  /** Number of BOM components in the calculation */
  componentCount: number;
  /** Product name for context */
  productName: string;
}

/**
 * Convert a 1-5 data quality rating to a letter grade.
 *
 * Scale:
 * - 5:   A+
 * - 4-5: A
 * - 3-4: B+
 * - 2-3: B
 * - 1-2: C
 * - <1:  D
 */
function getRatingGrade(rating: number): string {
  if (rating >= 4.5) return 'A+';
  if (rating >= 4.0) return 'A';
  if (rating >= 3.0) return 'B+';
  if (rating >= 2.0) return 'B';
  if (rating >= 1.0) return 'C';
  return 'D';
}

/**
 * Format number with thousand separators and fixed decimals
 */
function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export default function ResultsHero({
  totalCO2e,
  dataQualityRating,
  componentCount,
  productName,
}: ResultsHeroProps) {
  const grade = getRatingGrade(dataQualityRating);

  return (
    <div
      data-tour="results-summary"
      data-testid="results-hero"
      className="relative text-center py-4 pb-10 animate-fadeInUp"
    >
      {/* Radial emerald glow behind the value */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[300px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse, rgba(16, 185, 129, 0.08) 0%, transparent 70%)',
        }}
        aria-hidden="true"
      />

      {/* Product name */}
      <p className="text-[0.9375rem] text-[var(--text-muted)] font-medium mb-3 relative">
        {productName}
      </p>

      {/* Hero PCF value */}
      <div className="relative">
        <span
          className="font-heading text-[2.5rem] sm:text-[3.5rem] font-bold text-[var(--text-primary)] leading-none tabular-nums tracking-[-0.03em]"
          data-testid="total-co2e"
        >
          {formatNumber(totalCO2e)}
        </span>
        <span className="text-base sm:text-xl font-medium text-[var(--text-muted)] ml-1.5">
          kg CO<sub>2</sub>e
        </span>
      </div>

      {/* Rating badges row */}
      <div className="flex justify-center gap-2 mt-5 flex-wrap relative">
        {/* Data Quality Rating badge */}
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[0.8125rem] font-semibold bg-[var(--accent-emerald-dim)] text-[var(--accent-emerald)]"
          data-testid="quality-badge"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3.5 h-3.5 flex-shrink-0"
            aria-hidden="true"
          >
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z" />
          </svg>
          {grade} Rating
        </span>

        {/* ISO 14067 compliance badge */}
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[0.8125rem] font-semibold bg-[var(--accent-gold-dim)] text-[var(--accent-gold)]"
          data-testid="iso-badge"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3.5 h-3.5 flex-shrink-0"
            aria-hidden="true"
          >
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          ISO 14067
        </span>

        {/* Component count badge */}
        <span
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[0.8125rem] font-semibold bg-[var(--accent-sapphire-dim)] text-[var(--accent-sapphire)]"
          data-testid="components-badge"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3.5 h-3.5 flex-shrink-0"
            aria-hidden="true"
          >
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
          </svg>
          {componentCount} Component{componentCount !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
