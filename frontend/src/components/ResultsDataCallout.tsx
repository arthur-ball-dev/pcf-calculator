/**
 * ResultsDataCallout Component
 *
 * Subtle info callout displayed on the Results page, below the CO2e summary.
 * Communicates that results are based on illustrative data with a "Learn more"
 * link that opens the full DataDisclaimer dialog.
 *
 * Design:
 * - Unobtrusive info style -- not a warning, not alarming
 * - Small text with muted info icon
 * - "Learn more" link opens the shared DataDisclaimer dialog
 * - Consistent with ESG-authority aesthetic
 * - WCAG 2.1 AA compliant
 */

import React, { useState } from 'react';
import { Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DataDisclaimer, DATA_DISCLAIMER_TEXT } from '@/components/DataDisclaimer';

interface ResultsDataCalloutProps {
  /** Additional CSS classes */
  className?: string;
}

/**
 * ResultsDataCallout Component
 *
 * Renders a one-line info callout with the brief disclaimer text
 * and a "Learn more" link to the full disclaimer dialog.
 */
export const ResultsDataCallout: React.FC<ResultsDataCalloutProps> = ({ className }) => {
  const [disclaimerOpen, setDisclaimerOpen] = useState(false);

  return (
    <div
      className={cn(
        'flex items-start gap-2 px-4 py-2.5 rounded-lg bg-muted/40 border border-border/50',
        className
      )}
      role="note"
      aria-label="Data disclaimer notice"
      data-testid="results-data-callout"
    >
      <Info
        className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5"
        aria-hidden="true"
      />
      <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
        {DATA_DISCLAIMER_TEXT.brief}{' '}
        <button
          type="button"
          onClick={() => setDisclaimerOpen(true)}
          className="inline text-primary hover:text-primary/80 underline underline-offset-2 cursor-pointer bg-transparent border-0 p-0 m-0 text-xs sm:text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm"
          aria-label="Learn more about data disclaimer"
          data-testid="results-learn-more-link"
        >
          Learn more
        </button>
      </p>

      <DataDisclaimer
        open={disclaimerOpen}
        onOpenChange={setDisclaimerOpen}
      />
    </div>
  );
};

export default ResultsDataCallout;
