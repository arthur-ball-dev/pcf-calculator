/**
 * Excel Export Utility
 * TASK-FE-P5-005: Excel/XLSX generation and export functionality
 *
 * Features:
 * - Multi-sheet workbook creation (Summary, Breakdown, BOM)
 * - Column width configuration
 * - Cell formatting for numbers and percentages
 * - Download triggering with proper MIME type
 */

import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

export interface CalculationExportData {
  productName: string;
  productCode: string;
  calculationDate: Date | null;
  totalEmissions: number;
  unit: string;
  categoryBreakdown: Array<{
    scope: string;
    category: string;
    emissions: number;
    percentage: number;
  }>;
  bomEntries: Array<{
    component: string;
    quantity: number;
    unit: string;
    emissionFactor: number;
    emissions: number;
  }>;
  parameters: {
    transportDistance?: number;
    energySource?: string;
    productionVolume?: number;
  };
}

export interface SheetConfig {
  sheetName?: string;
}

type WorkBook = XLSX.WorkBook;
type WorkSheet = XLSX.WorkSheet;

/**
 * Create a new workbook
 */
export function createWorkbook(): WorkBook {
  return XLSX.utils.book_new();
}

/**
 * Add Summary sheet to workbook
 */
export function addSummarySheet(
  workbook: WorkBook,
  data: CalculationExportData,
  config: SheetConfig = {}
): void {
  const sheetName = config.sheetName || 'Summary';

  // Format date safely
  const dateStr = data.calculationDate
    ? data.calculationDate.toLocaleDateString()
    : 'N/A';

  const summaryData = [
    ['Product Carbon Footprint Calculation Report'],
    [''],
    ['Product Information'],
    ['Name', data.productName],
    ['Code', data.productCode],
    ['Calculation Date', dateStr],
    [''],
    ['Results'],
    ['Total Emissions', data.totalEmissions.toFixed(2), data.unit],
    [''],
    ['Calculation Parameters'],
    ['Transport Distance', data.parameters?.transportDistance || 'N/A', 'km'],
    ['Energy Source', data.parameters?.energySource || 'N/A'],
    ['Production Volume', data.parameters?.productionVolume || 1, 'units'],
  ];

  const sheet = XLSX.utils.aoa_to_sheet(summaryData);

  // Set column widths
  sheet['!cols'] = [{ wch: 25 }, { wch: 30 }, { wch: 15 }];

  // Merge cells for title
  sheet['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: 2 } }];

  XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
}

/**
 * Add Breakdown sheet to workbook
 */
export function addBreakdownSheet(
  workbook: WorkBook,
  categoryBreakdown: CalculationExportData['categoryBreakdown'],
  config: SheetConfig = {}
): void {
  const sheetName = config.sheetName || 'Breakdown';

  const headers = ['Scope', 'Category', 'Emissions (kg CO2e)', 'Percentage'];
  const dataRows = categoryBreakdown.map((item) => [
    item.scope,
    item.category,
    item.emissions,
    item.percentage / 100, // Excel percentage format expects decimal
  ]);

  const sheetData = [headers, ...dataRows];
  const sheet = XLSX.utils.aoa_to_sheet(sheetData);

  // Set column widths
  sheet['!cols'] = [{ wch: 15 }, { wch: 30 }, { wch: 20 }, { wch: 12 }];

  // Apply number formats
  const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1');
  for (let row = 1; row <= range.e.r; row++) {
    // Emissions column (C)
    const emissionsCell = XLSX.utils.encode_cell({ r: row, c: 2 });
    if (sheet[emissionsCell]) {
      sheet[emissionsCell].z = '#,##0.00';
    }

    // Percentage column (D)
    const percentCell = XLSX.utils.encode_cell({ r: row, c: 3 });
    if (sheet[percentCell]) {
      sheet[percentCell].z = '0.0%';
    }
  }

  XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
}

/**
 * Add BOM sheet to workbook
 */
export function addBOMSheet(
  workbook: WorkBook,
  bomEntries: CalculationExportData['bomEntries'],
  config: SheetConfig = {}
): void {
  const sheetName = config.sheetName || 'Bill of Materials';

  const headers = [
    'Component',
    'Quantity',
    'Unit',
    'Emission Factor',
    'Emissions (kg CO2e)',
  ];

  const dataRows = bomEntries.map((entry) => [
    entry.component,
    entry.quantity,
    entry.unit,
    entry.emissionFactor,
    entry.emissions,
  ]);

  // Calculate total emissions
  const totalEmissions = bomEntries.reduce((sum, e) => sum + e.emissions, 0);

  // Add totals row
  dataRows.push(['', '', '', 'TOTAL', totalEmissions]);

  const sheetData = [headers, ...dataRows];
  const sheet = XLSX.utils.aoa_to_sheet(sheetData);

  // Set column widths
  sheet['!cols'] = [
    { wch: 30 },
    { wch: 12 },
    { wch: 10 },
    { wch: 18 },
    { wch: 20 },
  ];

  XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
}

/**
 * Export data to Excel file
 */
export function exportToExcel(
  data: CalculationExportData,
  filename: string
): void {
  const workbook = createWorkbook();

  // Add all sheets
  addSummarySheet(workbook, data);
  addBreakdownSheet(workbook, data.categoryBreakdown);
  addBOMSheet(workbook, data.bomEntries);

  // Write workbook to array buffer
  const excelBuffer = XLSX.write(workbook, {
    bookType: 'xlsx',
    type: 'array',
  });

  // Create blob and trigger download
  const blob = new Blob([excelBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });

  saveAs(blob, `${filename}.xlsx`);
}
