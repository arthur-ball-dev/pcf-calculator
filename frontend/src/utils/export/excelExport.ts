/**
 * Excel Export Utility
 * TASK-FE-P5-005: Excel/XLSX generation and export functionality
 * TASK-FE-P7-024: Dynamic import for bundle optimization
 *
 * Features:
 * - Multi-sheet workbook creation (Summary, Breakdown, BOM)
 * - Column width configuration
 * - Cell formatting for numbers and percentages
 * - Download triggering with proper MIME type
 * - Dynamic import of xlsx library for code splitting
 *
 * Note: The main exportToExcel function uses dynamic import to keep xlsx
 * out of the initial bundle. The helper functions (createWorkbook, addSummarySheet, etc.)
 * are kept synchronous for backward compatibility with existing tests.
 */

import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import { formatCategoryLabel } from '../classifyComponent';

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
    category: string;
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

/**
 * Create a new workbook
 * Uses synchronous API for backward compatibility
 */
export function createWorkbook(): WorkBook {
  return XLSX.utils.book_new();
}

/**
 * Add Summary sheet to workbook
 * Uses synchronous API for backward compatibility
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
 * Uses synchronous API for backward compatibility
 */
export function addBreakdownSheet(
  workbook: WorkBook,
  categoryBreakdown: CalculationExportData['categoryBreakdown'],
  config: SheetConfig = {}
): void {
  const sheetName = config.sheetName || 'Breakdown';

  // Remove Scope column - just show Category, Emissions, Percentage
  const headers = ['Category', 'Emissions (kg CO2e)', 'Percentage'];
  const dataRows = categoryBreakdown.map((item) => [
    item.category,
    item.emissions,
    item.percentage / 100, // Excel percentage format expects decimal
  ]);

  const sheetData = [headers, ...dataRows];
  const sheet = XLSX.utils.aoa_to_sheet(sheetData);

  // Set column widths
  sheet['!cols'] = [{ wch: 30 }, { wch: 20 }, { wch: 12 }];

  // Apply number formats
  const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1');
  for (let row = 1; row <= range.e.r; row++) {
    // Emissions column (B)
    const emissionsCell = XLSX.utils.encode_cell({ r: row, c: 1 });
    if (sheet[emissionsCell]) {
      sheet[emissionsCell].z = '#,##0.00';
    }

    // Percentage column (C)
    const percentCell = XLSX.utils.encode_cell({ r: row, c: 2 });
    if (sheet[percentCell]) {
      sheet[percentCell].z = '0.0%';
    }
  }

  XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
}

/**
 * Add BOM sheet to workbook
 * Uses synchronous API for backward compatibility
 */
export function addBOMSheet(
  workbook: WorkBook,
  bomEntries: CalculationExportData['bomEntries'],
  totalProductEmissions: number,
  config: SheetConfig = {}
): void {
  const sheetName = config.sheetName || 'Bill of Materials';

  const headers = [
    'Component',
    'Category',
    'Quantity',
    'Unit',
    'Emission Factor',
    'Emissions (kg CO2e)',
    'Percentage',
  ];

  // Calculate sum of BOM item emissions
  const bomEmissionsSum = bomEntries.reduce((sum, e) => sum + e.emissions, 0);

  const dataRows: (string | number)[][] = bomEntries.map((entry) => [
    entry.component,
    formatCategoryLabel(entry.category),
    entry.quantity,
    entry.unit,
    entry.emissionFactor,
    entry.emissions,
    totalProductEmissions > 0 ? (entry.emissions / totalProductEmissions) : 0,
  ]);

  // Add "Other (not itemized)" row if there's unallocated emissions
  const unallocatedEmissions = totalProductEmissions - bomEmissionsSum;
  if (unallocatedEmissions > 0.001) {
    dataRows.push([
      'Other (not itemized)',
      '',
      '',
      '',
      '',
      unallocatedEmissions,
      totalProductEmissions > 0 ? (unallocatedEmissions / totalProductEmissions) : 0,
    ]);
  }

  // Add totals row
  dataRows.push(['TOTAL', '', '', '', '', totalProductEmissions, 1]);

  const sheetData = [headers, ...dataRows];
  const sheet = XLSX.utils.aoa_to_sheet(sheetData);

  // Set column widths
  sheet['!cols'] = [
    { wch: 30 },  // Component
    { wch: 12 },  // Category
    { wch: 12 },  // Quantity
    { wch: 10 },  // Unit
    { wch: 18 },  // Emission Factor
    { wch: 20 },  // Emissions
    { wch: 12 },  // Percentage
  ];

  // Apply percentage format to last column (index 6)
  const range = XLSX.utils.decode_range(sheet['!ref'] || 'A1');
  for (let row = 1; row <= range.e.r; row++) {
    const percentCell = XLSX.utils.encode_cell({ r: row, c: 6 });
    if (sheet[percentCell]) {
      sheet[percentCell].z = '0.0%';
    }
  }

  XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
}

