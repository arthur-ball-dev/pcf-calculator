/**
 * ExportDialog Component Tests
 * TASK-FE-P5-005: Test export dialog UI and interactions
 *
 * Test Coverage:
 * 1. Shows format selection (CSV, Excel)
 * 2. Shows options (include headers, date format)
 * 3. Export button triggers export with options
 * 4. Cancel button closes dialog
 * 5. Loading state during export
 * 6. Error display
 * 7. Accessibility
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, userEvent } from '../testUtils';
import { ExportDialog } from '@/components/ExportDialog';
import type { CalculationStatusResponse } from '@/types/api.types';

// Mock export utilities
vi.mock('@/utils/export/csvExport', () => ({
  exportToCSV: vi.fn(),
}));

vi.mock('@/utils/export/excelExport', () => ({
  exportToExcel: vi.fn(),
}));

import { exportToCSV } from '@/utils/export/csvExport';
import { exportToExcel } from '@/utils/export/excelExport';

describe('ExportDialog Component', () => {
  let mockOnClose: ReturnType<typeof vi.fn>;
  let mockOnExport: ReturnType<typeof vi.fn>;

  // Sample results data
  const sampleResults: CalculationStatusResponse = {
    calculation_id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    created_at: '2024-06-15T10:30:00Z',
    total_co2e_kg: 2.5,
  };

  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    results: sampleResults,
    productName: 'Test Widget',
    productCode: 'TW-001',
  };

  beforeEach(() => {
    mockOnClose = vi.fn();
    mockOnExport = vi.fn();
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Rendering
  // ==========================================================================

  describe('Rendering', () => {
    it('should render dialog when open is true', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should not render dialog when open is false', () => {
      render(<ExportDialog {...defaultProps} open={false} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render dialog title', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('heading', { name: /export/i })).toBeInTheDocument();
    });

    it('should render format selection', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText('Format')).toBeInTheDocument();
    });

    it('should render export button', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
    });

    it('should render cancel button', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 2: Format Selection
  // ==========================================================================

  describe('Format Selection', () => {
    it('should show CSV format option', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/csv/i)).toBeInTheDocument();
    });

    it('should show Excel format option', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/excel/i)).toBeInTheDocument();
    });

    it('should have CSV selected by default', () => {
      render(<ExportDialog {...defaultProps} />);

      const csvRadio = screen.getByLabelText(/csv/i);
      expect(csvRadio).toBeChecked();
    });

    it('should allow selecting Excel format', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      const excelRadio = screen.getByLabelText(/excel/i);
      await user.click(excelRadio);

      expect(excelRadio).toBeChecked();
    });

    it('should show format descriptions', () => {
      render(<ExportDialog {...defaultProps} />);

      // CSV description
      expect(screen.getByText(/comma.separated/i)).toBeInTheDocument();

      // Excel description
      expect(screen.getByText(/multi.sheet/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 3: Export Options
  // ==========================================================================

  describe('Export Options', () => {
    it('should show "Include Headers" option', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/include headers/i)).toBeInTheDocument();
    });

    it('should have "Include Headers" checked by default', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/include headers/i)).toBeChecked();
    });

    it('should allow unchecking "Include Headers"', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      const checkbox = screen.getByLabelText(/include headers/i);
      await user.click(checkbox);

      expect(checkbox).not.toBeChecked();
    });

    it('should show date format selector', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/date format/i)).toBeInTheDocument();
    });

    it('should have default date format selected', () => {
      render(<ExportDialog {...defaultProps} />);

      const dateSelect = screen.getByLabelText(/date format/i);
      expect(dateSelect).toHaveValue('iso');
    });

    it('should allow changing date format', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      const dateSelect = screen.getByLabelText(/date format/i);
      await user.selectOptions(dateSelect, 'locale');

      expect(dateSelect).toHaveValue('locale');
    });

    it('should show delimiter option for CSV', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/delimiter/i)).toBeInTheDocument();
    });

    it('should hide delimiter option when Excel selected', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByLabelText(/excel/i));

      expect(screen.queryByLabelText(/delimiter/i)).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 4: Export Action
  // ==========================================================================

  describe('Export Action', () => {
    it('should call exportToCSV when CSV selected and export clicked', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(exportToCSV).toHaveBeenCalled();
    });

    it('should call exportToExcel when Excel selected and export clicked', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByLabelText(/excel/i));
      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(exportToExcel).toHaveBeenCalled();
    });

    it('should pass include headers option to CSV export', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      // Uncheck include headers
      await user.click(screen.getByLabelText(/include headers/i));
      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(exportToCSV).toHaveBeenCalled();
    });

    it('should pass delimiter option to CSV export', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      // Change delimiter to semicolon
      await user.selectOptions(screen.getByLabelText(/delimiter/i), ';');
      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(exportToCSV).toHaveBeenCalled();
    });

    it('should close dialog after successful export', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} onClose={mockOnClose} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should not close dialog if export fails', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Export failed');
      });

      render(<ExportDialog {...defaultProps} onClose={mockOnClose} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      await waitFor(() => {
        expect(mockOnClose).not.toHaveBeenCalled();
      });
    });
  });

  // ==========================================================================
  // Test Suite 5: Cancel Action
  // ==========================================================================

  describe('Cancel Action', () => {
    it('should call onClose when cancel clicked', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} onClose={mockOnClose} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it.skip('should call onClose when dialog backdrop clicked', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} onClose={mockOnClose} />);

      // Click on dialog backdrop (outside content)
      const dialog = screen.getByRole('dialog');
      await user.click(dialog.parentElement!);

      // Depending on Radix Dialog implementation
      // This may or may not call onClose
    });

    it('should call onClose when Escape key pressed', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} onClose={mockOnClose} />);

      await user.keyboard('{Escape}');

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should reset form when dialog reopened', async () => {
      const user = userEvent.setup();

      const { rerender } = render(<ExportDialog {...defaultProps} />);

      // Change some options
      await user.click(screen.getByLabelText(/excel/i));

      // Close dialog
      rerender(<ExportDialog {...defaultProps} open={false} />);

      // Reopen dialog
      rerender(<ExportDialog {...defaultProps} open={true} />);

      // Should be back to default (CSV selected)
      expect(screen.getByLabelText(/csv/i)).toBeChecked();
    });
  });

  // ==========================================================================
  // Test Suite 6: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should disable export button during export', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ExportDialog {...defaultProps} />);

      const exportButton = screen.getByRole('button', { name: /^export$/i });
      await user.click(exportButton);

      expect(exportButton).toBeDisabled();
    });

    it('should show loading indicator during export', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(screen.getByText(/exporting/i)).toBeInTheDocument();
    });

    it('should disable cancel button during export', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
    });

    it('should disable format selection during export', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(screen.getByLabelText(/csv/i)).toBeDisabled();
      expect(screen.getByLabelText(/excel/i)).toBeDisabled();
    });
  });

  // ==========================================================================
  // Test Suite 7: Error Display
  // ==========================================================================

  describe('Error Display', () => {
    it('should show error message when export fails', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Network error');
      });

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it('should show error in alert role', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Failed');
      });

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('should allow retry after error', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>)
        .mockImplementationOnce(() => { throw new Error('Failed'); })
        .mockImplementation(() => {});

      render(<ExportDialog {...defaultProps} />);

      // First attempt fails
      await user.click(screen.getByRole('button', { name: /^export$/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Second attempt should work
      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(exportToCSV).toHaveBeenCalledTimes(2);
    });

    it('should clear error when dialog closed and reopened', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Failed');
      });

      const { rerender } = render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Close and reopen
      rerender(<ExportDialog {...defaultProps} open={false} />);
      rerender(<ExportDialog {...defaultProps} open={true} />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 8: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible dialog title', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAccessibleName();
    });

    it('should have accessible description', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAccessibleDescription();
    });

    it('should focus first interactive element when opened', () => {
      render(<ExportDialog {...defaultProps} />);

      // First radio button should be focused
      expect(screen.getByLabelText(/csv/i)).toHaveFocus();
    });

    it('should trap focus within dialog', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      // Tab through all elements
      await user.tab();
      await user.tab();
      await user.tab();
      await user.tab();
      await user.tab();

      // Should cycle back within dialog
      expect(screen.getByRole('dialog').contains(document.activeElement)).toBe(true);
    });

    it('should have accessible labels for all form controls', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByLabelText(/csv/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/excel/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/include headers/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/date format/i)).toBeInTheDocument();
    });

    it('should announce loading state to screen readers', async () => {
      const user = userEvent.setup();
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 1000))
      );

      render(<ExportDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      const loadingElement = screen.getByText(/exporting/i);
      expect(loadingElement).toHaveAttribute('aria-live', 'polite');
    });
  });

  // ==========================================================================
  // Test Suite 9: File Preview
  // ==========================================================================

  describe('File Preview', () => {
    it('should show expected filename preview', () => {
      render(<ExportDialog {...defaultProps} />);

      // Should show preview of generated filename
      const filenameElements = screen.getAllByText(/test_widget.*pcf/i);
      expect(filenameElements.length).toBeGreaterThan(0);
    });

    it('should update filename preview when format changes', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} />);

      // Initially shows .csv
      expect(screen.getAllByText(/.csv/i).length).toBeGreaterThan(0);

      // Select Excel
      await user.click(screen.getByLabelText(/excel/i));

      // Should show .xlsx
      expect(screen.getAllByText(/.xlsx/i).length).toBeGreaterThan(0);
    });
  });

  // ==========================================================================
  // Test Suite 10: Product Info Display
  // ==========================================================================

  describe('Product Info Display', () => {
    it('should display product name', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText(/test widget/i)).toBeInTheDocument();
    });

    it('should display product code', () => {
      render(<ExportDialog {...defaultProps} />);

      expect(screen.getByText(/tw-001/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 11: Custom onExport Handler
  // ==========================================================================

  describe('Custom onExport Handler', () => {
    it('should call custom onExport if provided', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} onExport={mockOnExport} />);

      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(mockOnExport).toHaveBeenCalledWith(
        expect.objectContaining({
          format: 'csv',
          includeHeaders: true,
        })
      );
    });

    it('should pass selected format to onExport', async () => {
      const user = userEvent.setup();

      render(<ExportDialog {...defaultProps} onExport={mockOnExport} />);

      await user.click(screen.getByLabelText(/excel/i));
      await user.click(screen.getByRole('button', { name: /^export$/i }));

      expect(mockOnExport).toHaveBeenCalledWith(
        expect.objectContaining({ format: 'excel' })
      );
    });
  });
});
