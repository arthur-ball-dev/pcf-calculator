/**
 * ExportButton Component Tests
 * TASK-FE-P5-005: Test export button UI and interactions
 *
 * Test Coverage:
 * 1. Renders direct CSV and Excel buttons
 * 2. CSV button triggers exportToCSV
 * 3. Excel button triggers exportToExcel
 * 4. Shows loading spinner during export
 * 5. Disabled when no data
 * 6. Accessibility
 * 7. Error display
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, userEvent } from '../testUtils';
import { ExportButton } from '@/components/ExportButton';
import { useExport } from '@/hooks/useExport';
import type { CalculationStatusResponse } from '@/types/api.types';

// Mock useExport hook
vi.mock('@/hooks/useExport');

describe('ExportButton Component', () => {
  let mockExportToCSV: ReturnType<typeof vi.fn>;
  let mockExportToExcel: ReturnType<typeof vi.fn>;
  let mockClearError: ReturnType<typeof vi.fn>;

  // Sample results data
  const sampleResults: CalculationStatusResponse = {
    calculation_id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    created_at: '2024-06-15T10:30:00Z',
    total_co2e_kg: 2.5,
  };

  const productInfo = {
    name: 'Test Widget',
    code: 'TW-001',
  };

  beforeEach(() => {
    mockExportToCSV = vi.fn().mockResolvedValue(undefined);
    mockExportToExcel = vi.fn().mockResolvedValue(undefined);
    mockClearError = vi.fn();

    (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
      exportToCSV: mockExportToCSV,
      exportToExcel: mockExportToExcel,
      isExporting: false,
      error: null,
      clearError: mockClearError,
    });

    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Rendering
  // ==========================================================================

  describe('Rendering', () => {
    it('should render export buttons container', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-buttons')).toBeInTheDocument();
    });

    it('should render with CSV and Excel button text', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByText(/csv/i)).toBeInTheDocument();
      expect(screen.getByText(/excel/i)).toBeInTheDocument();
    });

    it('should render CSV and Excel as buttons', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      const csvButton = screen.getByTestId('export-csv-button');
      const excelButton = screen.getByTestId('export-excel-button');
      expect(csvButton).toBeInTheDocument();
      expect(csvButton.tagName).toBe('BUTTON');
      expect(excelButton).toBeInTheDocument();
      expect(excelButton.tagName).toBe('BUTTON');
    });

    it('should render direct CSV button', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toBeInTheDocument();
    });

    it('should render direct Excel button', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-excel-button')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 2: CSV Export
  // ==========================================================================

  describe('CSV Export', () => {
    it('should trigger exportToCSV when CSV button clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-csv-button'));

      expect(mockExportToCSV).toHaveBeenCalled();
    });

    it('should trigger exportToCSV when direct CSV button clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-csv-button'));

      expect(mockExportToCSV).toHaveBeenCalled();
    });

    it('should call exportToCSV only once per click', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-csv-button'));

      expect(mockExportToCSV).toHaveBeenCalledTimes(1);
    });
  });

  // ==========================================================================
  // Test Suite 3: Excel Export
  // ==========================================================================

  describe('Excel Export', () => {
    it('should trigger exportToExcel when Excel button clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-excel-button'));

      expect(mockExportToExcel).toHaveBeenCalled();
    });

    it('should trigger exportToExcel when direct Excel button clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-excel-button'));

      expect(mockExportToExcel).toHaveBeenCalled();
    });

    it('should call exportToExcel only once per click', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-excel-button'));

      expect(mockExportToExcel).toHaveBeenCalledTimes(1);
    });
  });

  // ==========================================================================
  // Test Suite 4: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should show loading spinner when exporting', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      // Should have loading indicator (spinner) - check for animate-spin class on SVG
      const csvButton = screen.getByTestId('export-csv-button');
      const spinner = csvButton.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should disable buttons during export', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toBeDisabled();
      expect(screen.getByTestId('export-excel-button')).toBeDisabled();
    });

    it('should disable direct buttons during export', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toBeDisabled();
      expect(screen.getByTestId('export-excel-button')).toBeDisabled();
    });

    it('should show loading state via disabled buttons during export', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      // Both buttons should be disabled during export
      expect(screen.getByTestId('export-csv-button')).toBeDisabled();
      expect(screen.getByTestId('export-excel-button')).toBeDisabled();
    });
  });

  // ==========================================================================
  // Test Suite 5: Disabled State
  // ==========================================================================

  describe('Disabled State', () => {
    it('should disable buttons when disabled prop is true', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
          disabled={true}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toBeDisabled();
      expect(screen.getByTestId('export-excel-button')).toBeDisabled();
    });

    it('should disable buttons when no results', () => {
      render(
        <ExportButton
          results={null as any}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toBeDisabled();
      expect(screen.getByTestId('export-excel-button')).toBeDisabled();
    });

    it('should not call export when disabled', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
          disabled={true}
        />
      );

      // Try to click disabled button
      await user.click(screen.getByTestId('export-csv-button'));

      expect(mockExportToCSV).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 6: Error Display
  // ==========================================================================

  describe('Error Display', () => {
    it('should show error message when export fails', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: false,
        error: 'Export failed: Network error',
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByText(/export failed/i)).toBeInTheDocument();
    });

    it('should show error in alert role', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: false,
        error: 'Export failed',
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('should call clearError when error dismiss button clicked', async () => {
      const user = userEvent.setup();

      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: false,
        error: 'Export failed',
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      const dismissButton = screen.getByRole('button', { name: /dismiss/i });
      await user.click(dismissButton);

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 7: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible names for buttons', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toHaveAccessibleName();
      expect(screen.getByTestId('export-excel-button')).toHaveAccessibleName();
    });

    it('should have accessible names for direct buttons', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toHaveAccessibleName();
      expect(screen.getByTestId('export-excel-button')).toHaveAccessibleName();
    });

    it('should show loading via disabled state during export', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      // Buttons are disabled during export
      expect(screen.getByTestId('export-csv-button')).toBeDisabled();
    });

    it('should be keyboard accessible', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      const csvButton = screen.getByTestId('export-csv-button');

      // Focus button
      csvButton.focus();
      expect(document.activeElement).toBe(csvButton);

      // Activate with Enter key
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockExportToCSV).toHaveBeenCalled();
      });
    });

    it('should have proper focus management', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      const csvButton = screen.getByTestId('export-csv-button');
      const excelButton = screen.getByTestId('export-excel-button');

      // Focus CSV button and verify
      csvButton.focus();
      expect(document.activeElement).toBe(csvButton);

      // Tab to Excel button
      await user.tab();
      expect(document.activeElement).toBe(excelButton);
    });
  });

  // ==========================================================================
  // Test Suite 8: Custom Class Names
  // ==========================================================================

  describe('Custom Class Names', () => {
    it('should apply custom className', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
          className="custom-class"
        />
      );

      expect(screen.getByTestId('export-buttons')).toHaveClass('custom-class');
    });
  });

  // ==========================================================================
  // Test Suite 9: Icon Display
  // ==========================================================================

  describe('Icon Display', () => {
    it('should show download icon on buttons', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      // Check for icon (lucide-react renders SVG)
      const csvButton = screen.getByTestId('export-csv-button');
      expect(csvButton.querySelector('svg')).toBeInTheDocument();
    });

    it('should show loading spinner icon when exporting', () => {
      (useExport as ReturnType<typeof vi.fn>).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      // Should have spinning loader icon
      const csvButton = screen.getByTestId('export-csv-button');
      const svg = csvButton.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveClass('animate-spin');
    });
  });

  // ==========================================================================
  // Test Suite 10: Props Passing
  // ==========================================================================

  describe('Props Passing', () => {
    it('should pass results to useExport hook', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(useExport).toHaveBeenCalledWith(
        sampleResults,
        expect.objectContaining({
          name: productInfo.name,
          code: productInfo.code,
        })
      );
    });

    it('should pass product info to useExport hook', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName="Custom Product"
          productCode="CP-001"
        />
      );

      expect(useExport).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          name: 'Custom Product',
          code: 'CP-001',
        })
      );
    });
  });
});