/**
 * Export data to Excel file
 * Uses dynamic import to load xlsx library on demand for bundle optimization.
 * This is the main entry point for Excel export functionality.
 */
export async function exportToExcel(
  data: CalculationExportData,
  filename: string
): Promise<void> {
  // Dynamically load xlsx - this is where the code splitting happens
  // The import('xlsx') statement tells Vite/Rollup to create a separate chunk
  const xlsxModule = await import('xlsx');

  const workbook = xlsxModule.utils.book_new();

  // Add Summary sheet
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

  const summarySheet = xlsxModule.utils.aoa_to_sheet(summaryData);
  summarySheet['!cols'] = [{ wch: 25 }, { wch: 30 }, { wch: 15 }];
  summarySheet['!merges'] = [{ s: { r: 0, c: 0 }, e: { r: 0, c: 2 } }];
  xlsxModule.utils.book_append_sheet(workbook, summarySheet, 'Summary');

  // Add Breakdown sheet
  const breakdownHeaders = ['Category', 'Emissions (kg CO2e)', 'Percentage'];
  const breakdownDataRows = data.categoryBreakdown.map((item) => [
    item.category,
    item.emissions,
    item.percentage / 100,
  ]);
  const breakdownSheetData = [breakdownHeaders, ...breakdownDataRows];
  const breakdownSheet = xlsxModule.utils.aoa_to_sheet(breakdownSheetData);
  breakdownSheet['!cols'] = [{ wch: 30 }, { wch: 20 }, { wch: 12 }];

  const breakdownRange = xlsxModule.utils.decode_range(breakdownSheet['!ref'] || 'A1');
  for (let row = 1; row <= breakdownRange.e.r; row++) {
    const emissionsCell = xlsxModule.utils.encode_cell({ r: row, c: 1 });
    if (breakdownSheet[emissionsCell]) {
      breakdownSheet[emissionsCell].z = '#,##0.00';
    }
    const percentCell = xlsxModule.utils.encode_cell({ r: row, c: 2 });
    if (breakdownSheet[percentCell]) {
      breakdownSheet[percentCell].z = '0.0%';
    }
  }
  xlsxModule.utils.book_append_sheet(workbook, breakdownSheet, 'Breakdown');

  // Add BOM sheet
  const bomHeaders = [
    'Component',
    'Category',
    'Quantity',
    'Unit',
    'Emission Factor',
    'Emissions (kg CO2e)',
    'Percentage',
  ];
  const bomEmissionsSum = data.bomEntries.reduce((sum, e) => sum + e.emissions, 0);
  const bomDataRows: (string | number)[][] = data.bomEntries.map((entry) => [
    entry.component,
    formatCategoryLabel(entry.category),
    entry.quantity,
    entry.unit,
    entry.emissionFactor,
    entry.emissions,
    data.totalEmissions > 0 ? (entry.emissions / data.totalEmissions) : 0,
  ]);

  const unallocatedEmissions = data.totalEmissions - bomEmissionsSum;
  if (unallocatedEmissions > 0.001) {
    bomDataRows.push([
      'Other (not itemized)',
      '',
      '',
      '',
      '',
      unallocatedEmissions,
      data.totalEmissions > 0 ? (unallocatedEmissions / data.totalEmissions) : 0,
    ]);
  }
  bomDataRows.push(['TOTAL', '', '', '', '', data.totalEmissions, 1]);

  const bomSheetData = [bomHeaders, ...bomDataRows];
  const bomSheet = xlsxModule.utils.aoa_to_sheet(bomSheetData);
  bomSheet['!cols'] = [
    { wch: 30 }, { wch: 12 }, { wch: 12 }, { wch: 10 },
    { wch: 18 }, { wch: 20 }, { wch: 12 },
  ];

  const bomRange = xlsxModule.utils.decode_range(bomSheet['!ref'] || 'A1');
  for (let row = 1; row <= bomRange.e.r; row++) {
    const percentCell = xlsxModule.utils.encode_cell({ r: row, c: 6 });
    if (bomSheet[percentCell]) {
      bomSheet[percentCell].z = '0.0%';
    }
  }
  xlsxModule.utils.book_append_sheet(workbook, bomSheet, 'Bill of Materials');

  // Write workbook to array buffer
  const excelBuffer = xlsxModule.write(workbook, {
    bookType: 'xlsx',
    type: 'array',
  });

  // Create blob and trigger download
  const blob = new Blob([excelBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });

  saveAs(blob, `${filename}.xlsx`);
}
