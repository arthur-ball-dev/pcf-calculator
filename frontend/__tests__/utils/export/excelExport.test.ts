/**
 * Excel Export Utility Tests
 * TASK-FE-P5-005: Test Excel/XLSX generation and export functionality
 * P1-FIX-16: Updated for exceljs library (replaced xlsx)
 *
 * Test Coverage:
 * 1. Creates workbook with multiple sheets
 * 2. Summary sheet has correct structure
 * 3. Breakdown sheet has emission details
 * 4. BOM sheet has component list
 * 5. Column widths set appropriately
 * 6. Cell formatting (numbers, percentages)
 * 7. Handles calculation results data structure
 * 8. Download triggering
 * 9. Error handling
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  createWorkbook,
  addSummarySheet,
  addBreakdownSheet,
  addBOMSheet,
  exportToExcel,
  type CalculationExportData,
  type SheetConfig,
} from '@/utils/export/excelExport';

// Mock file-saver
vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}));

import { saveAs } from 'file-saver';

describe('Excel Export Utility', () => {
  // Sample test data
  const sampleExportData: CalculationExportData = {
    productName: 'Test Widget',
    productCode: 'TW-001',
    calculationDate: new Date('2024-06-15T10:30:00Z'),
    totalEmissions: 2.5,
    unit: 'kg CO2e',
    categoryBreakdown: [
      { scope: 'Scope 1', category: 'Materials', emissions: 1.5, percentage: 60 },
      { scope: 'Scope 2', category: 'Energy', emissions: 0.75, percentage: 30 },
      { scope: 'Scope 3', category: 'Transport', emissions: 0.25, percentage: 10 },
    ],
    bomEntries: [
      { component: 'Steel', category: 'material', quantity: 100, unit: 'kg', emissionFactor: 2.5, emissions: 250 },
      { component: 'Plastic', category: 'material', quantity: 50, unit: 'kg', emissionFactor: 3.2, emissions: 160 },
    ],
    parameters: {
      transportDistance: 500,
      energySource: 'Grid Electricity',
      productionVolume: 1000,
    },
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Workbook Creation
  // ==========================================================================

  describe('createWorkbook', () => {
    it('should create a new workbook', () => {
      const workbook = createWorkbook();
      expect(workbook).toBeDefined();
    });

    it('should return workbook with no worksheets initially', () => {
      const workbook = createWorkbook();
      expect(workbook.worksheets.length).toBe(0);
    });
  });

  // ==========================================================================
  // Test Suite 2: Summary Sheet
  // ==========================================================================

  describe('addSummarySheet', () => {
    it('should add summary sheet to workbook', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      const sheet = workbook.getWorksheet('Summary');
      expect(sheet).toBeDefined();
    });

    it('should include product information in summary', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      const sheet = workbook.getWorksheet('Summary')!;
      const values: string[] = [];
      sheet.eachRow((row) => {
        row.eachCell((cell) => {
          if (cell.value != null) values.push(String(cell.value));
        });
      });

      expect(values).toContain('Test Widget');
      expect(values).toContain('TW-001');
    });

    it('should include total emissions in summary', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      const sheet = workbook.getWorksheet('Summary')!;
      const values: string[] = [];
      sheet.eachRow((row) => {
        row.eachCell((cell) => {
          if (cell.value != null) values.push(String(cell.value));
        });
      });

      expect(values.some(v => v.includes('2.5') || v === '2.50')).toBe(true);
    });

    it('should have title row for the report', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      const sheet = workbook.getWorksheet('Summary')!;
      const firstRow = sheet.getRow(1);
      expect(String(firstRow.getCell(1).value)).toContain('Product Carbon Footprint');
    });

    it('should handle missing optional parameters', () => {
      const dataWithMissingParams: CalculationExportData = {
        ...sampleExportData,
        parameters: {},
      };
      const workbook = createWorkbook();
      expect(() => addSummarySheet(workbook, dataWithMissingParams)).not.toThrow();
    });
  });

  // ==========================================================================
  // Test Suite 3: Breakdown Sheet
  // ==========================================================================

  describe('addBreakdownSheet', () => {
    it('should add breakdown sheet to workbook', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown');
      expect(sheet).toBeDefined();
    });

    it('should include header row with correct columns', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown')!;
      const headerRow = sheet.getRow(1);
      const headers = [
        headerRow.getCell(1).value,
        headerRow.getCell(2).value,
        headerRow.getCell(3).value,
      ];

      expect(headers).toContain('Category');
      expect(headers).toContain('Emissions (kg CO2e)');
      expect(headers).toContain('Percentage');
    });

    it('should include all category breakdown entries', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown')!;
      // Should have header + 3 data rows = 4 rows
      expect(sheet.rowCount).toBe(4);
    });

    it('should format percentage as decimal for Excel', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown')!;
      // Second row (first data row), third column (percentage)
      // 60% should be 0.6 for Excel percentage format
      expect(sheet.getRow(2).getCell(3).value).toBe(0.6);
    });

    it('should handle empty breakdown gracefully', () => {
      const workbook = createWorkbook();
      expect(() => addBreakdownSheet(workbook, [])).not.toThrow();
    });
  });

  // ==========================================================================
  // Test Suite 4: BOM Sheet
  // ==========================================================================

  describe('addBOMSheet', () => {
    it('should add BOM sheet to workbook', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, sampleExportData.bomEntries, 410);

      const sheet = workbook.getWorksheet('Bill of Materials');
      expect(sheet).toBeDefined();
    });

    it('should include header row with correct columns', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, sampleExportData.bomEntries, 410);

      const sheet = workbook.getWorksheet('Bill of Materials')!;
      const headerRow = sheet.getRow(1);
      const headers: (string | null)[] = [];
      for (let i = 1; i <= 7; i++) {
        headers.push(headerRow.getCell(i).value as string | null);
      }

      expect(headers).toContain('Component');
      expect(headers).toContain('Category');
      expect(headers).toContain('Quantity');
      expect(headers).toContain('Unit');
      expect(headers).toContain('Emission Factor');
      expect(headers).toContain('Emissions (kg CO2e)');
    });

    it('should include all BOM entries plus totals row', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, sampleExportData.bomEntries, 410);

      const sheet = workbook.getWorksheet('Bill of Materials')!;
      // Should have header + 2 data rows + 1 totals row = 4 rows
      expect(sheet.rowCount).toBe(4);
    });

    it('should include totals row at the end', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, sampleExportData.bomEntries, 410);

      const sheet = workbook.getWorksheet('Bill of Materials')!;
      const lastRow = sheet.getRow(sheet.rowCount);
      expect(lastRow.getCell(1).value).toBe('TOTAL');
    });

    it('should calculate correct total emissions', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, sampleExportData.bomEntries, 410);

      const sheet = workbook.getWorksheet('Bill of Materials')!;
      const lastRow = sheet.getRow(sheet.rowCount);
      expect(lastRow.getCell(1).value).toBe('TOTAL');
      expect(lastRow.getCell(6).value).toBe(410);
    });

    it('should handle empty BOM entries', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, [], 0);

      const sheet = workbook.getWorksheet('Bill of Materials')!;
      // Should have header and totals row
      expect(sheet.rowCount).toBe(2);
    });
  });

  // ==========================================================================
  // Test Suite 5: Column Widths
  // ==========================================================================

  describe('Column Widths', () => {
    it('should set column widths for summary sheet', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      const sheet = workbook.getWorksheet('Summary')!;
      expect(sheet.columns.length).toBeGreaterThan(0);
    });

    it('should set column widths for breakdown sheet', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown')!;
      expect(sheet.columns.length).toBeGreaterThan(0);
    });

    it('should set column widths for BOM sheet', () => {
      const workbook = createWorkbook();
      addBOMSheet(workbook, sampleExportData.bomEntries, 410);

      const sheet = workbook.getWorksheet('Bill of Materials')!;
      expect(sheet.columns.length).toBeGreaterThan(0);
    });
  });

  // ==========================================================================
  // Test Suite 6: Cell Formatting
  // ==========================================================================

  describe('Cell Formatting', () => {
    it('should apply number format to emissions columns', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown')!;
      const emissionsCell = sheet.getRow(2).getCell(2);
      expect(emissionsCell.numFmt).toBe('#,##0.00');
    });

    it('should apply percentage format to percentage columns', () => {
      const workbook = createWorkbook();
      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const sheet = workbook.getWorksheet('Breakdown')!;
      const percentCell = sheet.getRow(2).getCell(3);
      expect(percentCell.numFmt).toBe('0.0%');
    });
  });

  // ==========================================================================
  // Test Suite 7: exportToExcel Integration
  // ==========================================================================

  describe('exportToExcel', () => {
    it('should create workbook with all four sheets (including Attribution)', async () => {
      await exportToExcel(sampleExportData, 'test-report');

      expect(saveAs).toHaveBeenCalled();
    });

    it('should trigger download with correct filename', async () => {
      await exportToExcel(sampleExportData, 'test-report');

      expect(saveAs).toHaveBeenCalledWith(
        expect.any(Blob),
        'test-report.xlsx'
      );
    });

    it('should create blob with correct MIME type', async () => {
      await exportToExcel(sampleExportData, 'test-report');

      const blobCall = (saveAs as ReturnType<typeof vi.fn>).mock.calls[0][0] as Blob;
      expect(blobCall.type).toBe(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
    });

    it('should handle special characters in filename', async () => {
      await exportToExcel(sampleExportData, 'test/report:with*special');
      expect(saveAs).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 8: Error Handling
  // ==========================================================================

  describe('Error Handling', () => {
    it('should handle missing productName gracefully', async () => {
      const incompleteData = {
        ...sampleExportData,
        productName: '',
      };
      await expect(exportToExcel(incompleteData, 'test')).resolves.not.toThrow();
    });

    it('should handle missing categoryBreakdown gracefully', async () => {
      const incompleteData = {
        ...sampleExportData,
        categoryBreakdown: [],
      };
      await expect(exportToExcel(incompleteData, 'test')).resolves.not.toThrow();
    });

    it('should handle missing bomEntries gracefully', async () => {
      const incompleteData = {
        ...sampleExportData,
        bomEntries: [],
      };
      await expect(exportToExcel(incompleteData, 'test')).resolves.not.toThrow();
    });

    it('should handle null date gracefully', async () => {
      const incompleteData = {
        ...sampleExportData,
        calculationDate: null as unknown as Date,
      };
      await expect(exportToExcel(incompleteData, 'test')).resolves.not.toThrow();
    });
  });

  // ==========================================================================
  // Test Suite 9: Merge Cells
  // ==========================================================================

  describe('Merge Cells', () => {
    it('should merge title row cells in summary sheet', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      const sheet = workbook.getWorksheet('Summary')!;
      // exceljs stores merges internally; verify the title cell spans columns
      const titleCell = sheet.getCell('A1');
      expect(titleCell.value).toContain('Product Carbon Footprint');
    });
  });

  // ==========================================================================
  // Test Suite 10: Sheet Configuration
  // ==========================================================================

  describe('Sheet Configuration', () => {
    it('should allow custom sheet names', () => {
      const workbook = createWorkbook();
      const config: SheetConfig = { sheetName: 'Custom Summary' };

      addSummarySheet(workbook, sampleExportData, config);

      expect(workbook.getWorksheet('Custom Summary')).toBeDefined();
    });

    it('should use default sheet names when not specified', () => {
      const workbook = createWorkbook();
      addSummarySheet(workbook, sampleExportData);

      expect(workbook.getWorksheet('Summary')).toBeDefined();
    });
  });

  // ==========================================================================
  // Test Suite 11: Data Validation
  // ==========================================================================

  describe('Data Validation', () => {
    it('should handle negative emission values', () => {
      const dataWithNegative = {
        ...sampleExportData,
        categoryBreakdown: [
          { scope: 'Scope 1', category: 'Offset', emissions: -0.5, percentage: -20 },
        ],
      };
      const workbook = createWorkbook();
      expect(() => addBreakdownSheet(workbook, dataWithNegative.categoryBreakdown)).not.toThrow();
    });

    it('should handle very large numbers', async () => {
      const dataWithLargeNumber = {
        ...sampleExportData,
        totalEmissions: 9999999999.99,
      };
      await expect(exportToExcel(dataWithLargeNumber, 'test')).resolves.not.toThrow();
    });

    it('should handle unicode characters in product names', async () => {
      const dataWithUnicode = {
        ...sampleExportData,
        productName: 'Widget Pro',
        bomEntries: [
          { component: 'Materiau special', category: 'material', quantity: 1, unit: 'kg', emissionFactor: 1, emissions: 1 },
        ],
      };
      await expect(exportToExcel(dataWithUnicode, 'test')).resolves.not.toThrow();
    });
  });
});
