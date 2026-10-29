/**
 * DataSourceAttribution Component
 *
 * Displays attribution information for data sources used in calculations.
 * Shows source name, license type, and required attribution text.
 *
 * CRITICAL: DEFRA (OGL v3.0) requires attribution.
 * This is a legal compliance requirement.
 *
 * @see knowledge/db_compliance/External_Data_Source_Compliance_Guide.md
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

/**
 * Data source information from API response
 */
export interface DataSource {
  code: string;
  name: string;
  license_type: string;
  factors_used: number;
  attribution_required: boolean;
  attribution_text: string;
  license_url?: string;
}

interface DataSourceAttributionProps {
  /** Array of data sources used in the calculation */
  dataSources: DataSource[];
  /** Optional className for styling */
  className?: string;
}

/**
 * Source code to display name and anchor mapping
 * Maps source codes to their display configuration
 */
export const SOURCE_CONFIG: Record<
  string,
  {
    anchor: string;
    shortName: string;
    color: string;
  }
> = {
  EPA: {
    anchor: 'epa-attribution',
    shortName: 'EPA',
    color: 'text-green-700',
  },
  DEFRA: {
    anchor: 'defra-attribution',
    shortName: 'DEF',
    color: 'text-blue-700',
  },
  PROXY: {
    anchor: 'proxy-attribution',
    shortName: 'PRX',
    color: 'text-gray-600',
  },
};

/**
 * DataSourceAttribution Component
 *
 * Displays attribution information for all data sources used in calculations.
 * Required attributions are emphasized and linked.
 */
export const DataSourceAttribution: React.FC<DataSourceAttributionProps> = ({
  dataSources,
  className,
}) => {
  if (!dataSources || dataSources.length === 0) {
    return (
      <Card className={cn('mt-4', className)}>
        <CardHeader>
          <CardTitle className="text-lg">Data Source Attributions</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No data sources available.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('mt-4 bg-muted/30', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg" role="heading" aria-level={2}>
          Data Source Attributions
        </CardTitle>
      </CardHeader>
      <Separator className="mb-4" />
      <CardContent className="space-y-4">
        {dataSources.map((source) => {
          const config = SOURCE_CONFIG[source.code];
          const anchorId = config?.anchor || source.code.toLowerCase();

          return (
            <div key={source.code} id={anchorId} className="space-y-1">
              <h3
                className={cn(
                  'font-semibold text-sm',
                  config?.color || 'text-foreground'
                )}
              >
                {source.name}
              </h3>
              <p className="text-xs text-muted-foreground">
                License: {source.license_type.replace(/_/g, ' ')}
                {source.factors_used > 0 && ` | Factors used: ${source.factors_used}`}
              </p>
              {source.attribution_required && source.attribution_text && (
                <p className="text-xs italic pl-2 border-l-2 border-muted-foreground/30">
                  {source.attribution_text}
                </p>
              )}
              {source.license_url && (
                <a
                  href={source.license_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline ml-2"
                >
                  View License
                </a>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
};

export default DataSourceAttribution;
