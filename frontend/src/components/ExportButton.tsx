/**
 * ExportButton Component
 * TASK-FE-P5-005: Export buttons for CSV and Excel download
 *
 * Features:
 * - Direct CSV and Excel download buttons
 * - Loading state with spinner
 * - Disabled state handling
 * - Error display
 * - Accessibility support
 */

import { Download, FileSpreadsheet, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useExport } from '@/hooks/useExport';
import type { CalculationStatusResponse } from '@/types/api.types';

// Extended results type
interface ExtendedResults extends CalculationStatusResponse {
  category_breakdown?: Array<{
    scope: string;
    category: string;
    emissions: number;
    percentage: number;
  }>;
  bom_details?: Array<{
    component_name: string;
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

interface ExportButtonProps {
  results: ExtendedResults | null;
  productName: string;
  productCode: string;
  disabled?: boolean;
  className?: string;
}

export function ExportButton({
  results,
  productName,
  productCode,
  disabled,
  className,
}: ExportButtonProps) {
  const { exportToCSV, exportToExcel, isExporting, error, clearError } =
    useExport(results, { name: productName, code: productCode });

  const handleCSVExport = async () => {
    try {
      await exportToCSV();
    } catch {
      // Error is handled by the hook
    }
  };

  const handleExcelExport = async () => {
    try {
      await exportToExcel();
    } catch {
      // Error is handled by the hook
    }
  };

  // Determine if buttons should be disabled
  const isDisabled = disabled || isExporting || !results;

  return (
    <div
      className={`flex flex-col items-start gap-2 ${className || ''}`}
      data-testid="export-buttons"
    >
      <div className="flex items-center gap-2">
        {/* CSV Download Button */}
        <Button
          variant="outline"
          onClick={handleCSVExport}
          disabled={isDisabled}
          data-testid="export-csv-button"
          aria-label="Download as CSV"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          CSV
        </Button>

        {/* Excel Download Button */}
        <Button
          variant="outline"
          onClick={handleExcelExport}
          disabled={isDisabled}
          data-testid="export-excel-button"
          aria-label="Download as Excel"
        >
          {isExporting ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Download className="h-4 w-4 mr-2" />
          )}
          Excel
        </Button>
      </div>

      {/* Error display */}
      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md"
        >
          <span>{error}</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearError}
            className="h-auto p-1"
            aria-label="Dismiss error"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );
}
