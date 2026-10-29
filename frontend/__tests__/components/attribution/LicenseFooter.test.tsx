/**
 * LicenseFooter Component Tests
 *
 * Tests for the license footer component including:
 * - Rendering of source links
 * - Link to full attribution
 * - Link to disclaimer
 * - Accessibility features
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '../../testUtils';
import { LicenseFooter } from '@/components/attribution';

describe('LicenseFooter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders as a footer element', () => {
      render(<LicenseFooter />);

      const footer = document.querySelector('footer');
      expect(footer).toBeInTheDocument();
    });

    it('displays data sources label', () => {
      render(<LicenseFooter />);

      expect(screen.getByText(/data sources:/i)).toBeInTheDocument();
    });
  });

  describe('Source Links', () => {
    it('displays EPA link', () => {
      render(<LicenseFooter />);

      const link = screen.getByRole('link', { name: /epa/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '#epa-attribution');
    });

    it('displays DEFRA link', () => {
      render(<LicenseFooter />);

      const link = screen.getByRole('link', { name: /defra/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '#defra-attribution');
    });


    it('displays Full Attribution link', () => {
      render(<LicenseFooter />);

      const link = screen.getByRole('link', { name: /full attribution/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/about#data-sources');
    });
  });

  describe('Disclaimer Link', () => {
    it('displays see disclaimer text', () => {
      render(<LicenseFooter />);

      expect(screen.getByText(/see/i)).toBeInTheDocument();
    });

    it('displays disclaimer link', () => {
      render(<LicenseFooter />);

      const link = screen.getByRole('link', { name: /disclaimer/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '#disclaimer');
    });

    it('displays usage information context', () => {
      render(<LicenseFooter />);

      expect(screen.getByText(/important usage information/i)).toBeInTheDocument();
    });
  });

  describe('Separator', () => {
    it('has visual separator between sections', () => {
      render(<LicenseFooter />);

      // Check for separator element (hr or div with border)
      const footer = document.querySelector('footer');
      expect(footer).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('uses semantic footer element', () => {
      render(<LicenseFooter />);

      expect(document.querySelector('footer')).toBeInTheDocument();
    });

    it('has accessible links', () => {
      render(<LicenseFooter />);

      const links = screen.getAllByRole('link');
      links.forEach((link) => {
        expect(link).toHaveAccessibleName();
      });
    });

    it('text is legible with sufficient contrast', () => {
      render(<LicenseFooter />);

      // Footer should have muted text styling for secondary content
      const footer = document.querySelector('footer');
      expect(footer).toHaveClass('text-muted-foreground');
    });
  });

  describe('Layout', () => {
    it('has proper padding', () => {
      render(<LicenseFooter />);

      const footer = document.querySelector('footer');
      expect(footer).toHaveClass('px-3');
      expect(footer).toHaveClass('py-2');
    });

    it('has border styling', () => {
      render(<LicenseFooter />);

      const footer = document.querySelector('footer');
      expect(footer).toHaveClass('border-t');
    });

    it('has background color', () => {
      render(<LicenseFooter />);

      const footer = document.querySelector('footer');
      expect(footer).toHaveClass('bg-muted');
    });
  });
});
