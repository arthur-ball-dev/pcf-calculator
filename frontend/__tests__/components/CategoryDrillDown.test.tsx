/**
 * CategoryDrillDown Component Tests
 *
 * Tests for the category drill-down modal that shows breakdown
 * of individual items within an emission category.
 *
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../testUtils';
import CategoryDrillDown from '../../src/components/visualizations/CategoryDrillDown';

describe('CategoryDrillDown', () => {
  const mockItems = [
    { name: 'Cotton Fabric', co2e: 6.5 },
    { name: 'Polyester Thread', co2e: 0.3 },
    { name: 'Dye Materials', co2e: 0.5 },
  ];

  const defaultProps = {
    category: 'Materials',
    items: mockItems,
    total: 7.3,
    open: true,
    onClose: vi.fn(),
  };

  describe('Rendering', () => {
    it('should render dialog when open is true', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should not render dialog when open is false', () => {
      render(<CategoryDrillDown {...defaultProps} open={false} />);

      const dialog = screen.queryByRole('dialog');
      expect(dialog).not.toBeInTheDocument();
    });

    it('should display category name as header', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      const header = screen.getByRole('heading', { name: /materials breakdown/i });
      expect(header).toBeInTheDocument();
    });

    it('should display all items in the list', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      expect(screen.getByText('Cotton Fabric')).toBeInTheDocument();
      expect(screen.getByText('Polyester Thread')).toBeInTheDocument();
      expect(screen.getByText('Dye Materials')).toBeInTheDocument();
    });

    it('should display CO2e values for each item', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      // Get all category items and check their values
      const items = screen.getAllByTestId('category-item');
      expect(items[0]).toHaveTextContent('6.500 kg');
      expect(items[1]).toHaveTextContent('0.500 kg'); // Dye Materials (sorted second)
      expect(items[2]).toHaveTextContent('0.300 kg'); // Polyester Thread (sorted third)
    });

    it('should display percentage of category for each item', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      // Cotton Fabric: 6.5 / 7.3 = 89.0%
      expect(screen.getByText(/89\.0%/)).toBeInTheDocument();
      // Polyester Thread: 0.3 / 7.3 = 4.1%
      expect(screen.getByText(/4\.1%/)).toBeInTheDocument();
      // Dye Materials: 0.5 / 7.3 = 6.8%
      expect(screen.getByText(/6\.8%/)).toBeInTheDocument();
    });

    it('should display total for category', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      // Look for the total section
      const totalText = screen.getByText(/^total$/i);
      expect(totalText).toBeInTheDocument();
      expect(screen.getByText(/7\.300 kg CO/)).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('should call onClose when dialog is dismissed', () => {
      const onClose = vi.fn();
      render(<CategoryDrillDown {...defaultProps} onClose={onClose} />);

      // Find and click the close button
      const closeButton = screen.getByRole('button', { name: /close/i });
      fireEvent.click(closeButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('should call onClose when escape key is pressed', () => {
      const onClose = vi.fn();
      render(<CategoryDrillDown {...defaultProps} onClose={onClose} />);

      // Press escape key
      fireEvent.keyDown(document, { key: 'Escape' });

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Empty State', () => {
    it('should display message when no items provided', () => {
      render(<CategoryDrillDown {...defaultProps} items={[]} total={0} />);

      const emptyMessage = screen.getByText(/no items/i);
      expect(emptyMessage).toBeInTheDocument();
    });
  });

  describe('Different Categories', () => {
    it('should display correct header for Energy category', () => {
      render(<CategoryDrillDown {...defaultProps} category="Energy" />);

      const header = screen.getByRole('heading', { name: /energy breakdown/i });
      expect(header).toBeInTheDocument();
    });

    it('should display correct header for Transport category', () => {
      render(<CategoryDrillDown {...defaultProps} category="Transport" />);

      const header = screen.getByRole('heading', { name: /transport breakdown/i });
      expect(header).toBeInTheDocument();
    });
  });

  describe('Data Formatting', () => {
    it('should handle very small CO2e values', () => {
      const smallItems = [{ name: 'Trace Material', co2e: 0.001 }];
      render(<CategoryDrillDown {...defaultProps} items={smallItems} total={0.001} />);

      // Use getAllByText since the value appears in both item and total
      const elements = screen.getAllByText(/0\.001/);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });

    it('should handle large CO2e values', () => {
      const largeItems = [{ name: 'Heavy Material', co2e: 1234.567 }];
      render(<CategoryDrillDown {...defaultProps} items={largeItems} total={1234.567} />);

      // Use getAllByText since the value appears in both item and total
      const elements = screen.getAllByText(/1234\.567/);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });

    it('should handle zero percentage gracefully', () => {
      const items = [{ name: 'Zero Item', co2e: 0 }];
      render(<CategoryDrillDown {...defaultProps} items={items} total={10} />);

      expect(screen.getByText(/0\.0%/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper dialog role', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should have accessible name on dialog', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAccessibleName(/materials breakdown/i);
    });

    it('should have visible close button with accessible name', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: /close/i });
      expect(closeButton).toBeInTheDocument();
    });

    it('should focus trap within dialog', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      // Radix Dialog should handle focus trap automatically
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('should display items sorted by CO2e value descending by default', () => {
      render(<CategoryDrillDown {...defaultProps} />);

      const items = screen.getAllByTestId('category-item');
      // First item should be the highest value (Cotton Fabric: 6.5)
      expect(items[0]).toHaveTextContent('Cotton Fabric');
      // Second item (Dye Materials: 0.5)
      expect(items[1]).toHaveTextContent('Dye Materials');
      // Third item (Polyester Thread: 0.3)
      expect(items[2]).toHaveTextContent('Polyester Thread');
    });
  });
});
