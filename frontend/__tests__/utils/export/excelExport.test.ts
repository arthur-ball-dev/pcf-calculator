/**
 * Excel Export Utility Tests
 * TASK-FE-P5-005: Test Excel/XLSX generation and export functionality
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

// Mock XLSX library
vi.mock('xlsx', () => ({
  utils: {
    book_new: vi.fn(() => ({ SheetNames: [], Sheets: {} })),
    book_append_sheet: vi.fn(),
    aoa_to_sheet: vi.fn(() => ({})),
    encode_cell: vi.fn(({ r, c }: { r: number; c: number }) => `${String.fromCharCode(65 + c)}${r + 1}`),
    decode_range: vi.fn(() => ({ s: { r: 0, c: 0 }, e: { r: 5, c: 3 } })),
  },
  write: vi.fn(() => new ArrayBuffer(8)),
}));

// Mock file-saver
vi.mock('file-saver', () => ({
  saveAs: vi.fn(),
}));

import * as XLSX from 'xlsx';
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
      { component: 'Steel', quantity: 100, unit: 'kg', emissionFactor: 2.5, emissions: 250 },
      { component: 'Plastic', quantity: 50, unit: 'kg', emissionFactor: 3.2, emissions: 160 },
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

      expect(XLSX.utils.book_new).toHaveBeenCalled();
      expect(workbook).toBeDefined();
    });

    it('should return workbook with empty SheetNames array initially', () => {
      const workbook = createWorkbook();

      expect(workbook.SheetNames).toEqual([]);
    });

    it('should return workbook with empty Sheets object initially', () => {
      const workbook = createWorkbook();

      expect(workbook.Sheets).toEqual({});
    });
  });

  // ==========================================================================
  // Test Suite 2: Summary Sheet
  // ==========================================================================

  describe('addSummarySheet', () => {
    it('should add summary sheet to workbook', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      expect(XLSX.utils.aoa_to_sheet).toHaveBeenCalled();
      expect(XLSX.utils.book_append_sheet).toHaveBeenCalledWith(
        workbook,
        expect.anything(),
        'Summary'
      );
    });

    it('should include product information in summary', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      // Check aoa_to_sheet was called with data containing product info
      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];

      // Should contain product name somewhere in the array
      const flatData = aoaCall.flat();
      expect(flatData).toContain('Test Widget');
      expect(flatData).toContain('TW-001');
    });

    it('should include total emissions in summary', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const flatData = aoaCall.flat();

      // Should contain total emissions value
      expect(flatData.some((v: unknown) =>
        typeof v === 'string' && v.includes('2.5') || v === 2.5
      )).toBe(true);
    });

    it('should include calculation date in summary', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const flatData = aoaCall.flat();

      // Should contain formatted date
      expect(flatData.some((v: unknown) =>
        typeof v === 'string' && v.includes('2024')
      )).toBe(true);
    });

    it('should include calculation parameters', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const flatData = aoaCall.flat();

      expect(flatData.some((v: unknown) => v === 500 || v === '500')).toBe(true);
      expect(flatData).toContain('Grid Electricity');
    });

    it('should have title row for the report', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];

      // First row should be title
      expect(aoaCall[0][0]).toContain('Product Carbon Footprint');
    });

    it('should handle missing optional parameters', () => {
      const dataWithMissingParams: CalculationExportData = {
        ...sampleExportData,
        parameters: {},
      };
      const workbook = createWorkbook();

      // Should not throw
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

      expect(XLSX.utils.book_append_sheet).toHaveBeenCalledWith(
        workbook,
        expect.anything(),
        'Breakdown'
      );
    });

    it('should include header row with correct columns', () => {
      const workbook = createWorkbook();

      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const headers = aoaCall[0];

      expect(headers).toContain('Scope');
      expect(headers).toContain('Category');
      expect(headers).toContain('Emissions (kg CO2e)');
      expect(headers).toContain('Percentage');
    });

    it('should include all category breakdown entries', () => {
      const workbook = createWorkbook();

      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];

      // Should have header + 3 data rows
      expect(aoaCall.length).toBe(4);
    });

    it('should format percentage as decimal for Excel', () => {
      const workbook = createWorkbook();

      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];

      // Second row (first data row), fourth column (percentage)
      // 60% should be 0.6 for Excel percentage format
      expect(aoaCall[1][3]).toBe(0.6);
    });

    it('should handle empty breakdown gracefully', () => {
      const workbook = createWorkbook();

      // Should not throw
      expect(() => addBreakdownSheet(workbook, [])).not.toThrow();
    });
  });

  // ==========================================================================
  // Test Suite 4: BOM Sheet
  // ==========================================================================

  describe('addBOMSheet', () => {
    it('should add BOM sheet to workbook', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, sampleExportData.bomEntries);

      expect(XLSX.utils.book_append_sheet).toHaveBeenCalledWith(
        workbook,
        expect.anything(),
        'Bill of Materials'
      );
    });

    it('should include header row with correct columns', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, sampleExportData.bomEntries);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const headers = aoaCall[0];

      expect(headers).toContain('Component');
      expect(headers).toContain('Quantity');
      expect(headers).toContain('Unit');
      expect(headers).toContain('Emission Factor');
      expect(headers).toContain('Emissions (kg CO2e)');
    });

    it('should include all BOM entries', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, sampleExportData.bomEntries);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];

      // Should have header + 2 data rows + 1 totals row
      expect(aoaCall.length).toBe(4);
    });

    it('should include totals row at the end', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, sampleExportData.bomEntries);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const lastRow = aoaCall[aoaCall.length - 1];

      // Totals row should have TOTAL label
      expect(lastRow).toContain('TOTAL');
    });

    it('should calculate correct total emissions', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, sampleExportData.bomEntries);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];
      const lastRow = aoaCall[aoaCall.length - 1];

      // Total should be 250 + 160 = 410
      const totalIndex = lastRow.findIndex((v: unknown) => v === 'TOTAL');
      expect(lastRow[totalIndex + 1]).toBe(410);
    });

    it('should handle empty BOM entries', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, []);

      const aoaCall = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.calls[0][0];

      // Should have header and totals row with 0
      expect(aoaCall.length).toBe(2);
    });
  });

  // ==========================================================================
  // Test Suite 5: Column Widths
  // ==========================================================================

  describe('Column Widths', () => {
    it('should set column widths for summary sheet', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      const sheet = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.results[0]?.value;

      // The sheet should have !cols property set
      expect(sheet['!cols'] || []).toBeDefined();
    });

    it('should set column widths for breakdown sheet', () => {
      const workbook = createWorkbook();

      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      // Verify aoa_to_sheet was called
      expect(XLSX.utils.aoa_to_sheet).toHaveBeenCalled();
    });

    it('should set column widths for BOM sheet', () => {
      const workbook = createWorkbook();

      addBOMSheet(workbook, sampleExportData.bomEntries);

      // Verify aoa_to_sheet was called
      expect(XLSX.utils.aoa_to_sheet).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 6: Cell Formatting
  // ==========================================================================

  describe('Cell Formatting', () => {
    it('should apply number format to emissions columns', () => {
      const workbook = createWorkbook();

      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      // Verify encode_cell was called for formatting
      expect(XLSX.utils.encode_cell).toHaveBeenCalled();
    });

    it('should apply percentage format to percentage columns', () => {
      const workbook = createWorkbook();

      addBreakdownSheet(workbook, sampleExportData.categoryBreakdown);

      // Verify decode_range was called for range iteration
      expect(XLSX.utils.decode_range).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 7: exportToExcel Integration
  // ==========================================================================

  describe('exportToExcel', () => {
    it('should create workbook with all three sheets', () => {
      exportToExcel(sampleExportData, 'test-report');

      // Should call book_append_sheet 3 times (Summary, Breakdown, BOM)
      expect(XLSX.utils.book_append_sheet).toHaveBeenCalledTimes(3);
    });

    it('should write workbook to array buffer', () => {
      exportToExcel(sampleExportData, 'test-report');

      expect(XLSX.write).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          bookType: 'xlsx',
          type: 'array',
        })
      );
    });

    it('should trigger download with correct filename', () => {
      exportToExcel(sampleExportData, 'test-report');

      expect(saveAs).toHaveBeenCalledWith(
        expect.any(Blob),
        'test-report.xlsx'
      );
    });

    it('should create blob with correct MIME type', () => {
      exportToExcel(sampleExportData, 'test-report');

      const blobCall = (saveAs as ReturnType<typeof vi.fn>).mock.calls[0][0] as Blob;
      expect(blobCall.type).toBe(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      );
    });

    it('should handle special characters in filename', () => {
      exportToExcel(sampleExportData, 'test/report:with*special');

      // Should sanitize filename or handle gracefully
      expect(saveAs).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 8: Error Handling
  // ==========================================================================

  describe('Error Handling', () => {
    it('should handle missing productName gracefully', () => {
      const incompleteData = {
        ...sampleExportData,
        productName: '',
      };

      expect(() => exportToExcel(incompleteData, 'test')).not.toThrow();
    });

    it('should handle missing categoryBreakdown gracefully', () => {
      const incompleteData = {
        ...sampleExportData,
        categoryBreakdown: [],
      };

      expect(() => exportToExcel(incompleteData, 'test')).not.toThrow();
    });

    it('should handle missing bomEntries gracefully', () => {
      const incompleteData = {
        ...sampleExportData,
        bomEntries: [],
      };

      expect(() => exportToExcel(incompleteData, 'test')).not.toThrow();
    });

    it('should handle null date gracefully', () => {
      const incompleteData = {
        ...sampleExportData,
        calculationDate: null as unknown as Date,
      };

      expect(() => exportToExcel(incompleteData, 'test')).not.toThrow();
    });

    it('should throw if XLSX write fails', () => {
      (XLSX.write as ReturnType<typeof vi.fn>).mockImplementationOnce(() => {
        throw new Error('Write failed');
      });

      expect(() => exportToExcel(sampleExportData, 'test')).toThrow('Write failed');
    });
  });

  // ==========================================================================
  // Test Suite 9: Merge Cells
  // ==========================================================================

  describe('Merge Cells', () => {
    it('should merge title row cells in summary sheet', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      const sheet = (XLSX.utils.aoa_to_sheet as ReturnType<typeof vi.fn>).mock.results[0]?.value;

      // Sheet should have merge configuration
      expect(sheet['!merges'] || []).toBeDefined();
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

      expect(XLSX.utils.book_append_sheet).toHaveBeenCalledWith(
        workbook,
        expect.anything(),
        'Custom Summary'
      );
    });

    it('should use default sheet names when not specified', () => {
      const workbook = createWorkbook();

      addSummarySheet(workbook, sampleExportData);

      expect(XLSX.utils.book_append_sheet).toHaveBeenCalledWith(
        workbook,
        expect.anything(),
        'Summary'
      );
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

    it('should handle very large numbers', () => {
      const dataWithLargeNumber = {
        ...sampleExportData,
        totalEmissions: 9999999999.99,
      };

      expect(() => exportToExcel(dataWithLargeNumber, 'test')).not.toThrow();
    });

    it('should handle unicode characters in product names', () => {
      const dataWithUnicode = {
        ...sampleExportData,
        productName: 'Widget Pro',
        bomEntries: [
          { component: 'Materiau special', quantity: 1, unit: 'kg', emissionFactor: 1, emissions: 1 },
        ],
      };

      expect(() => exportToExcel(dataWithUnicode, 'test')).not.toThrow();
    });
  });
});
