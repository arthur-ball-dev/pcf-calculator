/**
 * SankeyDiagram Node Click Tests
 *
 * Tests for category drill-down click handler functionality.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../testUtils';
import SankeyDiagram from '../../src/components/visualizations/SankeyDiagram';
import type { Calculation } from '../../src/types/store.types';

// Mock Nivo Sankey component with click handler support
vi.mock('@nivo/sankey', () => ({
  ResponsiveSankey: ({
    data,
    onClick,
  }: {
    data: { nodes: Array<{ id: string; label: string }>; links: unknown[] };
    onClick?: (node: { id: string }) => void;
  }) => {
    return (
      <div data-testid="sankey-chart">
        <div data-testid="sankey-nodes-count">{data.nodes.length}</div>
        <div data-testid="sankey-links-count">{data.links.length}</div>
        {/* Render clickable nodes for testing */}
        {data.nodes.map((node) => (
          <button
            key={node.id}
            data-testid={`sankey-node-${node.id}`}
            onClick={() => onClick?.({ id: node.id })}
          >
            {node.label}
          </button>
        ))}
      </div>
    );
  },
}));

describe('SankeyDiagram Node Click Handler', () => {
  const completedCalculation: Calculation = {
    id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    total_co2e_kg: 12.5,
    materials_co2e: 7.3,
    energy_co2e: 3.8,
    transport_co2e: 1.4,
  };

  it('should call onNodeClick when a category node is clicked', () => {
    const onNodeClick = vi.fn();

    render(<SankeyDiagram calculation={completedCalculation} onNodeClick={onNodeClick} />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    expect(onNodeClick).toHaveBeenCalled();
  });

  it('should pass category info when materials node is clicked', () => {
    const onNodeClick = vi.fn();

    render(<SankeyDiagram calculation={completedCalculation} onNodeClick={onNodeClick} />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    expect(onNodeClick).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'materials',
      })
    );
  });

  it('should pass category info when energy node is clicked', () => {
    const onNodeClick = vi.fn();

    render(<SankeyDiagram calculation={completedCalculation} onNodeClick={onNodeClick} />);

    // Click on energy node
    const energyNode = screen.getByTestId('sankey-node-energy');
    fireEvent.click(energyNode);

    expect(onNodeClick).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'energy',
      })
    );
  });

  it('should pass category info when transport node is clicked', () => {
    const onNodeClick = vi.fn();

    render(<SankeyDiagram calculation={completedCalculation} onNodeClick={onNodeClick} />);

    // Click on transport node
    const transportNode = screen.getByTestId('sankey-node-transport');
    fireEvent.click(transportNode);

    expect(onNodeClick).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'transport',
      })
    );
  });

  it('should not call onNodeClick when total node is clicked', () => {
    const onNodeClick = vi.fn();

    render(<SankeyDiagram calculation={completedCalculation} onNodeClick={onNodeClick} />);

    // Click on total node
    const totalNode = screen.getByTestId('sankey-node-total');
    fireEvent.click(totalNode);

    // Total node should not trigger callback (it's not a drillable category)
    expect(onNodeClick).not.toHaveBeenCalled();
  });

  it('should work without onNodeClick prop (optional)', () => {
    // Should not throw when clicking without handler
    render(<SankeyDiagram calculation={completedCalculation} />);

    const materialsNode = screen.getByTestId('sankey-node-materials');
    expect(() => fireEvent.click(materialsNode)).not.toThrow();
  });

  it('should render clickable cursor on category nodes', () => {
    const onNodeClick = vi.fn();

    render(<SankeyDiagram calculation={completedCalculation} onNodeClick={onNodeClick} />);

    const container = screen.getByTestId('sankey-container');
    // Container should have cursor pointer class when onNodeClick is provided
    expect(container).toHaveClass('cursor-pointer');
  });

  it('should not have clickable cursor when no onNodeClick prop', () => {
    render(<SankeyDiagram calculation={completedCalculation} />);

    const container = screen.getByTestId('sankey-container');
    // Container should not have cursor pointer when no handler
    expect(container).not.toHaveClass('cursor-pointer');
  });
});
