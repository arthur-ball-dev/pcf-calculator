/**
 * LicenseFooter Component
 *
 * Page footer with condensed attribution links.
 * Links to individual data source attributions and full disclaimer.
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Separator } from '@/components/ui/separator';

interface LicenseFooterProps {
  /** Optional className for styling */
  className?: string;
}

/**
 * LicenseFooter Component
 *
 * Displays condensed links to data sources and disclaimer.
 * Intended for page footer placement.
 */
export const LicenseFooter: React.FC<LicenseFooterProps> = ({ className }) => {
  return (
    <footer
      className={cn(
        'mt-auto py-2 px-3 bg-muted border-t text-muted-foreground text-xs',
        className
      )}
    >
      <p>
        Data sources:{' '}
        <a href="#epa-attribution" className="hover:underline text-primary">
          EPA
        </a>
        {' | '}
        <a href="#defra-attribution" className="hover:underline text-primary">
          DEFRA
        </a>
        {' | '}
        <a href="#exiobase-attribution" className="hover:underline text-primary">
          EXIOBASE
        </a>
        {' | '}
        <a href="/about#data-sources" className="hover:underline text-primary">
          Full Attribution
        </a>
      </p>
      <Separator className="my-1" />
      <p>
        See{' '}
        <a href="#disclaimer" className="hover:underline text-primary">
          Disclaimer
        </a>{' '}
        for important usage information.
      </p>
    </footer>
  );
};

export default LicenseFooter;
