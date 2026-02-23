/**
 * SourceBadge Component
 *
 * Inline source indicator with link to attribution section.
 * Displays a short code like [EPA], [DEF] that links
 * to the corresponding attribution anchor.
 *
 * Used in BOM tables and emission factor displays.
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 * TASK-FIX-P8-003: Support for derived factors with multiple sources
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { SOURCE_CONFIG } from './DataSourceAttribution';

interface SourceBadgeProps {
  /** Source code (e.g., 'EPA', 'DEFRA') or comma-separated sources for derived factors */
  sourceCode: string;
  /** Optional className for additional styling */
  className?: string;
}

/**
 * Single source badge - renders one clickable badge
 */
const SingleBadge: React.FC<{ source: string; className?: string }> = ({ source, className }) => {
  const trimmedSource = source.trim();
  const config = SOURCE_CONFIG[trimmedSource] || SOURCE_CONFIG[trimmedSource.toUpperCase()];

  if (!config) {
    return <span className={className}>{trimmedSource}</span>;
  }

  return (
    <a
      href={`#${config.anchor}`}
      className={cn(
        'font-bold no-underline hover:underline transition-colors',
        config.color,
        className
      )}
      title={`View ${trimmedSource} data source attribution`}
    >
      [{config.shortName}]
    </a>
  );
};

/**
 * SourceBadge Component
 *
 * Renders clickable badges that link to data source attribution sections.
 * Supports single sources and comma-separated multiple sources for derived factors.
 *
 * For derived factors (e.g., "DEFRA, EPA"):
 * - Renders badges for each source
 * - Shows a derived indicator (*)
 */
export const SourceBadge: React.FC<SourceBadgeProps> = ({ sourceCode, className }) => {
  // Check if this is a derived factor with multiple sources
  const sources = sourceCode.split(',').map(s => s.trim()).filter(s => s);
  const isDerived = sources.length > 1;

  if (isDerived) {
    // Render multiple badges with derived indicator
    return (
      <span className={cn('inline-flex items-center gap-0.5', className)}>
        {sources.map((source, index) => (
          <React.Fragment key={source}>
            <SingleBadge source={source} />
            {index < sources.length - 1 && <span className="text-muted-foreground">/</span>}
          </React.Fragment>
        ))}
        <span
          className="text-amber-600 ml-0.5 cursor-help"
          title="Derived factor: calculated from multiple emission factor sources"
        >
          *
        </span>
      </span>
    );
  }

  // Single source - use simple rendering
  return <SingleBadge source={sourceCode} className={className} />;
};

export default SourceBadge;
