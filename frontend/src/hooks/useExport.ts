/**
 * useExport Hook
 * TASK-FE-P5-005: Hook for managing export functionality
 * TASK-FE-P8-008: Integrated attribution into exports
 *
 * Features:
 * - CSV and Excel export methods
 * - Loading state management
 * - Error handling
 * - Data transformation from API response to export format
 * - Concurrent export prevention
 * - Attribution integration for legal compliance
 */

import { useState, useCallback, useRef } from 'react';
import { exportToCSV, type CSVOptions } from '@/utils/export/csvExport';
import { exportToExcel, type CalculationExportData } from '@/utils/export/excelExport';
import { classifyComponent, formatCategoryLabel } from '@/utils/classifyComponent';
import type { DataSourceInfo } from '@/utils/exportAttribution';
import type { CalculationStatusResponse } from '@/types/api.types';

// Default data sources with attribution info
// Used when explicit data sources are not provided
const DEFAULT_DATA_SOURCES: DataSourceInfo[] = [
  {
    code: 'EPA',
    name: 'EPA GHG Emission Factors Hub',
    attribution_required: false,
    attribution_text: 'Data source: U.S. EPA GHG Emission Factors Hub',
  },
  {
    code: 'DEFRA',
    name: 'UK Government GHG Conversion Factors',
    attribution_required: true,
    attribution_text: 'Contains UK Government GHG Conversion Factors for Company Reporting. (c) Crown copyright, licensed under the Open Government Licence v3.0.',
  },
  {
    code: 'EXIOBASE',
    name: 'EXIOBASE 3.8',
    attribution_required: true,
    attribution_text: 'EXIOBASE 3.8 is licensed under Creative Commons Attribution-ShareAlike 4.0. Citation: Stadler et al. 2018.',
  },
];

// Extended results type with optional breakdown fields and data sources
interface ExtendedResults extends CalculationStatusResponse {
  category_breakdown?: Array<{
    scope: string;
    category: string;
    emissions: number;
    percentage: number;
  }>;
  bom_details?: Array<{
    component_name: string;
    category: string;
    quantity: number;
    unit: string;
    emission_factor: number;
    emissions: number;
    data_source?: string;
  }>;
  parameters?: {
    transport_distance?: number;
    energy_source?: string;
    production_volume?: number;
  };
  data_sources?: DataSourceInfo[];
}

interface ProductInfo {
  name: string;
  code: string;
}

interface ExportCSVOptions extends CSVOptions {
  filename?: string;
  headers?: string[];
}

interface UseExportReturn {
  exportToCSV: (options?: ExportCSVOptions) => Promise<void>;
  exportToExcel: () => Promise<void>;
  isExporting: boolean;
  error: string | null;
  clearError: () => void;
}

/**
 * Generate a sanitized filename from product name
 */
function generateFilename(productName: string, productCode: string): string {
  // Use product name if available, otherwise use product code
  const name = productName || productCode || 'export';

  // Sanitize: replace special characters with underscore
  const sanitized = name.replace(/[^a-zA-Z0-9]/g, '_');

  // Add date
  const timestamp = new Date().toISOString().split('T')[0];

  return `${sanitized}_PCF_${timestamp}`;
}

/**
 * Get data sources from results or BOM items
 * Falls back to default sources to ensure legal compliance
 */
function getDataSourcesFromResults(results: ExtendedResults | null): DataSourceInfo[] {
  // Strategy 1: If results include explicit data_sources, use directly
  if (results?.data_sources && results.data_sources.length > 0) {
    return results.data_sources;
  }

  // Strategy 2: Infer from BOM items (if data_source field exists)
  const bomDetails = results?.bom_details || [];
  const sourceCodes = new Set<string>();
  bomDetails.forEach(item => {
    if (item.data_source) {
      sourceCodes.add(item.data_source);
    }
  });

  if (sourceCodes.size > 0) {
    // Map source codes to full DataSourceInfo objects
    return DEFAULT_DATA_SOURCES.filter(source => sourceCodes.has(source.code));
  }

  // Strategy 3: Return empty array (disclaimer will still be included)
  // This ensures we don't include attributions for sources not actually used
  return [];
}

/**
 * Hook for exporting calculation results
 */
