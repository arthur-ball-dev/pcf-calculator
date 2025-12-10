/**
 * CSV Export Utility
 * TASK-FE-P5-005: CSV generation and export functionality
 *
 * Features:
 * - Converts array of objects to CSV string
 * - UTF-8 BOM for Excel compatibility
 * - Custom delimiters (comma, semicolon, tab)
 * - Date and number formatting
 * - Special character escaping
 */

export interface CSVOptions {
  delimiter?: string;
  includeHeaders?: boolean;
  includeBOM?: boolean;
  headers?: string[];
  dateFormat?: (date: Date) => string;
  numberFormat?: (num: number) => string;
}

const defaultOptions: Required<Omit<CSVOptions, 'headers'>> & { headers?: string[] } = {
  delimiter: ',',
  includeHeaders: true,
  includeBOM: true,
  dateFormat: (date: Date) => {
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    return date.toISOString().split('T')[0];
  },
  numberFormat: (num: number) => num.toFixed(2),
};

/**
 * Generate a CSV string from an array of objects
 */
export function generateCSVString<T extends Record<string, unknown>>(
  data: T[],
  options: CSVOptions = {}
): string {
  const opts = { ...defaultOptions, ...options };

  // Handle empty data
  if (data.length === 0) {
    return opts.includeBOM ? '\uFEFF' : '';
  }

  // UTF-8 BOM for Excel compatibility
  const BOM = opts.includeBOM ? '\uFEFF' : '';

  // Extract headers from first row if not provided
  const cols = opts.headers || Object.keys(data[0]);

  // If no columns (empty object), return just BOM
  if (cols.length === 0) {
    return BOM;
  }

  // Build CSV content
  const lines: string[] = [];

  // Add header row
  if (opts.includeHeaders && !opts.headers) {
    lines.push(cols.join(opts.delimiter));
  } else if (opts.headers) {
    lines.push(opts.headers.join(opts.delimiter));
  }

  // Add data rows
  for (const row of data) {
    const values = cols.map((col) => {
      const key = opts.headers ? Object.keys(data[0])[cols.indexOf(col)] || col : col;
      const value = row[key];

      // Handle null/undefined
      if (value === null || value === undefined) {
        return '';
      }

      // Handle dates
      if (value instanceof Date) {
        return opts.dateFormat(value);
      }

      // Handle numbers
      if (typeof value === 'number') {
        return opts.numberFormat(value);
      }

      // Handle booleans
      if (typeof value === 'boolean') {
        return String(value);
      }

      // Handle strings - escape quotes, delimiters, and newlines
      const stringValue = String(value);
      if (
        stringValue.includes(opts.delimiter!) ||
        stringValue.includes('"') ||
        stringValue.includes('\n')
      ) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }

      return stringValue;
    });

    lines.push(values.join(opts.delimiter));
  }

  return BOM + lines.join('\n');
}

/**
 * Download a file with the given content
 */
export function downloadFile(
  content: string | Blob,
  filename: string,
  mimeType: string
): void {
  const blob =
    content instanceof Blob ? content : new Blob([content], { type: mimeType });

  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.visibility = 'hidden';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up
  URL.revokeObjectURL(url);
}

/**
 * Export data as CSV file
 */
export function exportToCSV<T extends Record<string, unknown>>(
  data: T[],
  filename: string,
  headers?: string[],
  options: CSVOptions = {}
): void {
  if (data.length === 0) {
    console.warn('No data to export');
    return;
  }

  const opts = { ...options };
  if (headers) {
    opts.headers = headers;
  }

  const csvContent = generateCSVString(data, opts);

  downloadFile(csvContent, `${filename}.csv`, 'text/csv;charset=utf-8;');
}
