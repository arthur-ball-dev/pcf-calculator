/**
 * Export Attribution Utility
 *
 * Generates attribution text for exports (PDF, CSV, Excel).
 * Ensures legal compliance by including required attributions
 * and disclaimer in exported documents.
 *
 * @see knowledge/db_compliance/External_Data_Source_Compliance_Guide.md
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

/**
 * Data source information for attribution generation
 */
export interface DataSourceInfo {
  code: string;
  name: string;
  attribution_required: boolean;
  attribution_text: string;
}

/**
 * Generate attribution text for exports
 *
 * Creates a formatted text block with:
 * - Header section
 * - Required attributions from data sources
 * - Disclaimer section
 *
 * @param sources - Array of data source information
 * @returns Formatted attribution text string
 */
export const generateAttributionText = (sources: DataSourceInfo[]): string => {
  const separator = '='.repeat(60);
  const lines: string[] = [];

  // Header section
  lines.push(separator);
  lines.push('DATA SOURCE ATTRIBUTIONS');
  lines.push(separator);
  lines.push('');

  // Attribution content - only for required sources
  for (const source of sources) {
    if (source.attribution_required && source.attribution_text) {
      lines.push(source.name);
      lines.push(source.attribution_text);
      lines.push('');
    }
  }

  // Disclaimer section
  lines.push(separator);
  lines.push('DISCLAIMER');
  lines.push(separator);
  lines.push('');
  lines.push('Calculations are for informational purposes only.');
  lines.push('No warranty is provided regarding accuracy.');
  lines.push('Consult qualified professionals for regulatory compliance.');
  lines.push('');

  return lines.join('\n');
};

/**
 * Append attribution text to CSV content
 *
 * Adds attribution information to the end of CSV exports.
 * Maintains proper separation between data and attribution.
 *
 * @param csvContent - Original CSV content
 * @param sources - Array of data source information
 * @returns CSV content with attribution appended
 */
export const appendAttributionToCSV = (
  csvContent: string,
  sources: DataSourceInfo[]
): string => {
  const attribution = generateAttributionText(sources);
  return csvContent + '\n\n' + attribution;
};

export default {
  generateAttributionText,
  appendAttributionToCSV,
};
