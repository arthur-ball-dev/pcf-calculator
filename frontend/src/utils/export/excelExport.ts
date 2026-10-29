/**
 * Excel Export Utility
 * TASK-FE-P5-005: Excel/XLSX generation and export functionality
 * TASK-FE-P7-024: Dynamic import for bundle optimization
 * TASK-FE-P8-008: Attribution sheet for legal compliance
 * P1-FIX-16: Replaced xlsx with exceljs for better license compliance
 *
 * Features:
 * - Multi-sheet workbook creation (Summary, Breakdown, BOM, Attribution)
 * - Column width configuration
 * - Cell formatting for numbers and percentages
 * - Download triggering with proper MIME type
 * - Dynamic import of exceljs library for code splitting
 * - Attribution sheet for data source compliance
 *
 * Note: The main exportToExcel function uses dynamic import to keep exceljs
 * out of the initial bundle. The helper functions (createWorkbook, addSummarySheet, etc.)
 * are kept synchronous for backward compatibility with existing tests.
 */

import ExcelJS from 'exceljs';
import { saveAs } from 'file-saver';
import { formatCategoryLabel } from '../classifyComponent';
import type { DataSourceInfo } from '../exportAttribution';

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
  // Data sources for attribution sheet (TASK-FE-P8-008)
  dataSources?: DataSourceInfo[];
}

export interface SheetConfig {
  sheetName?: string;
}

type WorkBook = ExcelJS.Workbook;

/**
 * Create a new workbook
 * Uses synchronous API for backward compatibility
 */
