/**
 * Disclaimer Component
 *
 * Application disclaimer for data accuracy and usage.
 * Supports full and condensed variants with expand/collapse.
 *
 * Per compliance guide requirements:
 * - Calculations are for informational purposes only
 * - No warranty on accuracy
 * - Users should consult professionals for compliance
 *
 * @see knowledge/db_compliance/External_Data_Source_Compliance_Guide.md
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface DisclaimerProps {
  /** Variant: 'full' for detailed, 'condensed' for brief */
  variant?: 'full' | 'condensed';
  /** Whether the full disclaimer is expanded by default */
  defaultExpanded?: boolean;
  /** Optional className for styling */
  className?: string;
}

/**
 * Full disclaimer text for legal compliance
 */
const FULL_DISCLAIMER = `This application uses emission factor data from multiple public sources including the U.S. EPA and UK Government (DEFRA/DESNZ).

The emission factors and calculations provided are for informational purposes only. While we strive for accuracy, no warranty is provided regarding the accuracy, completeness, or fitness for any particular purpose of the calculations or underlying data.

Users are responsible for verifying results and should consult qualified professionals for regulatory compliance, financial reporting, or legally-binding carbon accounting purposes.

The data providers (EPA, UK Government) make no warranty regarding data accuracy. See individual data source licenses for details.`;

/**
 * Condensed disclaimer for inline display
 */
const CONDENSED_DISCLAIMER = `Calculations are for informational purposes only. Verify results for regulatory or financial reporting.`;

/**
 * Disclaimer Component
 *
 * Displays legal disclaimer text in full or condensed format.
 * Full variant supports expand/collapse for space management.
 */
export const Disclaimer: React.FC<DisclaimerProps> = ({
  variant = 'full',
  defaultExpanded = true,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // Condensed variant - simple info alert
  if (variant === 'condensed') {
    return (
      <Alert className={cn('mb-2', className)} role="alert">
        <Info className="h-4 w-4" />
        <AlertTitle className="text-sm font-medium">Disclaimer</AlertTitle>
        <AlertDescription className="text-xs">
          {CONDENSED_DISCLAIMER}
          <span className="block mt-1">
            <a
              href="#disclaimer"
              className="text-primary underline text-xs"
            >
              View full disclaimer
            </a>
          </span>
        </AlertDescription>
      </Alert>
    );
  }

  // Full variant - expandable warning alert
  return (
    <Alert
      id="disclaimer"
      className={cn('mb-3 mt-2 border-amber-200 bg-amber-50', className)}
      role="alert"
    >
      <AlertTriangle className="h-4 w-4 text-amber-600" />
      <AlertTitle className="flex items-center justify-between pr-2">
        <span className="font-bold text-amber-800">DISCLAIMER</span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'collapse' : 'expand'}
          aria-controls="disclaimer-content"
        >
          {isExpanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </AlertTitle>
      <AlertDescription>
        {isExpanded ? (
          <div
            id="disclaimer-content"
            className="text-sm text-amber-900 whitespace-pre-line mt-2"
          >
            {FULL_DISCLAIMER}
          </div>
        ) : (
          <p className="text-xs text-amber-700 mt-1">
            Click to expand full disclaimer...
          </p>
        )}
      </AlertDescription>
    </Alert>
  );
};

export default Disclaimer;
