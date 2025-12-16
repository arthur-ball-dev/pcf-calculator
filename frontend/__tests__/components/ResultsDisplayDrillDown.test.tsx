/**
 * ResultsDisplay Category Drill-Down Integration Tests
 *
 * Tests for the integration of CategoryDrillDown modal with ResultsDisplay.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../testUtils';
import ResultsDisplay from '../../src/components/calculator/ResultsDisplay';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import type { Calculation, Product, BOMItem } from '../../src/types/store.types';

// Mock the stores
vi.mock('../../src/store/calculatorStore', () => ({
  useCalculatorStore: vi.fn(),
}));

vi.mock('../../src/store/wizardStore', () => ({
  useWizardStore: vi.fn(),
}));

// Mock Nivo Sankey component
vi.mock('@nivo/sankey', () => ({
  ResponsiveSankey: ({
    data,
    onClick,
  }: {
    data: { nodes: Array<{ id: string; label: string; metadata?: { co2e: number } }>; links: unknown[] };
    onClick?: (node: { id: string }) => void;
  }) => {
    return (
      <div data-testid="sankey-chart">
        {/* Render clickable nodes for testing */}
        {data.nodes.map((node) => (
          <button
            key={node.id}
            data-testid={`sankey-node-${node.id}`}
            onClick={() => onClick?.(node)}
          >
            {node.label}
          </button>
        ))}
      </div>
    );
  },
}));

describe('ResultsDisplay Category Drill-Down Integration', () => {
  const mockCalculation: Calculation = {
    id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    created_at: '2024-01-15T10:30:00Z',
    total_co2e_kg: 12.5,
    materials_co2e: 7.3,
    energy_co2e: 3.8,
    transport_co2e: 1.4,
    calculation_time_ms: 450,
  };

  const mockProduct: Product = {
    id: 'prod-456',
    code: 'TSHIRT-001',
    name: 'Cotton T-Shirt',
    category: 'apparel',
    unit: 'unit',
    is_finished_product: true,
  };

  const mockBomItems: BOMItem[] = [
    {
      id: 'bom-1',
      name: 'Cotton Fabric',
      quantity: 0.2,
      unit: 'kg',
      category: 'material',
      emissionFactorId: null,
    },
    {
      id: 'bom-2',
      name: 'Polyester Thread',
      quantity: 0.01,
      unit: 'kg',
      category: 'material',
      emissionFactorId: null,
    },
    {
      id: 'bom-3',
      name: 'Electricity',
      quantity: 2.5,
      unit: 'kWh',
      category: 'energy',
      emissionFactorId: null,
    },
  ];

  beforeEach(() => {
    // Setup default mock return values
    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      calculation: mockCalculation,
      selectedProduct: mockProduct,
      bomItems: mockBomItems,
      reset: vi.fn(),
    });

    (useWizardStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      reset: vi.fn(),
    });
  });

  it('should render ResultsDisplay with Sankey diagram', () => {
    render(<ResultsDisplay />);

    expect(screen.getByTestId('results-display')).toBeInTheDocument();
    expect(screen.getByTestId('sankey-chart')).toBeInTheDocument();
  });

  it('should open category drill-down modal when category node is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Wait for dialog to appear
    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });

  it('should display category name in drill-down modal header', async () => {
    render(<ResultsDisplay />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Check dialog header
    await waitFor(() => {
      const header = screen.getByRole('heading', { name: /materials breakdown/i });
      expect(header).toBeInTheDocument();
    });
  });

  it('should close drill-down modal when close button is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on materials node to open modal
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Wait for dialog to appear
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click close button
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    // Wait for dialog to disappear
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  it('should not open drill-down modal when total node is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on total node
    const totalNode = screen.getByTestId('sankey-node-total');
    fireEvent.click(totalNode);

    // Wait a bit and verify no dialog appears
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('should open drill-down modal for energy category', async () => {
    render(<ResultsDisplay />);

    // Click on energy node
    const energyNode = screen.getByTestId('sankey-node-energy');
    fireEvent.click(energyNode);

    // Check dialog header
    await waitFor(() => {
      const header = screen.getByRole('heading', { name: /energy breakdown/i });
      expect(header).toBeInTheDocument();
    });
  });

  it('should open drill-down modal for transport category', async () => {
    render(<ResultsDisplay />);

    // Click on transport node
    const transportNode = screen.getByTestId('sankey-node-transport');
    fireEvent.click(transportNode);

    // Check dialog header
    await waitFor(() => {
      const header = screen.getByRole('heading', { name: /transport breakdown/i });
      expect(header).toBeInTheDocument();
    });
  });

  it('should display items from BOM in materials drill-down', async () => {
    render(<ResultsDisplay />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Check that BOM items are displayed
    await waitFor(() => {
      expect(screen.getByText('Cotton Fabric')).toBeInTheDocument();
      expect(screen.getByText('Polyester Thread')).toBeInTheDocument();
    });
  });

  it('should display items from BOM in energy drill-down', async () => {
    render(<ResultsDisplay />);

    // Click on energy node
    const energyNode = screen.getByTestId('sankey-node-energy');
    fireEvent.click(energyNode);

    // Check that energy BOM item is displayed
    await waitFor(() => {
      expect(screen.getByText('Electricity')).toBeInTheDocument();
    });
  });

  it('should show description text for drill-down functionality', () => {
    render(<ResultsDisplay />);

    expect(screen.getByText(/click on a category to see detailed breakdown/i)).toBeInTheDocument();
  });
});
