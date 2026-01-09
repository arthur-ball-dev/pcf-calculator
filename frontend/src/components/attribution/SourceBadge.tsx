/**
 * SourceBadge Component
 *
 * Inline source indicator with link to attribution section.
 * Displays a short code like [EPA], [DEF], [EXI] that links
 * to the corresponding attribution anchor.
 *
 * Used in BOM tables and emission factor displays.
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { SOURCE_CONFIG } from './DataSourceAttribution';

interface SourceBadgeProps {
  /** Source code (e.g., 'EPA', 'DEFRA', 'EXIOBASE', 'PROXY') */
  sourceCode: string;
  /** Optional className for additional styling */
  className?: string;
}

/**
 * SourceBadge Component
 *
 * Renders a clickable badge that links to the data source attribution section.
 * Unknown source codes are displayed as plain text without a link.
 */
export const SourceBadge: React.FC<SourceBadgeProps> = ({ sourceCode, className }) => {
  const config = SOURCE_CONFIG[sourceCode];

  // Unknown source - render as plain text
  if (!config) {
    return <span className={className}>{sourceCode}</span>;
  }

  return (
    <a
      href={`#${config.anchor}`}
      className={cn(
        'font-semibold no-underline hover:underline transition-colors',
        config.color,
        className
      )}
      title={`View ${sourceCode} data source attribution`}
    >
      [{config.shortName}]
    </a>
  );
};

export default SourceBadge;