export function createWorkbook(): WorkBook {
  return new ExcelJS.Workbook();
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

  const sheet = workbook.addWorksheet(sheetName);

  // Set column widths
  sheet.columns = [
    { width: 25 },
    { width: 30 },
    { width: 15 },
  ];

  // Add data rows
  const rows = [
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

  rows.forEach(row => sheet.addRow(row));

  // Merge cells for title
  sheet.mergeCells('A1:C1');

  // Bold title
  const titleCell = sheet.getCell('A1');
  titleCell.font = { bold: true, size: 14 };
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

  const sheet = workbook.addWorksheet(sheetName);

  // Set column widths
  sheet.columns = [
    { width: 30 },
    { width: 20 },
    { width: 12 },
  ];

  // Add header row
  const headerRow = sheet.addRow(['Category', 'Emissions (kg CO2e)', 'Percentage']);
  headerRow.font = { bold: true };

  // Add data rows
  categoryBreakdown.forEach((item) => {
    const row = sheet.addRow([
      item.category,
      item.emissions,
      item.percentage / 100,
    ]);

    // Format emissions column
    row.getCell(2).numFmt = '#,##0.00';
    // Format percentage column
    row.getCell(3).numFmt = '0.0%';
  });
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

  const sheet = workbook.addWorksheet(sheetName);

  // Set column widths
  sheet.columns = [
    { width: 30 },  // Component
    { width: 12 },  // Category
    { width: 12 },  // Quantity
    { width: 10 },  // Unit
    { width: 18 },  // Emission Factor
    { width: 20 },  // Emissions
    { width: 12 },  // Percentage
  ];

  // Add header row
  const headerRow = sheet.addRow([
    'Component',
    'Category',
    'Quantity',
    'Unit',
    'Emission Factor',
    'Emissions (kg CO2e)',
    'Percentage',
  ]);
  headerRow.font = { bold: true };

  // Calculate sum of BOM item emissions
  const bomEmissionsSum = bomEntries.reduce((sum, e) => sum + e.emissions, 0);

  // Add data rows
  bomEntries.forEach((entry) => {
    const row = sheet.addRow([
      entry.component,
      formatCategoryLabel(entry.category),
      entry.quantity,
      entry.unit,
      entry.emissionFactor,
      entry.emissions,
      totalProductEmissions > 0 ? (entry.emissions / totalProductEmissions) : 0,
    ]);
    row.getCell(7).numFmt = '0.0%';
  });

  // Add "Other (not itemized)" row if there's unallocated emissions
  const unallocatedEmissions = totalProductEmissions - bomEmissionsSum;
  if (unallocatedEmissions > 0.001) {
    const otherRow = sheet.addRow([
      'Other (not itemized)',
      '',
      '',
      '',
      '',
      unallocatedEmissions,
      totalProductEmissions > 0 ? (unallocatedEmissions / totalProductEmissions) : 0,
    ]);
    otherRow.getCell(7).numFmt = '0.0%';
  }

  // Add totals row
  const totalRow = sheet.addRow(['TOTAL', '', '', '', '', totalProductEmissions, 1]);
  totalRow.font = { bold: true };
  totalRow.getCell(7).numFmt = '0.0%';
}

/**
 * Add Attribution sheet to workbook
 * TASK-FE-P8-008: Legal compliance for data sources
 * Uses synchronous API for backward compatibility
 */
export function addAttributionSheet(
  workbook: WorkBook,
  dataSources: DataSourceInfo[],
  config: SheetConfig = {}
): void {
  const sheetName = config.sheetName || 'Data Sources';

  const sheet = workbook.addWorksheet(sheetName);

  // Set column widths
  sheet.columns = [
    { width: 40 },
    { width: 20 },
    { width: 80 },
  ];

  // Title
  sheet.addRow(['DATA SOURCE ATTRIBUTIONS']);
  sheet.mergeCells('A1:C1');
  sheet.getCell('A1').font = { bold: true, size: 14 };

  sheet.addRow(['']);
  sheet.addRow(['This calculation uses data from the following sources:']);
  sheet.addRow(['']);

  // Header row
  const headerRow = sheet.addRow(['Source', 'Attribution Required', 'Attribution Text']);
  headerRow.font = { bold: true };

  // Add each data source that requires attribution
  const requiredSources = dataSources.filter(s => s.attribution_required && s.attribution_text);

  if (requiredSources.length > 0) {
    for (const source of requiredSources) {
      sheet.addRow([source.name, 'Yes', source.attribution_text]);
    }
  } else {
    sheet.addRow(['No specific attributions required', '', '']);
  }

  // Add disclaimer section
  sheet.addRow(['']);
  sheet.addRow(['']);
  const disclaimerRow = sheet.addRow(['DISCLAIMER']);
  disclaimerRow.font = { bold: true };
  sheet.addRow(['']);
  sheet.addRow(['Calculations are for informational purposes only.']);
  sheet.addRow(['No warranty is provided regarding accuracy.']);
  sheet.addRow(['Consult qualified professionals for regulatory compliance.']);
}

/**
 * Export data to Excel file
 * Uses dynamic import to load exceljs library on demand for bundle optimization.
 * This is the main entry point for Excel export functionality.
 */
export async function exportToExcel(
  data: CalculationExportData,
  filename: string
): Promise<void> {
  // Dynamically load exceljs - this is where the code splitting happens
  const ExcelJSModule = await import('exceljs');
  const workbook = new ExcelJSModule.default.Workbook();

  // Add Summary sheet
  const dateStr = data.calculationDate
    ? data.calculationDate.toLocaleDateString()
    : 'N/A';

  const summarySheet = workbook.addWorksheet('Summary');
  summarySheet.columns = [{ width: 25 }, { width: 30 }, { width: 15 }];

  const summaryRows = [
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
  summaryRows.forEach(row => summarySheet.addRow(row));
  summarySheet.mergeCells('A1:C1');
  summarySheet.getCell('A1').font = { bold: true, size: 14 };

  // Add Breakdown sheet
  const breakdownSheet = workbook.addWorksheet('Breakdown');
  breakdownSheet.columns = [{ width: 30 }, { width: 20 }, { width: 12 }];

  const breakdownHeader = breakdownSheet.addRow(['Category', 'Emissions (kg CO2e)', 'Percentage']);
  breakdownHeader.font = { bold: true };

  data.categoryBreakdown.forEach((item) => {
    const row = breakdownSheet.addRow([
      item.category,
      item.emissions,
      item.percentage / 100,
    ]);
    row.getCell(2).numFmt = '#,##0.00';
    row.getCell(3).numFmt = '0.0%';
  });

  // Add BOM sheet
  const bomSheet = workbook.addWorksheet('Bill of Materials');
  bomSheet.columns = [
    { width: 30 }, { width: 12 }, { width: 12 }, { width: 10 },
    { width: 18 }, { width: 20 }, { width: 12 },
  ];

  const bomHeader = bomSheet.addRow([
    'Component', 'Category', 'Quantity', 'Unit',
    'Emission Factor', 'Emissions (kg CO2e)', 'Percentage',
  ]);
  bomHeader.font = { bold: true };

  const bomEmissionsSum = data.bomEntries.reduce((sum, e) => sum + e.emissions, 0);
  data.bomEntries.forEach((entry) => {
    const row = bomSheet.addRow([
      entry.component,
      formatCategoryLabel(entry.category),
      entry.quantity,
      entry.unit,
      entry.emissionFactor,
      entry.emissions,
      data.totalEmissions > 0 ? (entry.emissions / data.totalEmissions) : 0,
    ]);
    row.getCell(7).numFmt = '0.0%';
  });

  const unallocatedEmissions = data.totalEmissions - bomEmissionsSum;
  if (unallocatedEmissions > 0.001) {
    const otherRow = bomSheet.addRow([
      'Other (not itemized)', '', '', '', '',
      unallocatedEmissions,
      data.totalEmissions > 0 ? (unallocatedEmissions / data.totalEmissions) : 0,
    ]);
    otherRow.getCell(7).numFmt = '0.0%';
  }

  const totalRow = bomSheet.addRow(['TOTAL', '', '', '', '', data.totalEmissions, 1]);
  totalRow.font = { bold: true };
  totalRow.getCell(7).numFmt = '0.0%';

  // Add Attribution sheet (TASK-FE-P8-008)
  const dataSources = data.dataSources || [];
  const attributionSheet = workbook.addWorksheet('Data Sources');
  attributionSheet.columns = [{ width: 40 }, { width: 20 }, { width: 80 }];

  attributionSheet.addRow(['DATA SOURCE ATTRIBUTIONS']);
  attributionSheet.mergeCells('A1:C1');
  attributionSheet.getCell('A1').font = { bold: true, size: 14 };

  attributionSheet.addRow(['']);
  attributionSheet.addRow(['This calculation uses data from the following sources:']);
  attributionSheet.addRow(['']);

  const attrHeader = attributionSheet.addRow(['Source', 'Attribution Required', 'Attribution Text']);
  attrHeader.font = { bold: true };

  const requiredSources = dataSources.filter(s => s.attribution_required && s.attribution_text);

  if (requiredSources.length > 0) {
    for (const source of requiredSources) {
      attributionSheet.addRow([source.name, 'Yes', source.attribution_text]);
    }
  } else {
    attributionSheet.addRow(['No specific attributions required', '', '']);
  }

  attributionSheet.addRow(['']);
  attributionSheet.addRow(['']);
  const disclaimerRow = attributionSheet.addRow(['DISCLAIMER']);
  disclaimerRow.font = { bold: true };
  attributionSheet.addRow(['']);
  attributionSheet.addRow(['Calculations are for informational purposes only.']);
  attributionSheet.addRow(['No warranty is provided regarding accuracy.']);
  attributionSheet.addRow(['Consult qualified professionals for regulatory compliance.']);

  // Write workbook to buffer and trigger download
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });

  saveAs(blob, `${filename}.xlsx`);
}
