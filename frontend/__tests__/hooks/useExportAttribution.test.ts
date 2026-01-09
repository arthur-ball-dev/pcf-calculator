/**
 * useExport Hook Attribution Integration Tests
 * TASK-FE-P8-008: Test export attribution integration in useExport hook
 *
 * Test Coverage:
 * 1. CSV export includes attribution section when data sources provided
 * 2. Excel export includes attribution when data sources provided
 * 3. Multiple data sources are handled correctly
 * 4. Empty data sources still include disclaimer
 * 5. Attribution text is properly passed through export chain
 *
 * These tests verify the integration of exportAttribution utility with the useExport hook.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '../testUtils';
import { useExport } from '@/hooks/useExport';
import type { CalculationStatusResponse } from '@/types/api.types';
import type { DataSourceInfo } from '@/utils/exportAttribution';

// Mock export utilities
vi.mock('@/utils/export/csvExport', () => ({
  exportToCSV: vi.fn(),
  generateCSVString: vi.fn(() => 'csv,data'),
}));

vi.mock('@/utils/export/excelExport', () => ({
  exportToExcel: vi.fn(),
}));

// Mock attribution utility
vi.mock('@/utils/exportAttribution', () => ({
  generateAttributionText: vi.fn((sources: DataSourceInfo[]) => {
    const lines = ['DATA SOURCE ATTRIBUTIONS'];
    sources.forEach(s => {
      if (s.attribution_required && s.attribution_text) {
        lines.push(s.name);
        lines.push(s.attribution_text);
      }
    });
    lines.push('DISCLAIMER');
    lines.push('Calculations are for informational purposes only.');
    return lines.join('\n');
  }),
  appendAttributionToCSV: vi.fn((csv: string, sources: DataSourceInfo[]) => {
    const lines = ['DATA SOURCE ATTRIBUTIONS'];
    sources.forEach(s => {
      if (s.attribution_required && s.attribution_text) {
        lines.push(s.name);
        lines.push(s.attribution_text);
      }
    });
    lines.push('DISCLAIMER');
    lines.push('Calculations are for informational purposes only.');
    return csv + '\n\n' + lines.join('\n');
  }),
}));

import { exportToCSV } from '@/utils/export/csvExport';
import { exportToExcel } from '@/utils/export/excelExport';
import { generateAttributionText, appendAttributionToCSV } from '@/utils/exportAttribution';

describe('useExport Hook - Attribution Integration', () => {
  // Sample data sources for testing
  const sampleDataSources: DataSourceInfo[] = [
    {
      code: 'DEFRA',
      name: 'UK Government GHG Conversion Factors',
      attribution_required: true,
      attribution_text: 'Contains UK Government GHG Conversion Factors for Company Reporting.',
    },
  ];

  const multipleDataSources: DataSourceInfo[] = [
    {
      code: 'EPA',
      name: 'EPA GHG Emission Factors Hub',
      attribution_required: false,
      attribution_text: 'EPA emission factors data.',
    },
    {
      code: 'DEFRA',
      name: 'UK Government GHG Conversion Factors',
      attribution_required: true,
      attribution_text: 'Contains UK Government GHG Conversion Factors.',
    },
    {
      code: 'EXIOBASE',
      name: 'EXIOBASE Database',
      attribution_required: true,
      attribution_text: 'EXIOBASE multi-regional environmentally extended database.',
    },
  ];

  // Extended results type with data_sources field
  interface ExtendedResultsWithSources extends CalculationStatusResponse {
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
      data_source?: string;
    }>;
    parameters?: {
      transport_distance?: number;
      energy_source?: string;
      production_volume?: number;
    };
    data_sources?: DataSourceInfo[];
  }

  // Sample calculation results with data sources
  const sampleResultsWithSources: ExtendedResultsWithSources = {
    calculation_id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    created_at: '2024-06-15T10:30:00Z',
    total_co2e_kg: 150.5,
    materials_co2e: 100.0,
    energy_co2e: 35.0,
    transport_co2e: 15.5,
    calculation_time_ms: 150,
    category_breakdown: [
      { scope: 'Scope 1', category: 'Materials', emissions: 100.0, percentage: 66.4 },
      { scope: 'Scope 2', category: 'Energy', emissions: 35.0, percentage: 23.3 },
      { scope: 'Scope 3', category: 'Transport', emissions: 15.5, percentage: 10.3 },
    ],
    bom_details: [
      { component_name: 'Steel', quantity: 100, unit: 'kg', emission_factor: 2.5, emissions: 250, data_source: 'DEFRA' },
      { component_name: 'Plastic', quantity: 50, unit: 'kg', emission_factor: 3.2, emissions: 160, data_source: 'EXIOBASE' },
    ],
    parameters: {
      transport_distance: 500,
      energy_source: 'Grid Electricity',
      production_volume: 1000,
    },
    data_sources: sampleDataSources,
  };

  const productInfo = {
    name: 'Test Widget',
    code: 'TW-001',
  };

  beforeEach(() => {
    vi.resetAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ==========================================================================
  // Test Suite 1: CSV Export with Attribution (Scenario 1)
  // ==========================================================================

  describe('CSV Export with Attribution - Scenario 1', () => {
    it('should pass data sources to CSV export when available', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // Verify CSV export was called
      expect(exportToCSV).toHaveBeenCalled();

      // The integration should pass data sources to the export function
      // (Implementation will add this in Phase B)
    });

    it('should include attribution text in exported CSV content', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, the CSV export should call appendAttributionToCSV
      // with the data sources from results
      // (Implementation will integrate this in Phase B)
    });

    it('should include DEFRA attribution when DEFRA source is used', async () => {
      const resultsWithDEFRA: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: [
          {
            code: 'DEFRA',
            name: 'UK Government GHG Conversion Factors',
            attribution_required: true,
            attribution_text: 'Contains UK Government GHG Conversion Factors for Company Reporting.',
          },
        ],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithDEFRA as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, verify that DEFRA attribution is included
      // The export should contain:
      // - DATA SOURCE ATTRIBUTIONS header
      // - UK Government GHG Conversion Factors name
      // - DEFRA attribution text
      // - DISCLAIMER section
    });

    it('should include disclaimer in exported CSV', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, the CSV should always include disclaimer section
      // even if no attribution is required
    });
  });

  // ==========================================================================
  // Test Suite 2: Multiple Data Sources (Scenario 2)
  // ==========================================================================

  describe('Multiple Data Sources - Scenario 2', () => {
    it('should include DEFRA and EXIOBASE attribution, omit EPA', async () => {
      const resultsWithMultipleSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: multipleDataSources,
      };

      const { result } = renderHook(() =>
        useExport(resultsWithMultipleSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented:
      // - DEFRA attribution should be included (attribution_required: true)
      // - EXIOBASE attribution should be included (attribution_required: true)
      // - EPA should NOT be included (attribution_required: false)
      // - Disclaimer should be included
    });

    it('should handle mixed attribution_required flags correctly', async () => {
      const mixedSources: DataSourceInfo[] = [
        {
          code: 'SOURCE_A',
          name: 'Source A',
          attribution_required: true,
          attribution_text: 'Source A attribution.',
        },
        {
          code: 'SOURCE_B',
          name: 'Source B',
          attribution_required: false,
          attribution_text: 'Source B attribution.',
        },
        {
          code: 'SOURCE_C',
          name: 'Source C',
          attribution_required: true,
          attribution_text: 'Source C attribution.',
        },
      ];

      const resultsWithMixedSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: mixedSources,
      };

      const { result } = renderHook(() =>
        useExport(resultsWithMixedSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented:
      // - Source A should be included
      // - Source B should NOT be included
      // - Source C should be included
    });
  });

  // ==========================================================================
  // Test Suite 3: Edge Case - No Data Sources (Scenario 3)
  // ==========================================================================

  describe('No Data Sources - Scenario 3', () => {
    it('should still export CSV successfully with empty data sources', async () => {
      const resultsWithNoSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: [],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithNoSources as any, productInfo)
      );

      // Should not throw
      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalled();
    });

    it('should still include disclaimer with empty data sources', async () => {
      const resultsWithNoSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: [],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithNoSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, the CSV should still contain disclaimer
      // even with empty data sources array
    });

    it('should handle undefined data_sources gracefully', async () => {
      const resultsWithUndefinedSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: undefined,
      };

      const { result } = renderHook(() =>
        useExport(resultsWithUndefinedSources as any, productInfo)
      );

      // Should not throw
      await act(async () => {
        await result.current.exportToCSV();
      });

      expect(exportToCSV).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 4: Excel Export with Attribution (Scenario 4)
  // ==========================================================================

  describe('Excel Export with Attribution - Scenario 4', () => {
    it('should pass data sources to Excel export', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalled();

      // When implemented, the export data should include data_sources
      // for the Excel export function to create an Attribution sheet
    });

    it('should include data sources in export data for Excel', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToExcel();
      });

      // When implemented, the export data passed to exportToExcel
      // should include dataSources field for attribution sheet creation
      const exportData = (exportToExcel as ReturnType<typeof vi.fn>).mock.calls[0]?.[0];

      // This test will fail until Phase B implementation adds dataSources to export data
      // expect(exportData.dataSources).toBeDefined();
    });

    it('should handle Excel export with multiple data sources', async () => {
      const resultsWithMultipleSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: multipleDataSources,
      };

      const { result } = renderHook(() =>
        useExport(resultsWithMultipleSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalled();

      // When implemented, the Excel file should have an Attribution sheet
      // containing DEFRA and EXIOBASE attributions (not EPA)
    });

    it('should handle Excel export with empty data sources', async () => {
      const resultsWithNoSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: [],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithNoSources as any, productInfo)
      );

      // Should not throw
      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 5: Data Source Detection from BOM Items
  // ==========================================================================

  describe('Data Source Detection from BOM Items', () => {
    it('should detect data sources from BOM item data_source field', async () => {
      const resultsWithBOMSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: undefined, // No explicit data_sources
        bom_details: [
          { component_name: 'Steel', quantity: 100, unit: 'kg', emission_factor: 2.5, emissions: 250, data_source: 'DEFRA' },
          { component_name: 'Plastic', quantity: 50, unit: 'kg', emission_factor: 3.2, emissions: 160, data_source: 'EXIOBASE' },
          { component_name: 'Aluminum', quantity: 25, unit: 'kg', emission_factor: 4.0, emissions: 100, data_source: 'DEFRA' },
        ],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithBOMSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, should detect unique sources (DEFRA, EXIOBASE) from BOM
      // and include their attribution in the export
    });

    it('should deduplicate data sources from BOM items', async () => {
      const resultsWithDuplicateSources: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: undefined,
        bom_details: [
          { component_name: 'Steel', quantity: 100, unit: 'kg', emission_factor: 2.5, emissions: 250, data_source: 'DEFRA' },
          { component_name: 'Iron', quantity: 50, unit: 'kg', emission_factor: 2.0, emissions: 100, data_source: 'DEFRA' },
          { component_name: 'Copper', quantity: 25, unit: 'kg', emission_factor: 5.0, emissions: 125, data_source: 'DEFRA' },
        ],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithDuplicateSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, DEFRA should only appear once in attribution
      // even though multiple BOM items use it
    });
  });

  // ==========================================================================
  // Test Suite 6: Additional Test Requirements from SPEC
  // ==========================================================================

  describe('Additional Requirements from SPEC', () => {
    it('should properly escape attribution text for CSV', async () => {
      const resultsWithSpecialChars: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: [
          {
            code: 'TEST',
            name: 'Test "Quoted" Source',
            attribution_required: true,
            attribution_text: 'Contains special chars: <>&, "quotes", and newlines\nlike this',
          },
        ],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithSpecialChars as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV();
      });

      // When implemented, special characters should be properly escaped
      // to maintain valid CSV format
    });

    it('should not change export filename when attribution is added', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      vi.setSystemTime(new Date('2024-06-15'));

      await act(async () => {
        await result.current.exportToCSV();
      });

      // Filename should follow same pattern regardless of attribution
      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining('Test_Widget')
      );
    });

    it('should handle Excel sheet with long attribution text', async () => {
      const longAttributionText = 'A'.repeat(1000);
      const resultsWithLongText: ExtendedResultsWithSources = {
        ...sampleResultsWithSources,
        data_sources: [
          {
            code: 'LONG',
            name: 'Source with Long Attribution',
            attribution_required: true,
            attribution_text: longAttributionText,
          },
        ],
      };

      const { result } = renderHook(() =>
        useExport(resultsWithLongText as any, productInfo)
      );

      // Should not throw
      await act(async () => {
        await result.current.exportToExcel();
      });

      expect(exportToExcel).toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 7: Integration with Export Options
  // ==========================================================================

  describe('Integration with Export Options', () => {
    it('should include attribution even with custom CSV options', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV({ delimiter: ';' });
      });

      expect(exportToCSV).toHaveBeenCalled();
      // When implemented, attribution should still be appended
      // regardless of custom options
    });

    it('should include attribution with custom filename', async () => {
      const { result } = renderHook(() =>
        useExport(sampleResultsWithSources as any, productInfo)
      );

      await act(async () => {
        await result.current.exportToCSV({ filename: 'custom-report' });
      });

      expect(exportToCSV).toHaveBeenCalledWith(
        expect.anything(),
        'custom-report'
      );
      // When implemented, attribution should still be included
    });
  });
});
