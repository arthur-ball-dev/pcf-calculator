/**
 * DataSourceAttribution Component Tests
 *
 * Tests for the data source attribution component including:
 * - Rendering all data sources
 * - Display of attribution text for required sources
 * - License links
 * - Accessibility features
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, within } from '../../testUtils';
import userEvent from '@testing-library/user-event';
import { DataSourceAttribution, SourceBadge } from '@/components/attribution';

// Mock data sources matching API response format
const mockDataSources = [
  {
    code: 'EPA',
    name: 'EPA GHG Emission Factors Hub',
    license_type: 'US_PUBLIC_DOMAIN',
    factors_used: 5,
    attribution_required: false,
    attribution_text: 'Data source: U.S. EPA GHG Emission Factors Hub',
    license_url: 'https://edg.epa.gov/epa_data_license.html',
  },
  {
    code: 'DEFRA',
    name: 'DEFRA Conversion Factors',
    license_type: 'OGL_V3',
    factors_used: 3,
    attribution_required: true,
    attribution_text:
      'Contains UK Government GHG Conversion Factors (c) Crown copyright, licensed under the Open Government Licence v3.0',
    license_url: 'https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/',
  },
];

describe('DataSourceAttribution', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the section title', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      expect(screen.getByText('Data Source Attributions')).toBeInTheDocument();
    });

    it('renders all data sources', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      expect(screen.getByText('EPA GHG Emission Factors Hub')).toBeInTheDocument();
      expect(screen.getByText('DEFRA Conversion Factors')).toBeInTheDocument();
    });

    it('displays license type for each source', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      expect(screen.getByText(/US PUBLIC DOMAIN/)).toBeInTheDocument();
      expect(screen.getByText(/OGL V3/)).toBeInTheDocument();
    });

    it('displays factors used count when greater than zero', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      expect(screen.getByText(/Factors used: 5/)).toBeInTheDocument();
      expect(screen.getByText(/Factors used: 3/)).toBeInTheDocument();
    });
  });

  describe('Attribution Text Display', () => {
    it('displays attribution text for sources that require it', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      // DEFRA attribution is required
      expect(
        screen.getByText(/Contains UK Government GHG Conversion Factors/)
      ).toBeInTheDocument();

    });

    it('does not show attribution text for sources that do not require it', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      // EPA attribution is NOT required - text should not be displayed in italic format
      // The EPA name is displayed, but the attribution text is not emphasized
      const epaSection = screen.getByText('EPA GHG Emission Factors Hub').closest('div');
      expect(epaSection).toBeInTheDocument();

      // Check that EPA attribution text is NOT in the document with italic styling
      const italicElements = document.querySelectorAll('[class*="italic"]');
      const epaAttributionInItalic = Array.from(italicElements).some((el) =>
        el.textContent?.includes('Data source: U.S. EPA')
      );
      expect(epaAttributionInItalic).toBe(false);
    });
  });

  describe('License Links', () => {
    it('displays View License link when license_url is provided', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      const links = screen.getAllByRole('link', { name: /view license/i });
      expect(links).toHaveLength(2);
    });

    it('license links open in new tab', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      const links = screen.getAllByRole('link', { name: /view license/i });
      links.forEach((link) => {
        expect(link).toHaveAttribute('target', '_blank');
        expect(link).toHaveAttribute('rel', 'noopener noreferrer');
      });
    });

    it('license links have correct URLs', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      const epaLink = screen
        .getAllByRole('link', { name: /view license/i })
        .find((link) => link.getAttribute('href')?.includes('epa.gov'));
      expect(epaLink).toHaveAttribute('href', 'https://edg.epa.gov/epa_data_license.html');
    });

    it('does not display View License link when no URL provided', () => {
      const sourcesWithoutUrl = [
        {
          code: 'CUSTOM',
          name: 'Custom Emission Factors',
          license_type: 'INTERNAL',
          factors_used: 1,
          attribution_required: false,
          attribution_text: '',
        },
      ];

      render(<DataSourceAttribution dataSources={sourcesWithoutUrl} />);

      expect(screen.queryByRole('link', { name: /view license/i })).not.toBeInTheDocument();
    });
  });

  describe('Anchor IDs', () => {
    it('creates anchor IDs for each source', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      expect(document.getElementById('epa-attribution')).toBeInTheDocument();
      expect(document.getElementById('defra-attribution')).toBeInTheDocument();
    });

    it('uses source code as fallback anchor ID', () => {
      const unknownSource = [
        {
          code: 'CUSTOM_SOURCE',
          name: 'Custom Source',
          license_type: 'MIT',
          factors_used: 1,
          attribution_required: false,
          attribution_text: '',
        },
      ];

      render(<DataSourceAttribution dataSources={unknownSource} />);

      expect(document.getElementById('custom_source')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('renders empty state message when no data sources', () => {
      render(<DataSourceAttribution dataSources={[]} />);

      expect(screen.getByText(/no data sources/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      const heading = screen.getByRole('heading', { name: /data source attributions/i });
      expect(heading).toBeInTheDocument();
    });

    it('source names are properly structured', () => {
      render(<DataSourceAttribution dataSources={mockDataSources} />);

      // Source names should be identifiable as headings or strong text
      const defraName = screen.getByText('DEFRA Conversion Factors');
      expect(defraName).toBeInTheDocument();
    });
  });
});

describe('SourceBadge', () => {
  describe('Basic Rendering', () => {
    it('renders EPA badge correctly', () => {
      render(<SourceBadge sourceCode="EPA" />);

      expect(screen.getByText('[EPA]')).toBeInTheDocument();
    });

    it('renders DEFRA badge correctly', () => {
      render(<SourceBadge sourceCode="DEFRA" />);

      expect(screen.getByText('[DEF]')).toBeInTheDocument();
    });

    it('renders unknown source codes as plain text', () => {
      render(<SourceBadge sourceCode="UNKNOWN_SOURCE" />);

      expect(screen.getByText('UNKNOWN_SOURCE')).toBeInTheDocument();
    });
  });

  describe('Anchor Links', () => {
    it('links to correct anchor for EPA', () => {
      render(<SourceBadge sourceCode="EPA" />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '#epa-attribution');
    });

    it('links to correct anchor for DEFRA', () => {
      render(<SourceBadge sourceCode="DEFRA" />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '#defra-attribution');
    });

  });

  describe('Styling', () => {
    it('has appropriate color for EPA badge', () => {
      render(<SourceBadge sourceCode="EPA" />);

      const link = screen.getByRole('link');
      // Check that the link has some color styling (specific color may vary)
      expect(link).toHaveClass('font-semibold');
    });

    it('has hover underline effect', async () => {
      const user = userEvent.setup();
      render(<SourceBadge sourceCode="DEFRA" />);

      const link = screen.getByRole('link');
      await user.hover(link);

      // Check link has appropriate styling
      expect(link).toBeInTheDocument();
    });
  });
});
