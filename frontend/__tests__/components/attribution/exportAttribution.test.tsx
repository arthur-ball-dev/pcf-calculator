/**
 * Export Attribution Utility Tests
 *
 * Tests for the export attribution utility functions including:
 * - generateAttributionText
 * - appendAttributionToCSV
 * - Proper formatting for all data sources
 * - Disclaimer inclusion
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import { describe, it, expect } from 'vitest';
import {
  generateAttributionText,
  appendAttributionToCSV,
  DataSourceInfo,
} from '@/utils/exportAttribution';

// Mock data sources
const mockDataSources: DataSourceInfo[] = [
  {
    code: 'EPA',
    name: 'EPA GHG Emission Factors Hub',
    attribution_required: false,
    attribution_text: 'Data source: U.S. EPA GHG Emission Factors Hub',
  },
  {
    code: 'DEFRA',
    name: 'DEFRA Conversion Factors',
    attribution_required: true,
    attribution_text:
      'Contains UK Government GHG Conversion Factors (c) Crown copyright, licensed under the Open Government Licence v3.0',
  },
  {
    code: 'EXIOBASE',
    name: 'EXIOBASE 3.8',
    attribution_required: true,
    attribution_text:
      'EXIOBASE 3.8 is licensed under Creative Commons Attribution-ShareAlike 4.0. Citation: Stadler et al. 2018',
  },
];

describe('generateAttributionText', () => {
  describe('Header Section', () => {
    it('includes DATA SOURCE ATTRIBUTIONS header', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
    });

    it('includes separator lines', () => {
      const result = generateAttributionText(mockDataSources);

      // Should have visual separators (equals signs)
      expect(result).toContain('='.repeat(60));
    });
  });

  describe('Attribution Content', () => {
    it('includes source names for required attributions', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain('DEFRA Conversion Factors');
      expect(result).toContain('EXIOBASE 3.8');
    });

    it('includes attribution text for required sources', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain(
        'Contains UK Government GHG Conversion Factors (c) Crown copyright'
      );
      expect(result).toContain('EXIOBASE 3.8 is licensed under Creative Commons');
    });

    it('does not include attribution text for non-required sources', () => {
      const result = generateAttributionText(mockDataSources);

      // EPA attribution is NOT required, so it should not appear in the output
      expect(result).not.toContain('Data source: U.S. EPA GHG Emission Factors Hub');
    });

    it('handles empty sources array', () => {
      const result = generateAttributionText([]);

      // Should still have header and disclaimer sections
      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
      expect(result).toContain('DISCLAIMER');
    });

    it('handles sources with only non-required attributions', () => {
      const nonRequiredSources: DataSourceInfo[] = [
        {
          code: 'EPA',
          name: 'EPA GHG Emission Factors Hub',
          attribution_required: false,
          attribution_text: 'Data source: U.S. EPA GHG Emission Factors Hub',
        },
      ];

      const result = generateAttributionText(nonRequiredSources);

      // Should have sections but no attribution text in content
      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
      expect(result).toContain('DISCLAIMER');
    });
  });

  describe('Disclaimer Section', () => {
    it('includes DISCLAIMER header', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain('DISCLAIMER');
    });

    it('includes informational purposes statement', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain('Calculations are for informational purposes only');
    });

    it('includes no warranty statement', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain('No warranty is provided regarding accuracy');
    });

    it('includes professional consultation recommendation', () => {
      const result = generateAttributionText(mockDataSources);

      expect(result).toContain('Consult qualified professionals for regulatory compliance');
    });
  });

  describe('Formatting', () => {
    it('uses newlines for proper separation', () => {
      const result = generateAttributionText(mockDataSources);

      // Should have multiple newlines for readability
      expect(result.split('\n').length).toBeGreaterThan(10);
    });

    it('returns a string', () => {
      const result = generateAttributionText(mockDataSources);

      expect(typeof result).toBe('string');
    });
  });
});

describe('appendAttributionToCSV', () => {
  const sampleCSV = `Component,Quantity,Unit,CO2e Factor,Source
Aluminum,1.2,kg,8.5,DEF
Electricity,25,kWh,0.4,EPA
Steel,0.5,kg,2.1,EXI`;

  describe('Appending Attribution', () => {
    it('appends attribution text to CSV content', () => {
      const result = appendAttributionToCSV(sampleCSV, mockDataSources);

      // Should contain original CSV content
      expect(result).toContain('Component,Quantity,Unit,CO2e Factor,Source');
      expect(result).toContain('Aluminum,1.2,kg,8.5,DEF');

      // Should also contain attribution
      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
    });

    it('separates CSV and attribution with blank lines', () => {
      const result = appendAttributionToCSV(sampleCSV, mockDataSources);

      // Should have blank lines between CSV and attribution
      expect(result).toContain('\n\n');
    });

    it('preserves original CSV content exactly', () => {
      const result = appendAttributionToCSV(sampleCSV, mockDataSources);

      // Original content should be at the start
      expect(result.startsWith(sampleCSV)).toBe(true);
    });

    it('includes disclaimer in appended content', () => {
      const result = appendAttributionToCSV(sampleCSV, mockDataSources);

      expect(result).toContain('DISCLAIMER');
      expect(result).toContain('Calculations are for informational purposes only');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty CSV content', () => {
      const result = appendAttributionToCSV('', mockDataSources);

      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
    });

    it('handles empty sources array', () => {
      const result = appendAttributionToCSV(sampleCSV, []);

      expect(result).toContain(sampleCSV);
      expect(result).toContain('DATA SOURCE ATTRIBUTIONS');
    });

    it('handles CSV with special characters', () => {
      const csvWithSpecialChars = `Name,Value
"Item, with comma",100
"Item ""with quotes""",200`;

      const result = appendAttributionToCSV(csvWithSpecialChars, mockDataSources);

      expect(result).toContain(csvWithSpecialChars);
    });

    it('handles CSV with unicode characters', () => {
      const csvWithUnicode = `Name,Value
"Item with (c) symbol",100
"Item with (c) Crown copyright",200`;

      const result = appendAttributionToCSV(csvWithUnicode, mockDataSources);

      expect(result).toContain('(c) symbol');
    });
  });
});
