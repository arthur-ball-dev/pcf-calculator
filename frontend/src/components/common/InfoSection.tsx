/**
 * InfoSection Component
 *
 * Collapsible "Data Disclaimer & Attributions" panel for the Emerald Night design.
 * Replaces both DataSourceAttributions and AppFooter with a unified glassmorphic
 * collapsible panel.
 *
 * Based on prototype: approach-5b-single-card/01-select-product.html
 *
 * Features:
 * - Glassmorphic toggle button with Info icon + chevron
 * - Collapsed by default
 * - When expanded: disclaimer text, divider, attribution cards
 * - Fetches attribution data from API
 * - EPA green badge, DEFRA blue badge
 * - License info pills
 *
 * Accessibility:
 * - Toggle button with aria-expanded
 * - Expanded content revealed with smooth transition
 */

import React, { useState, useEffect } from 'react';
import { Info, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { emissionFactorsAPI } from '@/services/api/emissionFactors';
import type { DataSourceAttribution, AttributionResponse } from '@/types/api.types';

const DISCLAIMER_TEXT =
  'Product names, brands, and models are fictional. Emission factors are sourced from authentic EPA and DEFRA datasets. Bill of Materials compositions and quantities are illustrative values based on industry-representative estimates. Results are for demonstration purposes and should not be used for regulatory reporting.';

/**
 * Get the short badge label for a data source
 */
function getSourceBadge(name: string): { label: string; variant: 'epa' | 'defra' | 'default' } {
  const lower = name.toLowerCase();
  if (lower.includes('epa')) return { label: 'EPA', variant: 'epa' };
  if (lower.includes('defra') || lower.includes('desnz')) return { label: 'DEF', variant: 'defra' };
  return { label: name.slice(0, 3).toUpperCase(), variant: 'default' };
}

/**
 * Get the license summary text
 */
function getLicenseSummary(attribution: DataSourceAttribution): string {
  if (!attribution.license_type) return '';
  const requiresAttribution = attribution.requires_attribution
    ? 'attribution required'
    : 'attribution not required';
  return `${attribution.license_type} \u2014 ${requiresAttribution}`;
}

const InfoSection: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [attributionData, setAttributionData] = useState<AttributionResponse | null>(null);

  useEffect(() => {
    const fetchAttributions = async () => {
      try {
        const data = await emissionFactorsAPI.getAttributions();
        setAttributionData(data);
      } catch (err) {
        console.error('Failed to fetch attributions:', err);
      }
    };

    fetchAttributions();
  }, []);

  return (
    <div className="mb-6" data-tour="attributions">
      {/* Toggle button */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className={cn(
          'flex items-center gap-2 w-full text-left',
          'px-4 py-3 rounded-[10px]',
          'bg-[var(--card-bg)] border border-[var(--card-border)] backdrop-blur-[12px]',
          'text-[var(--text-muted)] text-[0.8125rem] font-medium',
          'cursor-pointer transition-all duration-200',
          'hover:bg-white/[0.06] hover:border-white/[0.14]',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2'
        )}
        aria-expanded={isExpanded}
        aria-controls="info-section-content"
      >
        <Info
          className="w-4 h-4 flex-shrink-0 text-[var(--accent-emerald)]"
          aria-hidden="true"
        />
        <span>Data Disclaimer &amp; Attributions</span>
        <ChevronDown
          className={cn(
            'w-3.5 h-3.5 ml-auto flex-shrink-0 text-[var(--text-dim)]',
            'transition-transform duration-200',
            isExpanded && 'rotate-180'
          )}
          aria-hidden="true"
        />
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div
          id="info-section-content"
          className={cn(
            'mt-2 p-5 rounded-[10px]',
            'bg-[var(--card-bg)] border border-[var(--card-border)] backdrop-blur-[12px]'
          )}
        >
          {/* Disclaimer text */}
          <p className="text-[0.8125rem] text-[var(--text-muted)] leading-relaxed">
            <strong className="text-[var(--text-primary)] font-semibold">
              Data Disclaimer:
            </strong>{' '}
            {DISCLAIMER_TEXT}
          </p>

          {/* Divider */}
          <div className="h-px bg-[var(--card-border)] my-4" />

          {/* Attribution heading */}
          <h4 className="font-heading text-xs font-semibold text-[var(--text-dim)] uppercase tracking-[0.05em] mb-3">
            Data Source Attributions
          </h4>

          {/* Attribution cards */}
          <div className="flex flex-col gap-3">
            {attributionData?.attributions.map((attribution) => {
              const badge = getSourceBadge(attribution.name);
              const licenseSummary = getLicenseSummary(attribution);

              return (
                <div
                  key={attribution.id}
                  className={cn(
                    'flex gap-3 items-start',
                    'p-4 px-5 rounded-[10px]',
                    'bg-[var(--card-bg)] border border-[var(--card-border)] backdrop-blur-[12px]'
                  )}
                >
                  {/* Source badge */}
                  <span
                    className={cn(
                      'inline-flex items-center flex-shrink-0 mt-0.5',
                      'px-2.5 py-1 rounded-[5px]',
                      'text-[0.8125rem] font-bold tracking-[0.04em] whitespace-nowrap',
                      badge.variant === 'epa' &&
                        'bg-[rgba(16,185,129,0.25)] text-[var(--accent-emerald)] border border-[rgba(16,185,129,0.30)]',
                      badge.variant === 'defra' &&
                        'bg-[rgba(59,130,246,0.25)] text-[var(--accent-sapphire)] border border-[rgba(59,130,246,0.30)]',
                      badge.variant === 'default' &&
                        'bg-white/10 text-[var(--text-muted)] border border-white/15'
                    )}
                  >
                    {badge.label}
                  </span>

                  {/* Attribution text */}
                  <div>
                    <div className="text-[0.8125rem] text-[var(--text-muted)] leading-relaxed">
                      <strong className="text-[var(--text-primary)] font-semibold">
                        {attribution.name}
                      </strong>
                      <br />
                      {attribution.attribution_text || ''}
                    </div>

                    {/* License pill */}
                    {licenseSummary && (
                      <div
                        className={cn(
                          'inline-flex items-center gap-1.5 mt-1.5',
                          'px-2 py-0.5 rounded',
                          'bg-white/[0.04] border border-white/[0.06]',
                          'text-xs text-[var(--text-dim)] font-medium'
                        )}
                      >
                        {licenseSummary}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Fallback if no data yet */}
            {!attributionData && (
              <p className="text-xs text-[var(--text-dim)]">
                Loading attribution data...
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InfoSection;
