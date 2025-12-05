/**
 * useExport Hook Tests
 * TASK-FE-P5-005: Test export hook functionality
 *
 * Test Coverage:
 * 1. exportToCSV() triggers download
 * 2. exportToExcel() triggers download
 * 3. Returns loading state during export
 * 4. Handles export errors
 * 5. Correct file names generated
 * 6. Transforms calculation results to export data
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useExport } from '@/hooks/useExport';
import type { CalculationStatusResponse } from '@/types/api.types';

// Mock export utilities
vi.mock('@/utils/export/csvExport', () => ({
  exportToCSV: vi.fn(),
  generateCSVString: vi.fn(() => 'csv,data'),
}));

vi.mock('@/utils/export/excelExport', () => ({
  exportToExcel: vi.fn(),
}));

import { exportToCSV } from '@/utils/export/csvExport';
import { exportToExcel } from '@/utils/export/excelExport';

describe('useExport Hook', () => {
  // Sample calculation results
  const sampleResults: CalculationStatusResponse & {
    category_breakdown?: Array<{
      scope: string;
      category: string;
      emissions: number;
      percentage: number;
    }>;
    bom_details?: Array<{
      component_name: string;
      quantity: number;
      unit: string;
      emission_factor: number;
      emissions: number;
    }>;
    parameters?: {
      transport_distance?: number;
      energy_source?: string;
      production_volume?: number;
    };
  } = {
    calculation_id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    created_at: '2024-06-15T10:30:00Z',
    total_co2e_kg: 2.5,
    materials_co2e: 1.5,
    energy_co2e: 0.75,
    transport_co2e: 0.25,
    calculation_time_ms: 150,
    category_breakdown: [
      { scope: 'Scope 1', category: 'Materials', emissions: 1.5, percentage: 60 },
      { scope: 'Scope 2', category: 'Energy', emissions: 0.75, percentage: 30 },
      { scope: 'Scope 3', category: 'Transport', emissions: 0.25, percentage: 10 },
    ],
    bom_details: [
      { component_name: 'Steel', quantity: 100, unit: 'kg', emission_factor: 2.5, emissions: 250 },
      { component_name: 'Plastic', quantity: 50, unit: 'kg', emission_factor: 3.2, emissions: 160 },
    ],
    parameters: {
      transport_distance: 500,
      energy_source: 'Grid Electricity',
      production_volume: 1000,
    },
  };

  const productInfo = {
    name: 'Test Widget',
    code: 'TW-001',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ==========================================================================
  // Test Suite 1: Initial State
  // ==========================================================================

  describe('Initial State', () => {
    it('should return isExporting as false initially', () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      expect(result.current.isExporting).toBe(false);
    });

    it('should return error as null initially', () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      expect(result.current.error).toBeNull();
    });

    it('should provide exportToCSV function', () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      expect(typeof result.current.exportToCSV).toBe('function');
    });

    it('should provide exportToExcel function', () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      expect(typeof result.current.exportToExcel).toBe('function');
    });
  });

  // ==========================================================================
  // Test Suite 2: CSV Export
  // ==========================================================================

  describe('exportToCSV', () => {
    it('should call CSV export utility when triggered', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalled();
    });

    it('should pass category breakdown data to CSV export', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ Scope: 'Scope 1' }),
        ]),
        expect.any(String)
      );
    });

    it('should generate filename with product name', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining('Test_Widget')
      );
    });

    it('should include PCF in filename', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining('PCF')
      );
    });

    it('should include date in filename', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      // Set a specific date
      vi.setSystemTime(new Date('2024-06-15'));

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringMatching(/2024-06-15/)
      );
    });

    it('should sanitize special characters in product name for filename', async () => {
      const productWithSpecialChars = {
        name: 'Widget/Pro*Special',
        code: 'WPS-001',
      };
      const { result } = renderHook(() => useExport(sampleResults, productWithSpecialChars));

      await act(async () => {
        await result.current.exportToCSV();
      });

      // Filename should not contain special characters
      const filename = (exportToCSV as ReturnType<typeof vi.fn>).mock.calls[0][1];
      expect(filename).not.toMatch(/[\/\*]/);
    });
  });

  // ==========================================================================
  // Test Suite 3: Excel Export
  // ==========================================================================

  describe('exportToExcel', () => {
    it('should call Excel export utility when triggered', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalled();
    });

    it('should pass complete export data to Excel utility', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalledWith(
        expect.objectContaining({
          productName: 'Test Widget',
          productCode: 'TW-001',
          totalEmissions: 2.5,
        }),
        expect.any(String)
      );
    });

    it('should transform BOM details correctly', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToExcel();
      });

      const exportData = (exportToExcel as ReturnType<typeof vi.fn>).mock.calls[0][0];
      expect(exportData.bomEntries).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            component: 'Steel',
            quantity: 100,
          }),
        ])
      );
    });

    it('should include parameters in export data', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToExcel();
      });

      const exportData = (exportToExcel as ReturnType<typeof vi.fn>).mock.calls[0][0];
      expect(exportData.parameters).toEqual(
        expect.objectContaining({
          transportDistance: 500,
          energySource: 'Grid Electricity',
        })
      );
    });

    it('should generate filename with same pattern as CSV', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      vi.setSystemTime(new Date('2024-06-15'));

      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining('Test_Widget')
      );
    });
  });

  // ==========================================================================
  // Test Suite 4: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should set isExporting to true during CSV export', async () => {
      // Make export take some time
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        return new Promise(resolve => setTimeout(resolve, 100));
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      let exportPromise: Promise<void>;
      act(() => {
        exportPromise = result.current.exportToCSV();
      });

      // Should be exporting immediately
      expect(result.current.isExporting).toBe(true);

      // Complete the export
      await act(async () => {
        vi.advanceTimersByTime(100);
        await exportPromise!;
      });

      expect(result.current.isExporting).toBe(false);
    });

    it('should set isExporting to true during Excel export', async () => {
      (exportToExcel as ReturnType<typeof vi.fn>).mockImplementation(() => {
        return new Promise(resolve => setTimeout(resolve, 100));
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      let exportPromise: Promise<void>;
      act(() => {
        exportPromise = result.current.exportToExcel();
      });

      expect(result.current.isExporting).toBe(true);

      await act(async () => {
        vi.advanceTimersByTime(100);
        await exportPromise!;
      });

      expect(result.current.isExporting).toBe(false);
    });

    it('should reset isExporting to false after successful export', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(result.current.isExporting).toBe(false);
    });

    it('should reset isExporting to false after failed export', async () => {
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Export failed');
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        try {
          await result.current.exportToCSV();
        } catch {
          // Expected to throw
        }
      });

      expect(result.current.isExporting).toBe(false);
    });
  });

  // ==========================================================================
  // Test Suite 5: Error Handling
  // ==========================================================================

  describe('Error Handling', () => {
    it('should set error state when CSV export fails', async () => {
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('CSV export failed');
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        try {
          await result.current.exportToCSV();
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('CSV export failed');
    });

    it('should set error state when Excel export fails', async () => {
      (exportToExcel as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Excel export failed');
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        try {
          await result.current.exportToExcel();
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Excel export failed');
    });

    it('should clear error on successful export', async () => {
      // First call fails
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementationOnce(() => {
        throw new Error('Failed');
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      // First export fails
      await act(async () => {
        try {
          await result.current.exportToCSV();
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Failed');

      // Second export succeeds
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {});

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(result.current.error).toBeNull();
    });

    it('should provide clearError function', () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      expect(typeof result.current.clearError).toBe('function');
    });

    it('should clear error when clearError is called', async () => {
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Failed');
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        try {
          await result.current.exportToCSV();
        } catch {
          // Expected
        }
      });

      expect(result.current.error).toBe('Failed');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  // ==========================================================================
  // Test Suite 6: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle null results gracefully', () => {
      const { result } = renderHook(() => useExport(null as any, productInfo));

      expect(result.current.isExporting).toBe(false);
    });

    it('should handle missing category_breakdown', async () => {
      const resultsWithoutBreakdown = {
        ...sampleResults,
        category_breakdown: undefined,
      };

      const { result } = renderHook(() => useExport(resultsWithoutBreakdown, productInfo));

      // Should not throw
      await act(async () => {
        await result.current.exportToCSV();
      });
    });

    it('should handle missing bom_details', async () => {
      const resultsWithoutBOM = {
        ...sampleResults,
        bom_details: undefined,
      };

      const { result } = renderHook(() => useExport(resultsWithoutBOM, productInfo));

      await act(async () => {
        await result.current.exportToExcel();
      });

      const exportData = (exportToExcel as ReturnType<typeof vi.fn>).mock.calls[0][0];
      expect(exportData.bomEntries).toEqual([]);
    });

    it('should handle missing parameters', async () => {
      const resultsWithoutParams = {
        ...sampleResults,
        parameters: undefined,
      };

      const { result } = renderHook(() => useExport(resultsWithoutParams, productInfo));

      await act(async () => {
        await result.current.exportToExcel();
      });

      const exportData = (exportToExcel as ReturnType<typeof vi.fn>).mock.calls[0][0];
      expect(exportData.parameters).toEqual({});
    });

    it('should handle empty product name', async () => {
      const emptyProductInfo = { name: '', code: 'CODE-001' };
      const { result } = renderHook(() => useExport(sampleResults, emptyProductInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      // Should use fallback or code
      const filename = (exportToCSV as ReturnType<typeof vi.fn>).mock.calls[0][1];
      expect(filename).toBeTruthy();
    });
  });

  // ==========================================================================
  // Test Suite 7: Custom Export Options
  // ==========================================================================

  describe('Custom Export Options', () => {
    it('should accept custom CSV options', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV({ delimiter: ';' });
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        expect.anything(),
        undefined,
        expect.objectContaining({ delimiter: ';' })
      );
    });

    it('should accept custom filename', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV({ filename: 'custom-report' });
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        'custom-report'
      );
    });

    it('should accept custom headers for CSV', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));
      const customHeaders = ['Custom Scope', 'Custom Category', 'Custom Emissions'];

      await act(async () => {
        await result.current.exportToCSV({ headers: customHeaders });
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        expect.anything(),
        customHeaders,
        expect.anything()
      );
    });
  });

  // ==========================================================================
  // Test Suite 8: Concurrent Export Prevention
  // ==========================================================================

  describe('Concurrent Export Prevention', () => {
    it('should prevent concurrent exports', async () => {
      (exportToCSV as ReturnType<typeof vi.fn>).mockImplementation(() => {
        return new Promise(resolve => setTimeout(resolve, 100));
      });

      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      // Start first export
      act(() => {
        result.current.exportToCSV();
      });

      // Try to start second export while first is running
      act(() => {
        result.current.exportToCSV();
      });

      // Should only call export once
      expect(exportToCSV).toHaveBeenCalledTimes(1);

      // Cleanup
      await act(async () => {
        vi.advanceTimersByTime(100);
      });
    });

    it('should allow export after previous completes', async () => {
      const { result } = renderHook(() => useExport(sampleResults, productInfo));

      await act(async () => {
        await result.current.exportToCSV();
      });

      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalledTimes(2);
    });
  });
});
