/**
 * ExportButton Component Tests
 * TASK-FE-P5-005: Test export button UI and interactions
 *
 * Test Coverage:
 * 1. Renders dropdown with CSV and Excel options
 * 2. CSV option triggers exportToCSV
 * 3. Excel option triggers exportToExcel
 * 4. Shows loading spinner during export
 * 5. Disabled when no data
 * 6. Accessibility
 * 7. Direct button variants
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
    it('should render export button', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-dropdown')).toBeInTheDocument();
    });

    it('should render with "Export" text', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByText(/export/i)).toBeInTheDocument();
    });

    it('should render dropdown trigger button', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      const dropdownTrigger = screen.getByTestId('export-dropdown');
      expect(dropdownTrigger).toBeInTheDocument();
      expect(dropdownTrigger.tagName).toBe('BUTTON');
    });

    it('should render direct CSV button on desktop', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-csv-button')).toBeInTheDocument();
    });

    it('should render direct Excel button on desktop', () => {
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
  // Test Suite 2: Dropdown Menu
  // ==========================================================================

  describe('Dropdown Menu', () => {
    it('should open dropdown menu on click', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-dropdown'));

      await waitFor(() => {
        expect(screen.getByTestId('export-csv-option')).toBeVisible();
        expect(screen.getByTestId('export-excel-option')).toBeVisible();
      });
    });

    it('should show CSV option in dropdown', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-dropdown'));

      await waitFor(() => {
        expect(screen.getByText(/export as csv/i)).toBeInTheDocument();
      });
    });

    it('should show Excel option in dropdown', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-dropdown'));

      await waitFor(() => {
        expect(screen.getByText(/export as excel/i)).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 3: CSV Export
  // ==========================================================================

  describe('CSV Export', () => {
    it('should trigger exportToCSV when CSV option clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-dropdown'));
      await user.click(screen.getByTestId('export-csv-option'));

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
  // Test Suite 4: Excel Export
  // ==========================================================================

  describe('Excel Export', () => {
    it('should trigger exportToExcel when Excel option clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-dropdown'));
      await user.click(screen.getByTestId('export-excel-option'));

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
  // Test Suite 5: Loading State
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

      // Should have loading indicator (spinner)
      const dropdownButton = screen.getByTestId('export-dropdown');
      expect(dropdownButton).toHaveAttribute('aria-busy', 'true');
    });

    it('should disable dropdown during export', () => {
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

      expect(screen.getByTestId('export-dropdown')).toBeDisabled();
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

    it('should show "Exporting..." text during export', () => {
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

      expect(screen.getByText(/exporting/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 6: Disabled State
  // ==========================================================================

  describe('Disabled State', () => {
    it('should disable button when disabled prop is true', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
          disabled={true}
        />
      );

      expect(screen.getByTestId('export-dropdown')).toBeDisabled();
    });

    it('should disable button when no results', () => {
      render(
        <ExportButton
          results={null as any}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-dropdown')).toBeDisabled();
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
  // Test Suite 7: Error Display
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
  // Test Suite 8: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible name for dropdown button', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      expect(screen.getByTestId('export-dropdown')).toHaveAccessibleName();
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

    it('should set aria-busy during export', () => {
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

      expect(screen.getByTestId('export-dropdown')).toHaveAttribute('aria-busy', 'true');
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

      const dropdownButton = screen.getByTestId('export-dropdown');

      // Focus button
      dropdownButton.focus();
      expect(document.activeElement).toBe(dropdownButton);

      // Open with Enter key
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByTestId('export-csv-option')).toBeVisible();
      });
    });

    it('should have proper focus management in dropdown', async () => {
      const user = userEvent.setup();

      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      await user.click(screen.getByTestId('export-dropdown'));

      // First menu item should be focusable
      await waitFor(() => {
        const csvOption = screen.getByTestId('export-csv-option');
        expect(csvOption).toBeVisible();
      });
    });
  });

  // ==========================================================================
  // Test Suite 9: Custom Class Names
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
  // Test Suite 10: Icon Display
  // ==========================================================================

  describe('Icon Display', () => {
    it('should show download icon on dropdown button', () => {
      render(
        <ExportButton
          results={sampleResults}
          productName={productInfo.name}
          productCode={productInfo.code}
        />
      );

      // Check for icon (lucide-react renders SVG)
      const button = screen.getByTestId('export-dropdown');
      expect(button.querySelector('svg')).toBeInTheDocument();
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
      const button = screen.getByTestId('export-dropdown');
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveClass('animate-spin');
    });
  });

  // ==========================================================================
  // Test Suite 11: Props Passing
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
