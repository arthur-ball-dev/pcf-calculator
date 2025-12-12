/**
 * ExportDialog Component
 * TASK-FE-P5-005: Dialog for export options
 *
 * Features:
 * - Format selection (CSV, Excel)
 * - Export options (include headers, date format, delimiter)
 * - Loading state during export
 * - Error display
 * - File preview
 * - Accessibility support
 */

import { useState, useEffect, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { exportToCSV, type CSVOptions } from '@/utils/export/csvExport';
import { exportToExcel, type CalculationExportData } from '@/utils/export/excelExport';
import type { CalculationStatusResponse } from '@/types/api.types';

type ExportFormat = 'csv' | 'excel';
type DateFormatOption = 'iso' | 'locale';

interface ExportOptions {
  format: ExportFormat;
  includeHeaders: boolean;
  dateFormat: DateFormatOption;
  delimiter: string;
}

interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  results: CalculationStatusResponse;
  productName: string;
  productCode: string;
  onExport?: (options: ExportOptions) => void;
}

/**
 * Generate a sanitized filename from product name
 */
function generateFilename(productName: string): string {
  const sanitized = productName.replace(/[^a-zA-Z0-9]/g, '_');
  const timestamp = new Date().toISOString().split('T')[0];
  return `${sanitized}_PCF_${timestamp}`;
}

export function ExportDialog({
  open,
  onClose,
  results,
  productName,
  productCode,
  onExport,
}: ExportDialogProps) {
  // Form state
  const [format, setFormat] = useState<ExportFormat>('csv');
  const [includeHeaders, setIncludeHeaders] = useState(true);
  const [dateFormat, setDateFormat] = useState<DateFormatOption>('iso');
  const [delimiter, setDelimiter] = useState(',');

  // UI state
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setFormat('csv');
      setIncludeHeaders(true);
      setDateFormat('iso');
      setDelimiter(',');
      setError(null);
    }
  }, [open]);

  // Generate filename preview
  const filename = generateFilename(productName);
  const fileExtension = format === 'csv' ? '.csv' : '.xlsx';

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    setError(null);

    try {
      const options: ExportOptions = {
        format,
        includeHeaders,
        dateFormat,
        delimiter,
      };

      // Call custom onExport if provided
      if (onExport) {
        onExport(options);
      }

      if (format === 'csv') {
        // Prepare CSV data from results
        const csvData = [
          {
            Scope: 'Scope 1',
            Category: 'Materials',
            'Emissions (kg CO2e)': results.materials_co2e || 0,
            Percentage: '60%',
          },
          {
            Scope: 'Scope 2',
            Category: 'Energy',
            'Emissions (kg CO2e)': results.energy_co2e || 0,
            Percentage: '30%',
          },
          {
            Scope: 'Scope 3',
            Category: 'Transport',
            'Emissions (kg CO2e)': results.transport_co2e || 0,
            Percentage: '10%',
          },
        ];

        const csvOptions: CSVOptions = {
          delimiter,
          includeHeaders,
          dateFormat:
            dateFormat === 'locale'
              ? (date) => date.toLocaleDateString('en-US')
              : undefined,
        };

        await exportToCSV(csvData, filename, undefined, csvOptions);
      } else {
        // Prepare Excel data
        const exportData: CalculationExportData = {
          productName,
          productCode,
          calculationDate: new Date(),
          totalEmissions: results.total_co2e_kg || 0,
          unit: 'kg CO2e',
          categoryBreakdown: [
            {
              scope: 'Scope 1',
              category: 'Materials',
              emissions: results.materials_co2e || 0,
              percentage: 60,
            },
            {
              scope: 'Scope 2',
              category: 'Energy',
              emissions: results.energy_co2e || 0,
              percentage: 30,
            },
            {
              scope: 'Scope 3',
              category: 'Transport',
              emissions: results.transport_co2e || 0,
              percentage: 10,
            },
          ],
          bomEntries: [],
          parameters: {},
        };

        await exportToExcel(exportData, filename);
      }

      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
    } finally {
      setIsExporting(false);
    }
  }, [
    format,
    includeHeaders,
    dateFormat,
    delimiter,
    results,
    productName,
    productCode,
    filename,
    onClose,
    onExport,
  ]);

  const handleCancel = () => {
    if (!isExporting) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && handleCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Export Results</DialogTitle>
          <DialogDescription>
            Download results for {productName} ({productCode})
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4">
          {/* Format Selection */}
          <div className="grid gap-3">
            <Label htmlFor="format-group">Format</Label>
            <RadioGroup
              id="format-group"
              value={format}
              onValueChange={(value) => setFormat(value as ExportFormat)}
              disabled={isExporting}
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="csv" id="csv" aria-label="CSV" />
                <Label htmlFor="csv" className="font-normal cursor-pointer">
                  CSV - Comma-separated values
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="excel" id="excel" aria-label="Excel" />
                <Label htmlFor="excel" className="font-normal cursor-pointer">
                  Excel - Multi-sheet workbook (.xlsx)
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* Export Options */}
          <div className="grid gap-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="includeHeaders"
                checked={includeHeaders}
                onCheckedChange={(checked) =>
                  setIncludeHeaders(checked === true)
                }
                disabled={isExporting}
                aria-label="Include headers"
              />
              <Label htmlFor="includeHeaders" className="cursor-pointer">
                Include headers
              </Label>
            </div>
          </div>

          {/* Date Format */}
          <div className="grid gap-2">
            <Label htmlFor="dateFormat">Date format</Label>
            <select
              id="dateFormat"
              value={dateFormat}
              onChange={(e) =>
                setDateFormat(e.target.value as DateFormatOption)
              }
              disabled={isExporting}
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
              aria-label="Date format"
            >
              <option value="iso">ISO (2024-06-15)</option>
              <option value="locale">Locale (6/15/2024)</option>
            </select>
          </div>

          {/* Delimiter (CSV only) */}
          {format === 'csv' && (
            <div className="grid gap-2">
              <Label htmlFor="delimiter">Delimiter</Label>
              <select
                id="delimiter"
                value={delimiter}
                onChange={(e) => setDelimiter(e.target.value)}
                disabled={isExporting}
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
                aria-label="Delimiter"
              >
                <option value=",">Comma (,)</option>
                <option value=";">Semicolon (;)</option>
                <option value={'\t'}>Tab</option>
              </select>
            </div>
          )}

          {/* File Preview */}
          <div className="text-sm text-muted-foreground">
            <span>File: </span>
            <span className="font-mono">
              {filename}
              {fileExtension}
            </span>
          </div>

          {/* Error Display */}
          {error && (
            <div role="alert" className="text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Loading indicator for screen readers */}
          {isExporting && (
            <div aria-live="polite" className="text-sm text-muted-foreground">
              Exporting...
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isExporting}
          >
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            Export
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
