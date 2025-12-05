/**
 * CSV Export Utility Tests
 * TASK-FE-P5-005: Test CSV generation and export functionality
 *
 * Test Coverage:
 * 1. Converts array of objects to CSV string
 * 2. Includes headers by default
 * 3. Handles custom delimiters (semicolon for EU)
 * 4. Escapes values with commas, quotes, newlines
 * 5. UTF-8 BOM prepended for Excel compatibility
 * 6. Date formatting
 * 7. Number formatting (locale-aware)
 * 8. Handles empty arrays
 * 9. Handles null/undefined values
 * 10. Download triggering with proper MIME type
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  generateCSVString,
  exportToCSV,
  downloadFile,
  type CSVOptions,
} from '@/utils/export/csvExport';

// Mock DOM APIs for download testing
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = vi.fn();
const mockClick = vi.fn();
const mockAppendChild = vi.fn();
const mockRemoveChild = vi.fn();

describe('CSV Export Utility', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Mock URL API
    global.URL.createObjectURL = mockCreateObjectURL;
    global.URL.revokeObjectURL = mockRevokeObjectURL;

    // Mock document methods for download
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      if (tagName === 'a') {
        return {
          href: '',
          download: '',
          style: { visibility: '' },
          click: mockClick,
        } as unknown as HTMLAnchorElement;
      }
      return document.createElement(tagName);
    });

    vi.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild);
    vi.spyOn(document.body, 'removeChild').mockImplementation(mockRemoveChild);
  });

  // ==========================================================================
  // Test Suite 1: Basic CSV Generation
  // ==========================================================================

  describe('generateCSVString', () => {
    it('should convert array of objects to CSV string', () => {
      const data = [
        { name: 'Product A', value: 100 },
        { name: 'Product B', value: 200 },
      ];

      const result = generateCSVString(data);

      // Should contain headers and data rows
      expect(result).toContain('name,value');
      expect(result).toContain('Product A,100');
      expect(result).toContain('Product B,200');
    });

    it('should include headers by default', () => {
      const data = [
        { scope: 'Scope 1', category: 'Materials', emissions: 1.5 },
      ];

      const result = generateCSVString(data);
      const lines = result.split('\n');

      // First line should be headers
      expect(lines[0]).toBe('scope,category,emissions');
    });

    it('should exclude headers when includeHeaders is false', () => {
      const data = [
        { name: 'Product A', value: 100 },
      ];

      const result = generateCSVString(data, { includeHeaders: false });
      const lines = result.split('\n').filter(line => line.length > 0);

      // Should only have data row, no headers
      expect(lines.length).toBe(1);
      expect(lines[0]).toBe('Product A,100.00');
    });

    it('should use custom headers when provided', () => {
      const data = [
        { name: 'Product A', value: 100 },
      ];
      const customHeaders = ['Product Name', 'Emission Value'];

      const result = generateCSVString(data, { headers: customHeaders });
      const lines = result.split('\n');

      expect(lines[0]).toBe('Product Name,Emission Value');
    });
  });

  // ==========================================================================
  // Test Suite 2: Custom Delimiters
  // ==========================================================================

  describe('Custom Delimiters', () => {
    it('should use comma delimiter by default', () => {
      const data = [{ a: 1, b: 2 }];

      const result = generateCSVString(data);

      expect(result).toContain('a,b');
      expect(result).toContain('1,2');
    });

    it('should support semicolon delimiter for EU locale', () => {
      const data = [
        { name: 'Product', value: 100 },
      ];

      const result = generateCSVString(data, { delimiter: ';' });

      expect(result).toContain('name;value');
      expect(result).toContain('Product;100');
    });

    it('should support tab delimiter', () => {
      const data = [
        { name: 'Product', value: 100 },
      ];

      const result = generateCSVString(data, { delimiter: '\t' });

      expect(result).toContain('name\tvalue');
      expect(result).toContain('Product\t100');
    });
  });

  // ==========================================================================
  // Test Suite 3: Special Character Escaping
  // ==========================================================================

  describe('Special Character Escaping', () => {
    it('should escape values containing commas', () => {
      const data = [
        { name: 'Widget, Large', value: 100 },
      ];

      const result = generateCSVString(data);

      // Value with comma should be quoted
      expect(result).toContain('"Widget, Large"');
    });

    it('should escape values containing double quotes', () => {
      const data = [
        { name: 'Widget "Pro"', value: 100 },
      ];

      const result = generateCSVString(data);

      // Quotes should be doubled and value quoted
      expect(result).toContain('"Widget ""Pro"""');
    });

    it('should escape values containing newlines', () => {
      const data = [
        { name: 'Widget\nMultiline', value: 100 },
      ];

      const result = generateCSVString(data);

      // Value with newline should be quoted
      expect(result).toContain('"Widget\nMultiline"');
    });

    it('should handle values with multiple special characters', () => {
      const data = [
        { description: 'Item "A", has\nnewline' },
      ];

      const result = generateCSVString(data);

      // Should handle all special chars
      expect(result).toContain('"Item ""A"", has\nnewline"');
    });

    it('should escape delimiter in values when using custom delimiter', () => {
      const data = [
        { name: 'Value;with;semicolons' },
      ];

      const result = generateCSVString(data, { delimiter: ';' });

      expect(result).toContain('"Value;with;semicolons"');
    });
  });

  // ==========================================================================
  // Test Suite 4: UTF-8 BOM
  // ==========================================================================

  describe('UTF-8 BOM', () => {
    it('should prepend UTF-8 BOM for Excel compatibility', () => {
      const data = [{ name: 'Test', value: 1 }];

      const result = generateCSVString(data, { includeBOM: true });

      // UTF-8 BOM is \uFEFF (U+FEFF)
      expect(result.charCodeAt(0)).toBe(0xFEFF);
    });

    it('should not include BOM when includeBOM is false', () => {
      const data = [{ name: 'Test', value: 1 }];

      const result = generateCSVString(data, { includeBOM: false });

      expect(result.charCodeAt(0)).not.toBe(0xFEFF);
    });

    it('should include BOM by default for Excel compatibility', () => {
      const data = [{ name: 'Test', value: 1 }];

      // Default behavior should include BOM
      const result = generateCSVString(data);

      expect(result.charCodeAt(0)).toBe(0xFEFF);
    });
  });

  // ==========================================================================
  // Test Suite 5: Date Formatting
  // ==========================================================================

  describe('Date Formatting', () => {
    it('should format dates using ISO format by default', () => {
      const testDate = new Date('2024-06-15T10:30:00Z');
      const data = [{ date: testDate }];

      const result = generateCSVString(data);

      expect(result).toContain('2024-06-15');
    });

    it('should use custom date formatter when provided', () => {
      const testDate = new Date('2024-06-15T10:30:00Z');
      const data = [{ date: testDate }];
      const customDateFormat = (date: Date) => date.toLocaleDateString('en-US');

      const result = generateCSVString(data, { dateFormat: customDateFormat });

      // Should use custom format (e.g., "6/15/2024" for en-US)
      expect(result).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/);
    });

    it('should handle invalid dates gracefully', () => {
      const data = [{ date: new Date('invalid') }];

      const result = generateCSVString(data);

      // Invalid date should show as empty or Invalid Date
      expect(result).toMatch(/date\n(Invalid Date|)/);
    });
  });

  // ==========================================================================
  // Test Suite 6: Number Formatting
  // ==========================================================================

  describe('Number Formatting', () => {
    it('should format numbers with 2 decimal places by default', () => {
      const data = [{ value: 1234.5678 }];

      const result = generateCSVString(data);

      expect(result).toContain('1234.57');
    });

    it('should use custom number formatter when provided', () => {
      const data = [{ value: 1234.5 }];
      const customNumberFormat = (num: number) => num.toLocaleString('de-DE');

      const result = generateCSVString(data, { numberFormat: customNumberFormat });

      // German format uses comma as decimal separator
      expect(result).toContain('1.234,5');
    });

    it('should handle integer values', () => {
      const data = [{ count: 100 }];

      const result = generateCSVString(data);

      expect(result).toContain('100.00');
    });

    it('should handle negative numbers', () => {
      const data = [{ value: -50.5 }];

      const result = generateCSVString(data);

      expect(result).toContain('-50.50');
    });

    it('should handle zero', () => {
      const data = [{ value: 0 }];

      const result = generateCSVString(data);

      expect(result).toContain('0.00');
    });

    it('should handle very large numbers', () => {
      const data = [{ value: 1234567890.123 }];

      const result = generateCSVString(data);

      expect(result).toContain('1234567890.12');
    });

    it('should handle very small numbers', () => {
      const data = [{ value: 0.000123 }];

      const result = generateCSVString(data);

      expect(result).toContain('0.00');
    });
  });

  // ==========================================================================
  // Test Suite 7: Empty and Edge Cases
  // ==========================================================================

  describe('Empty and Edge Cases', () => {
    it('should handle empty array', () => {
      const data: Record<string, unknown>[] = [];

      const result = generateCSVString(data);

      // Should return empty string or just BOM
      expect(result.replace('\uFEFF', '')).toBe('');
    });

    it('should handle array with single empty object', () => {
      const data = [{}];

      const result = generateCSVString(data);

      // Should handle gracefully
      expect(result).toBeDefined();
    });

    it('should handle objects with different keys', () => {
      const data = [
        { a: 1, b: 2 },
        { a: 3, c: 4 }, // different keys
      ];

      // Should use keys from first object
      const result = generateCSVString(data);

      expect(result).toContain('a,b');
      expect(result).toContain('1,2');
      expect(result).toContain('3,'); // b is undefined
    });
  });

  // ==========================================================================
  // Test Suite 8: Null and Undefined Handling
  // ==========================================================================

  describe('Null and Undefined Handling', () => {
    it('should handle null values as empty string', () => {
      const data = [{ name: 'Test', value: null }];

      const result = generateCSVString(data);

      expect(result).toContain('Test,');
    });

    it('should handle undefined values as empty string', () => {
      const data = [{ name: 'Test', value: undefined }];

      const result = generateCSVString(data);

      expect(result).toContain('Test,');
    });

    it('should handle mixed null and undefined in same row', () => {
      const data = [{ a: null, b: undefined, c: 'valid' }];

      const result = generateCSVString(data);

      expect(result).toContain(',,valid');
    });
  });

  // ==========================================================================
  // Test Suite 9: Boolean Handling
  // ==========================================================================

  describe('Boolean Handling', () => {
    it('should convert true to string', () => {
      const data = [{ active: true }];

      const result = generateCSVString(data);

      expect(result).toContain('true');
    });

    it('should convert false to string', () => {
      const data = [{ active: false }];

      const result = generateCSVString(data);

      expect(result).toContain('false');
    });
  });

  // ==========================================================================
  // Test Suite 10: Download Functionality
  // ==========================================================================

  describe('downloadFile', () => {
    it('should create blob URL and trigger download', () => {
      const content = 'test,data\n1,2';
      const filename = 'test.csv';
      const mimeType = 'text/csv;charset=utf-8;';

      downloadFile(content, filename, mimeType);

      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });

    it('should set correct download filename', () => {
      const filename = 'export-2024-06-15.csv';
      const createElement = vi.spyOn(document, 'createElement');

      downloadFile('content', filename, 'text/csv');

      const linkElement = createElement.mock.results[0]?.value;
      expect(linkElement.download).toBe(filename);
    });

    it('should clean up blob URL after download', () => {
      downloadFile('content', 'test.csv', 'text/csv');

      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });
  });

  // ==========================================================================
  // Test Suite 11: exportToCSV Integration
  // ==========================================================================

  describe('exportToCSV', () => {
    it('should generate CSV and trigger download', () => {
      const data = [
        { scope: 'Scope 1', emissions: 100 },
        { scope: 'Scope 2', emissions: 200 },
      ];

      exportToCSV(data, 'emissions-report');

      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockClick).toHaveBeenCalled();
    });

    it('should use .csv extension in filename', () => {
      const data = [{ value: 1 }];
      const createElement = vi.spyOn(document, 'createElement');

      exportToCSV(data, 'report');

      const linkElement = createElement.mock.results[0]?.value;
      expect(linkElement.download).toBe('report.csv');
    });

    it('should not download when data is empty', () => {
      const data: Record<string, unknown>[] = [];
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      exportToCSV(data, 'empty-report');

      expect(mockCreateObjectURL).not.toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalledWith('No data to export');

      consoleSpy.mockRestore();
    });

    it('should pass options to generateCSVString', () => {
      const data = [{ value: 1000.5555 }];
      const options: CSVOptions = {
        delimiter: ';',
        numberFormat: (n) => n.toFixed(4),
      };

      exportToCSV(data, 'report', undefined, options);

      // Verify download was triggered (blob was created)
      expect(mockCreateObjectURL).toHaveBeenCalled();
    });

    it('should use custom headers when provided', () => {
      const data = [{ a: 1, b: 2 }];
      const headers = ['Column A', 'Column B'];

      exportToCSV(data, 'report', headers);

      expect(mockCreateObjectURL).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 12: PCF-Specific Data Export
  // ==========================================================================

  describe('PCF-Specific Data Export', () => {
    it('should export category breakdown data correctly', () => {
      const categoryBreakdown = [
        { scope: 'Scope 1', category: 'Materials', emissions: 1.5, percentage: 60 },
        { scope: 'Scope 2', category: 'Energy', emissions: 0.75, percentage: 30 },
        { scope: 'Scope 3', category: 'Transport', emissions: 0.25, percentage: 10 },
      ];

      const result = generateCSVString(categoryBreakdown);

      expect(result).toContain('scope,category,emissions,percentage');
      expect(result).toContain('Scope 1,Materials,1.50,60.00');
      expect(result).toContain('Scope 2,Energy,0.75,30.00');
      expect(result).toContain('Scope 3,Transport,0.25,10.00');
    });

    it('should export BOM data correctly', () => {
      const bomData = [
        { component: 'Steel', quantity: 100, unit: 'kg', emissionFactor: 2.5, emissions: 250 },
        { component: 'Plastic', quantity: 50, unit: 'kg', emissionFactor: 3.2, emissions: 160 },
      ];

      const result = generateCSVString(bomData);

      expect(result).toContain('component,quantity,unit,emissionFactor,emissions');
      expect(result).toContain('Steel,100.00,kg,2.50,250.00');
      expect(result).toContain('Plastic,50.00,kg,3.20,160.00');
    });

    it('should handle unit values that may contain commas', () => {
      const data = [
        { component: 'Steel, grade A', quantity: 100, unit: 'kg' },
      ];

      const result = generateCSVString(data);

      // Component name with comma should be escaped
      expect(result).toContain('"Steel, grade A"');
    });
  });
});
