/**
 * BreakdownTable Component Tests
 *
 * Tests for the expandable breakdown table component including:
 * - Category display with totals
 * - Expand/collapse functionality
 * - Individual item rendering
 * - Sorting functionality
 * - Accessibility features
 *
 * TASK-FE-P8-003: Expand Items in Detailed Breakdown Section
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, within, waitFor } from '../testUtils';
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

    it('shows item count when breakdown data is available', () => {
      render(<BreakdownTable {...mockProps} />);

      // Materials has 2 items (cotton, polyester)
      expect(screen.getByText('(2 items)')).toBeInTheDocument();

      // Energy and Transport each have 1 item - use getAllByText since both show "(1 item)"
      const singleItemTexts = screen.getAllByText('(1 item)');
      expect(singleItemTexts).toHaveLength(2); // energy + transport
    });
  });

  describe('Expand/Collapse Functionality', () => {
    it('category rows are collapsed by default', () => {
      render(<BreakdownTable {...mockProps} />);

      // Individual items should not be visible initially
      expect(screen.queryByTestId('item-row-cotton')).not.toBeInTheDocument();
      expect(screen.queryByTestId('item-row-polyester')).not.toBeInTheDocument();
    });

    it('clicking a category expands it to show items', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      // Click on materials category expand button
      const expandButton = screen.getByTestId('expand-materials');
      await user.click(expandButton);

      // Items should now be visible
      await waitFor(() => {
        expect(screen.getByTestId('item-row-cotton')).toBeInTheDocument();
        expect(screen.getByTestId('item-row-polyester')).toBeInTheDocument();
      });
    });

    it('clicking an expanded category collapses it', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      // Expand materials
      const expandButton = screen.getByTestId('expand-materials');
      await user.click(expandButton);

      // Wait for items to appear
      await waitFor(() => {
        expect(screen.getByTestId('item-row-cotton')).toBeInTheDocument();
      });

      // Click again to collapse
      await user.click(expandButton);

      // Items should be hidden
      await waitFor(() => {
        expect(screen.queryByTestId('item-row-cotton')).not.toBeInTheDocument();
      });
    });

    it('allows multiple categories to be expanded simultaneously', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      // Expand materials
      await user.click(screen.getByTestId('expand-materials'));
      await waitFor(() => {
        expect(screen.getByTestId('item-row-cotton')).toBeInTheDocument();
      });

      // Expand energy
      await user.click(screen.getByTestId('expand-energy'));
      await waitFor(() => {
        expect(screen.getByTestId('item-row-electricity_us')).toBeInTheDocument();
      });

      // Both categories should still be expanded
      expect(screen.getByTestId('item-row-cotton')).toBeInTheDocument();
      expect(screen.getByTestId('item-row-electricity_us')).toBeInTheDocument();
    });

    it('shows chevron rotation when expanded', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByTestId('expand-materials');

      // Initially not rotated
      const chevron = expandButton.querySelector('svg');
      expect(chevron).not.toHaveClass('rotate-90');

      // Click to expand
      await user.click(expandButton);

      // Should now have rotate class
      await waitFor(() => {
        const expandedChevron = screen.getByTestId('expand-materials').querySelector('svg');
        expect(expandedChevron).toHaveClass('rotate-90');
      });
    });
  });

  describe('Item Display', () => {
    it('displays item names correctly', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        expect(screen.getByText('cotton')).toBeInTheDocument();
        expect(screen.getByText('polyester')).toBeInTheDocument();
      });
    });

    it('displays item CO2e values with precision', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByTestId('expand-materials'));

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

      await user.click(screen.getByTestId('expand-materials'));

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

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const rows = screen.getAllByTestId(/^item-row-/);
        // Cotton (1.5) should come before polyester (0.3)
        expect(rows[0]).toHaveAttribute('data-testid', 'item-row-cotton');
        expect(rows[1]).toHaveAttribute('data-testid', 'item-row-polyester');
      });
    });
  });

  describe('Category Classification', () => {
    it('classifies electricity components as energy', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByTestId('expand-energy'));

      await waitFor(() => {
        expect(screen.getByTestId('item-row-electricity_us')).toBeInTheDocument();
      });
    });

    it('classifies transport components correctly', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByTestId('expand-transport'));

      await waitFor(() => {
        expect(screen.getByTestId('item-row-truck_transport')).toBeInTheDocument();
      });
    });

    it('classifies other components as materials', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        expect(screen.getByTestId('item-row-cotton')).toBeInTheDocument();
        expect(screen.getByTestId('item-row-polyester')).toBeInTheDocument();
      });
    });
  });

  describe('Sorting', () => {
    it('sorts by CO2e descending by default', () => {
      render(<BreakdownTable {...mockProps} />);

      const categoryRows = screen.getAllByTestId(/^category-row-/);
      // Materials (1.8) > Energy (0.15) > Transport (0.1)
      expect(categoryRows[0]).toHaveAttribute('data-testid', 'category-row-materials');
    });

    it('clicking CO2e header toggles sort direction', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const co2eHeader = screen.getByRole('button', { name: /sort by co2e/i });
      await user.click(co2eHeader);

      // Should now be ascending
      const categoryRows = screen.getAllByTestId(/^category-row-/);
      expect(categoryRows[0]).toHaveAttribute('data-testid', 'category-row-transport');
    });

    it('clicking Category header sorts alphabetically', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const categoryHeader = screen.getByRole('button', { name: /sort by category/i });
      await user.click(categoryHeader);

      const categoryRows = screen.getAllByTestId(/^category-row-/);
      // When clicking category (from default co2e desc sort), it sorts alphabetically descending first
      // Then clicking again would be ascending: Energy < Materials < Transport
      // Default sort is by CO2e desc, clicking category header changes to category desc
      // So it becomes: Transport > Materials > Energy (reverse alphabetical)
      // Actually the default direction when switching fields is desc
      expect(categoryRows[0]).toHaveAttribute('data-testid', 'category-row-transport');
    });

    it('double-clicking Category header sorts alphabetically ascending', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const categoryHeader = screen.getByRole('button', { name: /sort by category/i });
      // First click: category descending
      await user.click(categoryHeader);
      // Second click: category ascending
      await user.click(categoryHeader);

      const categoryRows = screen.getAllByTestId(/^category-row-/);
      // Ascending: Energy < Materials < Transport
      expect(categoryRows[0]).toHaveAttribute('data-testid', 'category-row-energy');
    });
  });

  describe('Accessibility', () => {
    it('has accessible expand buttons with aria-expanded', async () => {
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByTestId('expand-materials');
      expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('updates aria-expanded when toggled', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      const expandButton = screen.getByTestId('expand-materials');
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

    it('sort buttons have accessible labels', () => {
      render(<BreakdownTable {...mockProps} />);

      expect(screen.getByRole('button', { name: /sort by category/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by co2e/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by percentage/i })).toBeInTheDocument();
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

    it('handles very large CO2e values', () => {
      render(
        <BreakdownTable
          totalCO2e={1000000}
          materialsCO2e={1000000}
          breakdown={{ huge_component: 1000000 }}
        />
      );

      expect(screen.getByText('Materials')).toBeInTheDocument();
      expect(screen.getByText('1000000.00')).toBeInTheDocument();
    });
  });

  describe('Visual Feedback', () => {
    it('shows different background for expanded items', async () => {
      const user = userEvent.setup();
      render(<BreakdownTable {...mockProps} />);

      await user.click(screen.getByTestId('expand-materials'));

      await waitFor(() => {
        const itemRow = screen.getByTestId('item-row-cotton');
        expect(itemRow).toHaveClass('bg-muted/30');
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
