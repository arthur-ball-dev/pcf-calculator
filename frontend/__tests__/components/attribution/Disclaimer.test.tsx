/**
 * Disclaimer Component Tests
 *
 * Tests for the disclaimer component including:
 * - Full and condensed variants
 * - Expand/collapse functionality
 * - Accessibility features
 * - Legal compliance text display
 *
 * TASK-FE-P8-004: Attribution & Compliance UI
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '../../testUtils';
import userEvent from '@testing-library/user-event';
import { Disclaimer } from '@/components/attribution';

describe('Disclaimer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Full Variant (default)', () => {
    it('renders with full variant by default', () => {
      render(<Disclaimer />);

      expect(screen.getByText('DISCLAIMER')).toBeInTheDocument();
    });

    it('displays full disclaimer text when expanded', () => {
      render(<Disclaimer defaultExpanded={true} />);

      expect(
        screen.getByText(/This application uses emission factor data from multiple public sources/)
      ).toBeInTheDocument();

      expect(
        screen.getByText(/including the U.S. EPA, UK Government \(DEFRA\/DESNZ\), and EXIOBASE/)
      ).toBeInTheDocument();
    });

    it('shows disclaimer about informational purposes', () => {
      render(<Disclaimer defaultExpanded={true} />);

      expect(
        screen.getByText(/emission factors and calculations provided are for informational purposes only/i)
      ).toBeInTheDocument();
    });

    it('shows disclaimer about no warranty', () => {
      render(<Disclaimer defaultExpanded={true} />);

      expect(screen.getByText(/no warranty is provided/i)).toBeInTheDocument();
    });

    it('shows disclaimer about consulting professionals', () => {
      render(<Disclaimer defaultExpanded={true} />);

      expect(
        screen.getByText(/consult qualified professionals for regulatory compliance/i)
      ).toBeInTheDocument();
    });

    it('shows disclaimer about data provider warranties', () => {
      render(<Disclaimer defaultExpanded={true} />);

      expect(
        screen.getByText(/data providers.*make no warranty regarding data accuracy/i)
      ).toBeInTheDocument();
    });
  });

  describe('Expand/Collapse Functionality', () => {
    it('is expanded by default when defaultExpanded is true', () => {
      render(<Disclaimer variant="full" defaultExpanded={true} />);

      expect(
        screen.getByText(/This application uses emission factor data/)
      ).toBeInTheDocument();
    });

    it('is collapsed when defaultExpanded is false', () => {
      render(<Disclaimer variant="full" defaultExpanded={false} />);

      // Full text should not be visible when collapsed
      expect(screen.getByText(/click to expand/i)).toBeInTheDocument();
    });

    it('expands when clicking expand button', async () => {
      const user = userEvent.setup();
      render(<Disclaimer variant="full" defaultExpanded={false} />);

      // Click expand button
      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      await waitFor(() => {
        expect(
          screen.getByText(/This application uses emission factor data/)
        ).toBeInTheDocument();
      });
    });

    it('collapses when clicking collapse button', async () => {
      const user = userEvent.setup();
      render(<Disclaimer variant="full" defaultExpanded={true} />);

      // Click collapse button
      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      await waitFor(() => {
        expect(screen.getByText(/click to expand/i)).toBeInTheDocument();
      });
    });

    it('toggles aria-expanded state correctly', async () => {
      const user = userEvent.setup();
      render(<Disclaimer variant="full" defaultExpanded={false} />);

      const button = screen.getByRole('button');

      // Initially not expanded
      expect(button).toHaveAttribute('aria-expanded', 'false');

      // Click to expand
      await user.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });

  describe('Condensed Variant', () => {
    it('renders condensed text', () => {
      render(<Disclaimer variant="condensed" />);

      expect(
        screen.getByText(/Calculations are for informational purposes only/)
      ).toBeInTheDocument();
    });

    it('shows link to full disclaimer', () => {
      render(<Disclaimer variant="condensed" />);

      const link = screen.getByRole('link', { name: /view full disclaimer/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '#disclaimer');
    });

    it('does not show expand/collapse button', () => {
      render(<Disclaimer variant="condensed" />);

      expect(screen.queryByRole('button', { name: /expand/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /collapse/i })).not.toBeInTheDocument();
    });

    it('shows verify results message', () => {
      render(<Disclaimer variant="condensed" />);

      expect(
        screen.getByText(/Verify results for regulatory or financial reporting/)
      ).toBeInTheDocument();
    });
  });

  describe('Alert Styling', () => {
    it('full variant has warning severity', () => {
      render(<Disclaimer variant="full" />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      // Should have warning styling (amber/yellow colors)
      expect(alert).toHaveClass('border-amber-200');
    });

    it('condensed variant has info severity', () => {
      render(<Disclaimer variant="condensed" />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });
  });

  describe('ID and Anchor', () => {
    it('full variant has disclaimer ID for anchor linking', () => {
      render(<Disclaimer variant="full" />);

      expect(document.getElementById('disclaimer')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has alert role', () => {
      render(<Disclaimer />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('has accessible expand/collapse button', () => {
      render(<Disclaimer variant="full" defaultExpanded={false} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAccessibleName();
    });

    it('full disclaimer text is readable by screen readers when expanded', () => {
      render(<Disclaimer variant="full" defaultExpanded={true} />);

      const content = screen.getByText(/This application uses emission factor data/);
      expect(content).toBeVisible();
    });
  });
});
