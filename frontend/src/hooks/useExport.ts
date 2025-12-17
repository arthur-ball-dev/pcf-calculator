/**
 * useExport Hook
 * TASK-FE-P5-005: Hook for managing export functionality
 *
 * Features:
 * - CSV and Excel export methods
 * - Loading state management
 * - Error handling
 * - Data transformation from API response to export format
 * - Concurrent export prevention
 */

import { useState, useCallback, useRef } from 'react';
import { exportToCSV, type CSVOptions } from '@/utils/export/csvExport';
import { exportToExcel, type CalculationExportData } from '@/utils/export/excelExport';
import { classifyComponent, formatCategoryLabel } from '@/utils/classifyComponent';
import type { CalculationStatusResponse } from '@/types/api.types';

// Extended results type with optional breakdown fields
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
  }>;
  parameters?: {
    transport_distance?: number;
    energy_source?: string;
    production_volume?: number;
  };
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

        // Check if any custom options were provided
        const hasCustomOptions =
          options.delimiter !== undefined ||
          options.includeHeaders !== undefined ||
          options.includeBOM !== undefined ||
          options.dateFormat !== undefined ||
          options.numberFormat !== undefined;

        const hasHeaders = options.headers !== undefined;

        // Call exportToCSV with appropriate arguments based on what was provided
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

          await exportToCSV(csvData, filename, options.headers, csvOptions);
        } else {
          // Simple call with just data and filename
          await exportToCSV(csvData, filename);
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
