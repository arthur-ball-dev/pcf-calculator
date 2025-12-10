/**
 * ExportButton Component
 * TASK-FE-P5-005: Export button with dropdown and direct buttons
 *
 * Features:
 * - Dropdown menu with CSV and Excel options
 * - Direct buttons for quick access on desktop
 * - Loading state with spinner
 * - Disabled state handling
 * - Error display
 * - Accessibility support
 */

import React from 'react';
import { FileDown, FileSpreadsheet, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
        {/* Dropdown Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="outline"
              disabled={isDisabled}
              data-testid="export-dropdown"
              aria-busy={isExporting}
              aria-label="Export options"
            >
              {isExporting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <FileDown className="h-4 w-4 mr-2" />
              )}
              {isExporting ? 'Exporting...' : 'Export'}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem
              onClick={handleCSVExport}
              data-testid="export-csv-option"
            >
              <FileDown className="h-4 w-4 mr-2" />
              Export as CSV
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={handleExcelExport}
              data-testid="export-excel-option"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Export as Excel
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Direct buttons for desktop */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCSVExport}
          disabled={isDisabled}
          data-testid="export-csv-button"
          className="hidden md:flex"
          aria-label="Export as CSV"
        >
          <FileDown className="h-4 w-4 mr-1" />
          CSV
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={handleExcelExport}
          disabled={isDisabled}
          data-testid="export-excel-button"
          className="hidden md:flex"
          aria-label="Export as Excel"
        >
          <FileSpreadsheet className="h-4 w-4 mr-1" />
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
