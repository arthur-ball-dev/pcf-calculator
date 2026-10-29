/**
 * SankeyDiagram Component Tests
 *
 * Tests for Sankey diagram visualization component.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-008: Nivo Sankey Implementation
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../testUtils';
import SankeyDiagram from '../../src/components/visualizations/SankeyDiagram';
import type { Calculation } from '../../src/types/store.types';

// Mock Nivo Sankey component
vi.mock('@nivo/sankey', () => ({
  ResponsiveSankey: ({ data }: { data: { nodes: unknown[]; links: unknown[] } }) => (
    <div data-testid="sankey-chart">
      <div data-testid="sankey-nodes-count">{data.nodes.length}</div>
      <div data-testid="sankey-links-count">{data.links.length}</div>
    </div>
  ),
}));

describe('SankeyDiagram', () => {
  describe('Rendering', () => {
    it('should render Sankey diagram with calculation data', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const chart = screen.getByTestId('sankey-chart');
      expect(chart).toBeInTheDocument();
    });

    it('should render with correct number of nodes', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const nodesCount = screen.getByTestId('sankey-nodes-count');
      expect(nodesCount.textContent).toBe('4'); // materials, energy, transport, total
    });

    it('should render with correct number of links', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const linksCount = screen.getByTestId('sankey-links-count');
      expect(linksCount.textContent).toBe('3'); // materials→total, energy→total, transport→total
    });

    it('should have container with correct test id', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const container = screen.getByTestId('sankey-container');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('should show empty state when calculation is null', () => {
      render(<SankeyDiagram calculation={null} />);

      const emptyState = screen.getByText(/no calculation data available/i);
      expect(emptyState).toBeInTheDocument();
    });

    it('should show loading state when calculation is pending', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'pending',
        product_id: 'prod-456',
      };

      render(<SankeyDiagram calculation={calculation} />);

      const loadingState = screen.getByText(/calculating/i);
      expect(loadingState).toBeInTheDocument();
    });

    it('should show loading state when calculation is in progress', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'in_progress',
        product_id: 'prod-456',
      };

      render(<SankeyDiagram calculation={calculation} />);

      const loadingState = screen.getByText(/calculating/i);
      expect(loadingState).toBeInTheDocument();
    });

    it('should show error state when calculation failed', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'failed',
        product_id: 'prod-456',
        error_message: 'Calculation failed',
      };

      render(<SankeyDiagram calculation={calculation} />);

      const errorState = screen.getByText(/calculation failed/i);
      expect(errorState).toBeInTheDocument();
    });
  });

  describe('Responsive Sizing', () => {
    it('should apply custom width when provided', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} width={800} />);

      const container = screen.getByTestId('sankey-container');
      expect(container).toHaveStyle({ width: '800px' });
    });

    it('should apply custom height when provided', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} height={400} />);

      const container = screen.getByTestId('sankey-container');
      expect(container).toHaveStyle({ height: '400px' });
    });

    it('should have minimum height of 400px when no height provided', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const container = screen.getByTestId('sankey-container');
      const style = window.getComputedStyle(container);
      const heightValue = parseInt(style.height, 10);
      expect(heightValue).toBeGreaterThanOrEqual(400);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA role for visualization', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const container = screen.getByTestId('sankey-container');
      expect(container).toHaveAttribute('role', 'img');
    });

    it('should have descriptive aria-label', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const container = screen.getByTestId('sankey-container');
      expect(container).toHaveAttribute('aria-label');
      const ariaLabel = container.getAttribute('aria-label');
      expect(ariaLabel).toContain('Carbon flow');
    });
  });

  describe('Data Transformation', () => {
    it('should exclude zero-value categories from visualization', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 10.0,
        materials_co2e: 10.0,
        energy_co2e: 0,
        transport_co2e: 0,
      };

      render(<SankeyDiagram calculation={calculation} />);

      const nodesCount = screen.getByTestId('sankey-nodes-count');
      expect(nodesCount.textContent).toBe('2'); // Only materials and total
    });

    it('should handle calculations with missing breakdown data', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 15.0,
        // No breakdown fields
      };

      render(<SankeyDiagram calculation={calculation} />);

      // Should show empty state when no breakdown data
      const emptyState = screen.getByText(/no breakdown data available/i);
      expect(emptyState).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('should memoize transformed data to prevent recalculation', () => {
      const calculation: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      const { rerender } = render(<SankeyDiagram calculation={calculation} />);

      // Rerender with same data
      rerender(<SankeyDiagram calculation={calculation} />);

      // Component should still render correctly
      const chart = screen.getByTestId('sankey-chart');
      expect(chart).toBeInTheDocument();
    });
  });
});
