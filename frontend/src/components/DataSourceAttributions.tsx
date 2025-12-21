/**
 * Data Source Attributions Component
 *
 * Displays license and attribution information for emission factor data sources.
 * Required for compliance with:
 * - EPA: Public Domain (recommended attribution)
 * - DEFRA: Open Government Licence v3.0 (required attribution)
 * - Exiobase: CC-BY-SA-4.0 (required attribution with share-alike)
 */

import { useState, useEffect } from 'react';
import { ExternalLink, Info, ChevronDown, ChevronUp, Scale } from 'lucide-react';
import { emissionFactorsAPI } from '@/services/api/emissionFactors';
import type { DataSourceAttribution, AttributionResponse } from '@/types/api.types';
import { cn } from '@/lib/utils';

interface DataSourceAttributionsProps {
  /** Show in compact footer mode (default) or expanded mode */
  variant?: 'footer' | 'expanded';
  /** Additional CSS classes */
  className?: string;
}

/**
 * License badge colors based on license type
 */
const getLicenseBadgeStyle = (licenseType: string | null): string => {
  if (!licenseType) return 'bg-gray-100 text-gray-700';

  const lower = licenseType.toLowerCase();
  if (lower.includes('public domain')) {
    return 'bg-green-100 text-green-800';
  }
  if (lower.includes('cc-by-sa') || lower.includes('share')) {
    return 'bg-amber-100 text-amber-800';
  }
  if (lower.includes('ogl') || lower.includes('open government')) {
    return 'bg-blue-100 text-blue-800';
  }
  return 'bg-gray-100 text-gray-700';
};

/**
 * Single attribution item display
 */
function AttributionItem({ attribution }: { attribution: DataSourceAttribution }) {
  return (
    <div className="border-l-2 border-muted pl-3 py-2">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-medium text-sm">{attribution.name}</span>
        {attribution.license_type && (
          <span className={cn(
            'text-xs px-2 py-0.5 rounded-full font-medium',
            getLicenseBadgeStyle(attribution.license_type)
          )}>
            {attribution.license_type}
          </span>
        )}
        {attribution.requires_attribution && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">
            Attribution Required
          </span>
        )}
        {attribution.requires_share_alike && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
            Share-Alike
          </span>
        )}
      </div>

      {attribution.attribution_text && (
        <p className="text-xs text-muted-foreground mt-1">
          {attribution.attribution_text}
        </p>
      )}

      <div className="flex gap-3 mt-1">
        {attribution.attribution_url && (
          <a
            href={attribution.attribution_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary hover:underline inline-flex items-center gap-1"
          >
            Source <ExternalLink className="h-3 w-3" />
          </a>
        )}
        {attribution.license_url && (
          <a
            href={attribution.license_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary hover:underline inline-flex items-center gap-1"
          >
            License <Scale className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  );
}

/**
 * Data Source Attributions Component
 *
 * Displays attribution information for all active emission factor data sources.
 * Can be displayed as a compact footer or expanded panel.
 */
export function DataSourceAttributions({
  variant = 'footer',
  className
}: DataSourceAttributionsProps) {
  const [attributionData, setAttributionData] = useState<AttributionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(variant === 'expanded');

  useEffect(() => {
    const fetchAttributions = async () => {
      try {
        setLoading(true);
        const data = await emissionFactorsAPI.getAttributions();
        setAttributionData(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch attributions:', err);
        setError('Unable to load data source attributions');
      } finally {
        setLoading(false);
      }
    };

    fetchAttributions();
  }, []);

  // Filter to only sources that require attribution
  const requiredAttributions = attributionData?.attributions.filter(
    a => a.requires_attribution
  ) || [];

  if (loading) {
    return (
      <div className={cn('text-xs text-muted-foreground', className)}>
        Loading data source information...
      </div>
    );
  }

  if (error || !attributionData) {
    return null; // Silently fail - attributions are informational
  }

  // Compact footer variant
  if (variant === 'footer' && !isExpanded) {
    return (
      <div
        className={cn(
          'border-t bg-muted/30 px-4 py-2',
          className
        )}
        data-tour="attributions"
      >
        <button
          onClick={() => setIsExpanded(true)}
          className="w-full flex items-center justify-between text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <span className="flex items-center gap-2">
            <Info className="h-3 w-3" />
            Data sources: EPA, DEFRA, Exiobase
            {requiredAttributions.length > 0 && (
              <span className="text-amber-700">
                ({requiredAttributions.length} require attribution)
              </span>
            )}
          </span>
          <ChevronDown className="h-4 w-4" />
        </button>
      </div>
    );
  }

  // Expanded variant
  return (
    <div
      className={cn(
        'border-t bg-muted/30 px-4 py-3',
        className
      )}
      data-tour="attributions"
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <Scale className="h-4 w-4" />
          Data Source Attributions
        </h4>
        {variant === 'footer' && (
          <button
            onClick={() => setIsExpanded(false)}
            className="text-muted-foreground hover:text-foreground"
          >
            <ChevronUp className="h-4 w-4" />
          </button>
        )}
      </div>

      <p className="text-xs text-muted-foreground mb-3">
        {attributionData.notice}
      </p>

      <div className="space-y-3">
        {attributionData.attributions.map((attribution) => (
          <AttributionItem key={attribution.id} attribution={attribution} />
        ))}
      </div>
    </div>
  );
}

/**
 * Compact inline attribution notice for calculation results
 */
export function AttributionNotice({ className }: { className?: string }) {
  return (
    <p className={cn('text-xs text-muted-foreground', className)}>
      Emission factors sourced from EPA (Public Domain), DEFRA (OGL v3.0), and Exiobase (CC-BY-SA-4.0).{' '}
      <a href="#attributions" className="text-primary hover:underline">
        View full attributions
      </a>
    </p>
  );
}

export default DataSourceAttributions;
