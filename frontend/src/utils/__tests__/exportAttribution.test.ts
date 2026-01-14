/**
 * Export Attribution Utility Tests
 * TASK-FE-P8-008: Tests for export attribution integration
 *
 * Test Coverage:
 * 1. generateAttributionText returns formatted attribution
 * 2. appendAttributionToCSV appends attribution to CSV content
 * 3. Only sources with attribution_required: true are included
 * 4. Disclaimer is always included
 * 5. Edge cases: empty sources, multiple sources
 */

import { describe, it, expect } from 'vitest';
import {
  generateAttributionText,
  appendAttributionToCSV,
  type DataSourceInfo,
} from '@/utils/exportAttribution';

describe('exportAttribution Utility', () => {
  // ==========================================================================
  // Test Suite 1: generateAttributionText
  // ==========================================================================

  describe('generateAttributionText', () => {
    it('should include header section with DATA SOURCE ATTRIBUTIONS', () => {
      const sources: DataSourceInfo[] = [
        {
          code: 'DEFRA',
          name: 'UK Government GHG Conversion Factors',
          attribution_required: true,
          attribution_text: 'Contains UK Government GHG Conversion Factors for Company Reporting.',
        },
      ];

      const result = generateAttributionText(sources);

      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
    });

    it('should include DEFRA attribution text when DEFRA source is provided', () => {
      const sources: DataSourceInfo[] = [
        {
          code: 'DEFRA',
          name: 'UK Government GHG Conversion Factors',
          attribution_required: true,
          attribution_text: 'Contains UK Government GHG Conversion Factors for Company Reporting.',
        },
      ];

      const result = generateAttributionText(sources);

      expect(result).toContain('UK Government GHG Conversion Factors');
      expect(result).toContain('Contains UK Government GHG Conversion Factors for Company Reporting.');
    });

    it('should include DISCLAIMER section always', () => {
      const sources: DataSourceInfo[] = [];

      const result = generateAttributionText(sources);

      expect(result).toContain('DISCLAIMER');
      expect(result).toContain('Calculations are for informational purposes only.');
      expect(result).toContain('No warranty is provided regarding accuracy.');
      expect(result).toContain('Consult qualified professionals for regulatory compliance.');
    });

    it('should only include sources with attribution_required: true', () => {
      const sources: DataSourceInfo[] = [
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
      ];

      const result = generateAttributionText(sources);

      // Should include DEFRA
      expect(result).toContain('UK Government GHG Conversion Factors');
      // Should NOT include EPA
      expect(result).not.toContain('EPA GHG Emission Factors Hub');
      expect(result).not.toContain('EPA emission factors data.');
    });


    it('should handle empty sources array with disclaimer only', () => {
      const sources: DataSourceInfo[] = [];

      const result = generateAttributionText(sources);

      // Should still have structure
      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
      expect(result).toContain('DISCLAIMER');
      // Should not have any attribution content
      expect(result).toContain('Calculations are for informational purposes only.');
    });

    it('should skip sources with empty attribution_text', () => {
      const sources: DataSourceInfo[] = [
        {
          code: 'DEFRA',
          name: 'UK Government GHG Conversion Factors',
          attribution_required: true,
          attribution_text: '',
        },
      ];

      const result = generateAttributionText(sources);

      // Should not include the source name when attribution_text is empty
      // (based on implementation checking both attribution_required AND attribution_text)
      expect(result).not.toContain('UK Government GHG Conversion Factors');
    });

    it('should use separator lines for sections', () => {
      const sources: DataSourceInfo[] = [];

      const result = generateAttributionText(sources);

      // Should contain separator lines (60 equals signs)
      expect(result).toContain('='.repeat(60));
    });
  });

  // ==========================================================================
  // Test Suite 2: appendAttributionToCSV
  // ==========================================================================

  describe('appendAttributionToCSV', () => {
    it('should append attribution text to CSV content', () => {
      const csvContent = 'Component,Emissions\nSteel,1.5\nPlastic,0.8';
      const sources: DataSourceInfo[] = [
        {
          code: 'DEFRA',
          name: 'UK Government GHG Conversion Factors',
          attribution_required: true,
          attribution_text: 'Contains UK Government GHG Conversion Factors.',
        },
      ];

      const result = appendAttributionToCSV(csvContent, sources);

      // Original content preserved
      expect(result).toContain('Component,Emissions');
      expect(result).toContain('Steel,1.5');
      expect(result).toContain('Plastic,0.8');
      // Attribution appended
      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
      expect(result).toContain('UK Government GHG Conversion Factors');
      expect(result).toContain('DISCLAIMER');
    });

    it('should add blank lines between CSV data and attribution', () => {
      const csvContent = 'Component,Emissions\nSteel,1.5';
      const sources: DataSourceInfo[] = [];

      const result = appendAttributionToCSV(csvContent, sources);

      // Should have two newlines separating data from attribution
      expect(result).toContain('Steel,1.5\n\n');
    });

    it('should preserve CSV format - data rows before attribution', () => {
      const csvContent = 'A,B,C\n1,2,3\n4,5,6';
      const sources: DataSourceInfo[] = [
        {
          code: 'TEST',
          name: 'Test Source',
          attribution_required: true,
          attribution_text: 'Test attribution text.',
        },
      ];

      const result = appendAttributionToCSV(csvContent, sources);

      // CSV data should come before attribution section
      const dataIndex = result.indexOf('A,B,C');
      const attributionIndex = result.indexOf('DATA SOURCE ATTRIBUTIONS');
      expect(dataIndex).toBeLessThan(attributionIndex);
    });

    it('should include disclaimer even with empty sources in CSV', () => {
      const csvContent = 'Header\nData';
      const sources: DataSourceInfo[] = [];

      const result = appendAttributionToCSV(csvContent, sources);

      expect(result).toContain('DISCLAIMER');
      expect(result).toContain('Calculations are for informational purposes only.');
    });

    it('should handle special characters in attribution text', () => {
      const csvContent = 'Data\n1';
      const sources: DataSourceInfo[] = [
        {
          code: 'TEST',
          name: 'Test "Quoted" Source',
          attribution_required: true,
          attribution_text: 'Contains special chars: <>&',
        },
      ];

      const result = appendAttributionToCSV(csvContent, sources);

      // Special characters should be preserved (not escaped in attribution section)
      expect(result).toContain('Test "Quoted" Source');
      expect(result).toContain('Contains special chars: <>&');
    });
  });

  // ==========================================================================
  // Test Suite 3: Scenario-Based Tests (from SPEC)
  // ==========================================================================

  describe('SPEC Scenarios', () => {
    describe('Scenario 1: Happy Path - CSV export includes attribution', () => {
      it('should generate attribution with DEFRA source text and disclaimer', () => {
        const sources: DataSourceInfo[] = [
          {
            code: 'DEFRA',
            name: 'UK Government GHG Conversion Factors',
            attribution_required: true,
            attribution_text: 'Contains UK Government GHG Conversion Factors for Company Reporting.',
          },
        ];

        const csvContent = 'Component,Quantity,Unit,Emissions\nSteel,100,kg,150.5';
        const result = appendAttributionToCSV(csvContent, sources);

        // Verify all requirements
        expect(result).toContain('Steel,100,kg,150.5'); // Data rows
        expect(result).toContain('UK Government GHG Conversion Factors'); // Source name (DEFRA's official name)
        expect(result).toContain('Contains UK Government GHG Conversion Factors'); // Attribution text
        expect(result).toContain('DISCLAIMER'); // Disclaimer section
        // Verify attribution section present
        expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
      });
    });


    describe('Scenario 3: Edge Case - No data sources', () => {
      it('should still work and include disclaimer', () => {
        const sources: DataSourceInfo[] = [];

        const csvContent = 'Component,Emissions\nItem,100';
        const result = appendAttributionToCSV(csvContent, sources);

        // CSV export still works
        expect(result).toContain('Component,Emissions');
        expect(result).toContain('Item,100');
        // Disclaimer section still included
        expect(result).toContain('DISCLAIMER');
        expect(result).toContain('Calculations are for informational purposes only.');
      });
    });
  });

  // ==========================================================================
  // Test Suite 4: Edge Cases
  // ==========================================================================

  describe('Edge Cases', () => {
    it('should handle null/undefined attribution_text gracefully', () => {
      const sources: DataSourceInfo[] = [
        {
          code: 'TEST',
          name: 'Test Source',
          attribution_required: true,
          attribution_text: undefined as unknown as string,
        },
      ];

      // Should not throw
      expect(() => generateAttributionText(sources)).not.toThrow();
    });

    it('should handle very long attribution text', () => {
      const longText = 'A'.repeat(1000);
      const sources: DataSourceInfo[] = [
        {
          code: 'TEST',
          name: 'Test Source',
          attribution_required: true,
          attribution_text: longText,
        },
      ];

      const result = generateAttributionText(sources);

      expect(result).toContain(longText);
    });

    it('should handle newlines in attribution text', () => {
      const sources: DataSourceInfo[] = [
        {
          code: 'TEST',
          name: 'Test Source',
          attribution_required: true,
          attribution_text: 'Line 1\nLine 2\nLine 3',
        },
      ];

      const result = generateAttributionText(sources);

      expect(result).toContain('Line 1\nLine 2\nLine 3');
    });

    it('should maintain order of data sources as provided', () => {
      const sources: DataSourceInfo[] = [
        {
          code: 'FIRST',
          name: 'First Source',
          attribution_required: true,
          attribution_text: 'First attribution.',
        },
        {
          code: 'SECOND',
          name: 'Second Source',
          attribution_required: true,
          attribution_text: 'Second attribution.',
        },
      ];

      const result = generateAttributionText(sources);

      const firstIndex = result.indexOf('First Source');
      const secondIndex = result.indexOf('Second Source');
      expect(firstIndex).toBeLessThan(secondIndex);
    });
  });
});
