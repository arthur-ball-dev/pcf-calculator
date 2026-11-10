/**
 * BreakdownTable Component Tests
 *
 * Tests for the expandable breakdown table component including:
 * - Category display with totals
 * - Expand/collapse functionality
 * - Individual item rendering
 * - Accessibility features
 *
 * TASK-FE-P8-003: Expand Items in Detailed Breakdown Section
 * Emerald Night 5B Rebuild: Raw HTML table with colored bars and category dots
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '../testUtils';
import userEvent from '@testing-library/user-event';
import BreakdownTable from '@/components/calculator/BreakdownTable';

// Mock data for tests
const mockBreakdown = {
  cotton: 1.5,
  polyester: 0.3,
  electricity_us: 0.15,
  truck_transport: 0.1,
};

const mockProps = {
  totalCO2e: 2.05,
  materialsCO2e: 1.8,
  energyCO2e: 0.15,
  transportCO2e: 0.1,
  breakdown: mockBreakdown,
};

describe('BreakdownTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders category rows with correct totals', () => {
      render(<BreakdownTable {...mockProps} />);

      // Check materials category is displayed
      expect(screen.getByText('Materials')).toBeInTheDocument();

      // Check energy category is displayed
      expect(screen.getByText('Energy')).toBeInTheDocument();

      // Check transport category is displayed
      expect(screen.getByText('Transport')).toBeInTheDocument();
    });

    it('displays correct CO2e values for each category', () => {
      render(<BreakdownTable {...mockProps} />);

      // Materials: 1.80 kg
      expect(screen.getByText('1.80')).toBeInTheDocument();

      // Energy: 0.15 kg
      expect(screen.getByText('0.15')).toBeInTheDocument();

      // Transport: 0.10 kg
      expect(screen.getByText('0.10')).toBeInTheDocument();
    });

    it('displays percentage values for each category', () => {
      render(<BreakdownTable {...mockProps} />);

      // Materials: 1.8/2.05 * 100 = 87.8%
      expect(screen.getByText('87.8%')).toBeInTheDocument();

      // Energy: 0.15/2.05 * 100 = 7.3%
      expect(screen.getByText('7.3%')).toBeInTheDocument();

      // Transport: 0.1/2.05 * 100 = 4.9%
      expect(screen.getByText('4.9%')).toBeInTheDocument();
    });

    it('only renders categories with non-zero values', () => {
      render(
        <BreakdownTable
          totalCO2e={1.8}
          materialsCO2e={1.8}
          energyCO2e={0}
          transportCO2e={0}
        />
      );

      expect(screen.getByText('Materials')).toBeInTheDocument();
      expect(screen.queryByText('Energy')).not.toBeInTheDocument();
      expect(screen.queryByText('Transport')).not.toBeInTheDocument();
    });

    it('renders table headers for Category, Amount, Percentage, Distribution', () => {
      render(<BreakdownTable {...mockProps} />);

      // Emerald Night 5B uses raw HTML table with these column headers
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Amount')).toBeInTheDocument();
      expect(screen.getByText('Percentage')).toBeInTheDocument();
      expect(screen.getByText('Distribution')).toBeInTheDocument();
    });
  });

  describe('Expand/Collapse Functionality', () => {
    it('category rows are collapsed by default', () => {
      render(<BreakdownTable {...mockProps} />);

      // Individual items should not be visible initially
      expect(screen.queryByRole('row', { name: /^Cotton\b/ })).not.toBeInTheDocument();
      expect(screen.queryByRole('row', { name: /^Polyester\b/ })).not.toBeInTheDocument();
    });

    it('clicking a category expands it to show items', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      // Click on materials category expand button
      const expandButton = screen.getByRole('button', { name: 'Materials' });
      await user.click(expandButton);

      // Items should now be visible
      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Cotton\b/ })).toBeInTheDocument();
        expect(screen.getByRole('row', { name: /^Polyester\b/ })).toBeInTheDocument();
      });
    });

    it('clicking an expanded category collapses it', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      // Expand materials
      const expandButton = screen.getByRole('button', { name: 'Materials' });
      await user.click(expandButton);

      // Wait for items to appear
      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Cotton\b/ })).toBeInTheDocument();
      });

      // Click again to collapse
      await user.click(expandButton);

      // Items should be hidden
      await waitFor(() => {
        expect(screen.queryByRole('row', { name: /^Cotton\b/ })).not.toBeInTheDocument();
      });
    });

    it('allows multiple categories to be expanded simultaneously', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      // Expand materials
      await user.click(screen.getByRole('button', { name: 'Materials' }));
      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Cotton\b/ })).toBeInTheDocument();
      });

      // Expand energy
      await user.click(screen.getByRole('button', { name: 'Energy' }));
      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Electricity Us\b/ })).toBeInTheDocument();
      });

      // Both categories should still be expanded
      expect(screen.getByRole('row', { name: /^Cotton\b/ })).toBeInTheDocument();
      expect(screen.getByRole('row', { name: /^Electricity Us\b/ })).toBeInTheDocument();
    });

    it('shows chevron rotation when expanded', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByRole('button', { name: 'Materials' });

      // Initially not rotated
      const chevron = expandButton.querySelector('svg');
      expect(chevron).not.toHaveClass('rotate-90');

      // Click to expand
      await user.click(expandButton);

      // Should now have rotate class
      await waitFor(() => {
        const expandedChevron = screen.getByRole('button', { name: 'Materials' }).querySelector('svg');
        expect(expandedChevron).toHaveClass('rotate-90');
      });
    });
  });

  describe('Item Display', () => {
    it('displays item names correctly with Title Case formatting', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Materials' }));

      // Emerald Night formatComponentName converts to Title Case
      await waitFor(() => {
        expect(screen.getByText('Cotton')).toBeInTheDocument();
        expect(screen.getByText('Polyester')).toBeInTheDocument();
      });
    });

    it('displays item CO2e values with precision', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Materials' }));

      await waitFor(() => {
        // Cotton: 1.500 kg
        expect(screen.getByText('1.500')).toBeInTheDocument();
        // Polyester: 0.300 kg
        expect(screen.getByText('0.300')).toBeInTheDocument();
      });
    });

    it('displays item percentage contribution', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Materials' }));

      await waitFor(() => {
        // Cotton: 1.5/2.05 * 100 = 73.2%
        expect(screen.getByText('73.2%')).toBeInTheDocument();
        // Polyester: 0.3/2.05 * 100 = 14.6%
        expect(screen.getByText('14.6%')).toBeInTheDocument();
      });
    });

    it('sorts items within category by CO2e descending', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Materials' }));

      await waitFor(() => {
        const rows = screen.getAllByRole('row', { name: /^(Cotton|Polyester)\b/ });
        // Cotton (1.5) should come before polyester (0.3)
        expect(rows[0]).toHaveAccessibleName(/^Cotton\b/);
        expect(rows[1]).toHaveAccessibleName(/^Polyester\b/);
      });
    });
  });

  describe('Category Classification', () => {
    it('classifies electricity components as energy', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Energy' }));

      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Electricity Us\b/ })).toBeInTheDocument();
      });
    });

    it('classifies transport components correctly', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Transport' }));

      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Truck Transport\b/ })).toBeInTheDocument();
      });
    });

    it('classifies other components as materials', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Materials' }));

      await waitFor(() => {
        expect(screen.getByRole('row', { name: /^Cotton\b/ })).toBeInTheDocument();
        expect(screen.getByRole('row', { name: /^Polyester\b/ })).toBeInTheDocument();
      });
    });
  });

  describe('Sorting', () => {
    it('sorts categories by CO2e descending by default', () => {
      render(<BreakdownTable {...mockProps} />);

      const categoryRows = screen.getAllByRole('row', { name: /^(Materials|Energy|Transport)\b/ });
      // Materials (1.8) > Energy (0.15) > Transport (0.1)
      expect(categoryRows[0]).toHaveAccessibleName(/^Materials\b/);
      expect(categoryRows[1]).toHaveAccessibleName(/^Energy\b/);
      expect(categoryRows[2]).toHaveAccessibleName(/^Transport\b/);
    });
  });

  describe('Accessibility', () => {
    it('has accessible expand buttons with aria-expanded', async () => {
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByRole('button', { name: 'Materials' });
      expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('updates aria-expanded when toggled', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByRole('button', { name: 'Materials' });
      await user.click(expandButton);

      await waitFor(() => {
        expect(expandButton).toHaveAttribute('aria-expanded', 'true');
      });
    });

    it('has progress bars with aria labels', () => {
      render(<BreakdownTable {...mockProps} />);

      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars.length).toBeGreaterThan(0);

      // Check first progress bar has aria-label
      expect(progressBars[0]).toHaveAttribute('aria-label');
    });

    it('expand buttons have aria-controls pointing to category items', () => {
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByRole('button', { name: 'Materials' });
      expect(expandButton).toHaveAttribute('aria-controls', 'materials-items');
    });
  });

  describe('Edge Cases', () => {
    it('handles zero total CO2e gracefully', () => {
      render(
        <BreakdownTable
          totalCO2e={0}
          materialsCO2e={0}
          energyCO2e={0}
          transportCO2e={0}
        />
      );

      // Should not crash, but also not show any categories
      expect(screen.queryByText('Materials')).not.toBeInTheDocument();
    });

    it('handles missing breakdown prop', () => {
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.5}
          energyCO2e={0.5}
        />
      );

      // Should render categories but expand buttons should be disabled/hidden
      expect(screen.getByText('Materials')).toBeInTheDocument();
      expect(screen.getByText('Energy')).toBeInTheDocument();
    });

    it('handles empty breakdown object', () => {
      render(
        <BreakdownTable
          totalCO2e={2.0}
          materialsCO2e={1.5}
          energyCO2e={0.5}
          breakdown={{}}
        />
      );

      // Categories should still render
      expect(screen.getByText('Materials')).toBeInTheDocument();
    });

    it('handles very small CO2e values', () => {
      render(
        <BreakdownTable
          totalCO2e={0.001}
          materialsCO2e={0.001}
          breakdown={{ tiny_component: 0.001 }}
        />
      );

      expect(screen.getByText('Materials')).toBeInTheDocument();
    });

    it('handles very large CO2e values with locale formatting', () => {
      render(
        <BreakdownTable
          totalCO2e={1000000}
          materialsCO2e={1000000}
          breakdown={{ huge_component: 1000000 }}
        />
      );

      expect(screen.getByText('Materials')).toBeInTheDocument();
      // Emerald Night formatAmount uses Intl.NumberFormat with thousand separators
      expect(screen.getByText('1,000,000.00')).toBeInTheDocument();
    });
  });

  describe('Visual Feedback', () => {
    it('shows different background for expanded items', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByRole('button', { name: 'Materials' }));

      await waitFor(() => {
        const itemRow = screen.getByRole('row', { name: /^Cotton\b/ });
        // Emerald Night uses subtle white overlay for expanded item rows
        expect(itemRow).toHaveClass('bg-white/[0.015]');
      });
    });

    it('shows progress bars with category colors', () => {
      render(<BreakdownTable {...mockProps} />);

      const progressBars = screen.getAllByRole('progressbar');
      // Progress bars should exist for each category
      expect(progressBars.length).toBe(3); // materials, energy, transport
    });
  });
});