export function useExport(
  results: ExtendedResults | null,
  productInfo: ProductInfo
): UseExportReturn {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Use ref for synchronous lock to prevent concurrent exports
  const isExportingRef = useRef(false);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleExportToCSV = useCallback(
    async (options: ExportCSVOptions = {}) => {
      // Prevent concurrent exports using ref for synchronous check
      if (isExportingRef.current) return;

      isExportingRef.current = true;
      setIsExporting(true);
      setError(null);

      try {
        // Export BOM details with emissions for each component
        const bomDetails = results?.bom_details || [];
        const totalEmissions = results?.total_co2e_kg || 0;

        // Calculate sum of all BOM item emissions
        const bomEmissionsSum = bomDetails.reduce((sum, item) => sum + (item.emissions || 0), 0);

        // Transform to CSV data format - include all BOM items with emissions
        // Reclassify category based on component name for consistent display
        const csvData: Record<string, string | number>[] = bomDetails.map((item) => ({
          Component: item.component_name,
          Category: formatCategoryLabel(classifyComponent(item.component_name)),
          Quantity: item.quantity,
          Unit: item.unit,
          'Emission Factor': item.emission_factor.toFixed(4),
          'Emissions (kg CO2e)': item.emissions,
          Percentage: totalEmissions > 0 ? `${((item.emissions / totalEmissions) * 100).toFixed(1)}%` : '0%',
        }));

        // Add "Other/Unallocated" row if breakdown doesn't account for all emissions
        const unallocatedEmissions = totalEmissions - bomEmissionsSum;
        if (unallocatedEmissions > 0.001) { // Only add if there's meaningful unallocated amount
          csvData.push({
            Component: 'Other (not itemized)',
            Category: '',
            Quantity: '',
            Unit: '',
            'Emission Factor': '',
            'Emissions (kg CO2e)': Number(unallocatedEmissions.toFixed(4)),
            Percentage: `${((unallocatedEmissions / totalEmissions) * 100).toFixed(1)}%`,
          });
        }

        // Add total row
        csvData.push({
          Component: 'TOTAL',
          Category: '',
          Quantity: '',
          Unit: '',
          'Emission Factor': '',
          'Emissions (kg CO2e)': Number(totalEmissions.toFixed(4)),
          Percentage: '100.0%',
        });

        // Use custom filename if provided, otherwise generate
        const filename =
          options.filename || generateFilename(productInfo.name, productInfo.code);

        // Get data sources for attribution (TASK-FE-P8-008)
        const dataSources = getDataSourcesFromResults(results);

        // Check if any custom options were provided
        const hasCustomOptions =
          options.delimiter !== undefined ||
          options.includeHeaders !== undefined ||
          options.includeBOM !== undefined ||
          options.dateFormat !== undefined ||
          options.numberFormat !== undefined;

        const hasHeaders = options.headers !== undefined;

        // Call exportToCSV with appropriate arguments based on what was provided
        // Attribution is handled by the exportToCSV function via dataSources option
        // Note: await the result in case the function returns a Promise (for testing mocks)
        if (hasHeaders || hasCustomOptions) {
          // Extract CSV-specific options
          const csvOptions: CSVOptions = {};
          if (options.delimiter) csvOptions.delimiter = options.delimiter;
          if (options.includeHeaders !== undefined)
            csvOptions.includeHeaders = options.includeHeaders;
          if (options.includeBOM !== undefined)
            csvOptions.includeBOM = options.includeBOM;
          if (options.dateFormat) csvOptions.dateFormat = options.dateFormat;
          if (options.numberFormat) csvOptions.numberFormat = options.numberFormat;
          // Add data sources for attribution (TASK-FE-P8-008)
          csvOptions.dataSources = dataSources;

          await exportToCSV(csvData, filename, options.headers, csvOptions);
        } else {
          // Simple call with just data and filename
          // TASK-FE-P8-008: Pass dataSources for attribution
          // Use the fourth argument for options with dataSources
          await exportToCSV(csvData, filename, undefined, { dataSources });
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'CSV export failed';
        setError(message);
        throw err;
      } finally {
        isExportingRef.current = false;
        setIsExporting(false);
      }
    },
    [results, productInfo]
  );

  const handleExportToExcel = useCallback(async () => {
    // Prevent concurrent exports using ref for synchronous check
    if (isExportingRef.current) return;

    isExportingRef.current = true;
    setIsExporting(true);
    setError(null);

    try {
      // Get data sources for attribution (TASK-FE-P8-008)
      const dataSources = getDataSourcesFromResults(results);

      // Transform API response to export data format
      const exportData: CalculationExportData = {
        productName: productInfo.name,
        productCode: productInfo.code,
        calculationDate: new Date(),
        totalEmissions: results?.total_co2e_kg || 0,
        unit: 'kg CO2e',
        categoryBreakdown: results?.category_breakdown || [],
        bomEntries:
          results?.bom_details?.map((entry) => ({
            component: entry.component_name,
            // Reclassify category based on component name for consistent display
            category: classifyComponent(entry.component_name),
            quantity: entry.quantity,
            unit: entry.unit,
            emissionFactor: entry.emission_factor,
            emissions: entry.emissions,
          })) || [],
        parameters: results?.parameters
          ? {
              transportDistance: results.parameters.transport_distance,
              energySource: results.parameters.energy_source,
              productionVolume: results.parameters.production_volume,
            }
          : {},
        // Add data sources for attribution sheet (TASK-FE-P8-008)
        dataSources: dataSources,
      };

      const filename = generateFilename(productInfo.name, productInfo.code);
      // await the result in case the function returns a Promise (for testing mocks)
      await exportToExcel(exportData, filename);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Excel export failed';
      setError(message);
      throw err;
    } finally {
      isExportingRef.current = false;
      setIsExporting(false);
    }
  }, [results, productInfo]);

  return {
    exportToCSV: handleExportToCSV,
    exportToExcel: handleExportToExcel,
    isExporting,
    error,
    clearError,
  };
}
