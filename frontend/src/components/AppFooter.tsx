/**
 * AppFooter Component
 *
 * Persistent application footer displayed at the bottom of every page.
 * Contains a subtle "Data Disclaimer" link that opens the shared
 * DataDisclaimer dialog.
 *
 * Design:
 * - Muted text, small font size, consistent with ESG-authority aesthetic
 * - Works on both mobile and desktop
 * - WCAG 2.1 AA compliant (keyboard navigable, sufficient contrast)
 *
 * Note: Uses <div> rather than <footer> to avoid duplicate "contentinfo"
 * landmarks, since the page already has a semantic <footer> for
 * DataSourceAttributions.
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { DataDisclaimer } from '@/components/DataDisclaimer';

interface AppFooterProps {
  /** Additional CSS classes */
  className?: string;
}

/**
 * AppFooter Component
 *
 * Renders a minimal footer area with a "Data Disclaimer" link.
 * The link opens a Dialog with the full disclaimer text.
 */
export const AppFooter: React.FC<AppFooterProps> = ({ className }) => {
  const [disclaimerOpen, setDisclaimerOpen] = useState(false);

  return (
    <div
      className={cn(
        'border-t bg-muted/20 px-4 py-3 text-center',
        className
      )}
      aria-label="Data disclaimer"
      data-testid="app-footer"
    >
      <p className="text-xs text-muted-foreground">
        <button
          type="button"
          onClick={() => setDisclaimerOpen(true)}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 decoration-muted-foreground/40 hover:decoration-foreground/60 transition-colors cursor-pointer bg-transparent border-0 p-0 m-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded-sm"
          aria-label="Open data disclaimer"
          data-testid="footer-data-disclaimer-link"
        >
          Data Disclaimer
        </button>
      </p>

      <DataDisclaimer
        open={disclaimerOpen}
        onOpenChange={setDisclaimerOpen}
      />
    </div>
  );
};

export default AppFooter;
