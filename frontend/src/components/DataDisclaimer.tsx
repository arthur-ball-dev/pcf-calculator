/**
 * DataDisclaimer Component
 *
 * Reusable data disclaimer dialog for the PCF Calculator application.
 * Communicates that product names, BOM compositions, and quantities are
 * illustrative/fictional, while emission factors are sourced from authentic
 * EPA and DEFRA datasets.
 *
 * Used in two places:
 * 1. App footer -- persistent "Data Disclaimer" link
 * 2. Results page -- "Learn more" link in the info callout
 *
 * Uses shadcn/ui Dialog (Radix UI) for accessible modal behavior.
 * Fully keyboard navigable and screen reader friendly (WCAG 2.1 AA).
 */

import React, { useState } from 'react';
import { Info } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';

interface DataDisclaimerProps {
  /** Controlled open state (optional -- if omitted, component manages its own state) */
  open?: boolean;
  /** Callback when open state changes */
  onOpenChange?: (open: boolean) => void;
  /** Content to render as the trigger. If omitted, no trigger is rendered (use controlled mode). */
  trigger?: React.ReactNode;
}

/**
 * Full disclaimer text content -- the canonical source for the data disclaimer.
 * Reused by both the dialog body and any inline references.
 */
export const DATA_DISCLAIMER_TEXT = {
  title: 'Data Disclaimer',
  body: `This application demonstrates Product Carbon Footprint (PCF) calculation capabilities. Product names, brands, and models are fictional. Emission factors are sourced from authentic EPA and DEFRA datasets. Bill of Materials compositions and quantities are illustrative values based on industry-representative estimates. Results are for demonstration purposes and should not be used for regulatory reporting.`,
  brief: `Results are based on illustrative product data and industry-representative estimates.`,
};

/**
 * DataDisclaimer Component
 *
 * Renders a Dialog containing the full data disclaimer text.
 * Supports both controlled (open/onOpenChange) and uncontrolled modes.
 * When a trigger is provided, it wraps the trigger to open the dialog on click.
 */
export const DataDisclaimer: React.FC<DataDisclaimerProps> = ({
  open: controlledOpen,
  onOpenChange: controlledOnOpenChange,
  trigger,
}) => {
  const [internalOpen, setInternalOpen] = useState(false);

  // Use controlled state if provided, otherwise use internal state
  const isOpen = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const handleOpenChange = controlledOnOpenChange || setInternalOpen;

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      {/* Render trigger if provided -- clicking opens the dialog */}
      {trigger && (
        <button
          type="button"
          onClick={() => handleOpenChange(true)}
          className="inline-flex items-center cursor-pointer bg-transparent border-0 p-0 m-0"
          aria-label="Open data disclaimer"
        >
          {trigger}
        </button>
      )}

      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Info className="h-4 w-4 text-primary" aria-hidden="true" />
            </div>
            <DialogTitle className="text-base font-semibold">
              {DATA_DISCLAIMER_TEXT.title}
            </DialogTitle>
          </div>
          <DialogDescription className="sr-only">
            Important information about the data used in this application
          </DialogDescription>
        </DialogHeader>

        <div className="text-sm leading-relaxed text-muted-foreground">
          {DATA_DISCLAIMER_TEXT.body}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DataDisclaimer;
