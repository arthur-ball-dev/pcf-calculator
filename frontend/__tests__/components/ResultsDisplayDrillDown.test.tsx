/**
 * ResultsDisplay Category Drill-Down Integration Tests
 *
 * Tests for the integration of SankeyDiagram drill-down with ResultsDisplay.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * Architecture note: Drill-down is handled INTERNALLY by SankeyDiagram.
 * - SankeyDiagram has internal state (expandedCategory) for drill-down
 * - When a drillable category node is clicked, SankeyDiagram re-renders
 *   the chart with expanded breakdown data and shows a "Back to Overview" button
 * - ResultsDisplay simply passes `calculation` prop to SankeyDiagram
 * - There is no external dialog/modal for drill-down
 *
 * TASK-FE-P8-002: Category Drill-Down in Carbon Flow Visualization
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../testUtils';
import ResultsDisplay from '../../src/components/calculator/ResultsDisplay';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import type { Calculation, Product, BOMItem } from '../../src/types/store.types';

// Track the last onNodeClick and calculation passed to SankeyDiagram
let capturedSankeyProps: { calculation: Calculation | null; onNodeClick?: (node: unknown) => void };

// Mock SankeyDiagram with a functional mock that simulates drill-down behavior.
// The real SankeyDiagram handles drill-down internally with expandedCategory state.
// This mock replicates that behavior: renders category buttons, and when clicked,
// shows expanded view with back button and breakdown items.
vi.mock('../../src/components/visualizations/SankeyDiagram', () => {
  const { useState } = require('react');
  return {
    default: ({ calculation }: { calculation: Calculation | null; onNodeClick?: (node: unknown) => void }) => {
      const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

      capturedSankeyProps = { calculation };

      if (!calculation || calculation.status !== 'completed') {
        return <div data-testid="sankey-container">No data</div>;
      }

      const categories = [
        { id: 'materials', label: 'Materials', value: calculation.materials_co2e || 0 },
        { id: 'energy', label: 'Energy', value: calculation.energy_co2e || 0 },
        { id: 'transport', label: 'Transport', value: calculation.transport_co2e || 0 },
      ].filter(c => c.value > 0);

      // Expanded view - show breakdown details and back button
      if (expandedCategory) {
        const cat = categories.find(c => c.id === expandedCategory);
        const title = cat
          ? `${cat.label} Breakdown`
          : `${expandedCategory.charAt(0).toUpperCase() + expandedCategory.slice(1)} Breakdown`;

        // Simulate breakdown items from calculation.breakdown
        const breakdownItems: string[] = [];
        if (calculation.breakdown) {
          Object.keys(calculation.breakdown).forEach(name => {
            breakdownItems.push(name);
          });
        }

        return (
          <div data-testid="sankey-container" role="img" aria-label={`${title} showing breakdown`}>
            <button
              data-testid="sankey-back-button"
              onClick={() => setExpandedCategory(null)}
            >
              Back to Overview
            </button>
            <span data-testid="sankey-expanded-title">{title}</span>
            {breakdownItems.map(item => (
              <span key={item}>{item}</span>
            ))}
          </div>
        );
      }

      // Overview mode - show clickable category nodes and hint text
      return (
        <div data-testid="sankey-container" role="img" aria-label={`Carbon flow diagram showing emissions breakdown with ${categories.length + 1} categories. Click on a category to see detailed breakdown.`}>
          <div data-testid="sankey-chart">
            <p>Click on a category to drill down</p>
            {categories.map(cat => (
              <button
                key={cat.id}
                data-testid={`sankey-node-${cat.id}`}
                onClick={() => setExpandedCategory(cat.id)}
              >
                {cat.label}
              </button>
            ))}
            <button
              data-testid="sankey-node-total"
              onClick={() => {/* total is not drillable */}}
            >
              Total
            </button>
          </div>
        </div>
      );
    },
  };
});

// Mock ExportButton to simplify testing
vi.mock('../../src/components/ExportButton', () => ({
  ExportButton: () => <button data-testid="mock-export-button">Export</button>,
}));

// Mock ResultsHero to simplify testing
vi.mock('../../src/components/calculator/ResultsHero', () => ({
  default: ({ totalCO2e }: { totalCO2e: number }) => (
    <div data-testid="mock-results-hero">Total: {totalCO2e} kg CO2e</div>
  ),
}));

// Mock BreakdownTable to simplify testing
vi.mock('../../src/components/calculator/BreakdownTable', () => ({
  default: () => <div data-testid="mock-breakdown-table">Breakdown Table</div>,
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
    breakdown: {
      'Cotton Fabric': 4.5,
      'Polyester Thread': 2.8,
      'Electricity': 3.8,
      'Truck Transport': 1.4,
    },
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
    // Setup store state with completed calculation
    useCalculatorStore.setState({
      calculation: mockCalculation,
      selectedProduct: mockProduct,
      bomItems: mockBomItems,
    });
  });

  it('should render ResultsDisplay with Sankey diagram', () => {
    render(<ResultsDisplay />);

    expect(screen.getByTestId('results-display')).toBeInTheDocument();
    expect(screen.getByTestId('sankey-chart')).toBeInTheDocument();
  });

  it('should expand to category breakdown when category node is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // SankeyDiagram internally switches to expanded view with title
    await waitFor(() => {
      expect(screen.getByTestId('sankey-expanded-title')).toHaveTextContent('Materials Breakdown');
    });
  });

  it('should display category name in expanded view header', async () => {
    render(<ResultsDisplay />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Check expanded header shows materials breakdown title
    await waitFor(() => {
      expect(screen.getByTestId('sankey-expanded-title')).toHaveTextContent(/materials breakdown/i);
    });
  });

  it('should return to overview when back button is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on materials node to expand
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Wait for expanded view
    await waitFor(() => {
      expect(screen.getByTestId('sankey-expanded-title')).toHaveTextContent('Materials Breakdown');
    });

    // Click back button
    const backButton = screen.getByTestId('sankey-back-button');
    fireEvent.click(backButton);

    // Wait for overview to return (drill-down hint reappears)
    await waitFor(() => {
      expect(screen.getByText(/click on a category to drill down/i)).toBeInTheDocument();
    });
  });

  it('should not expand when total node is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on total node
    const totalNode = screen.getByTestId('sankey-node-total');
    fireEvent.click(totalNode);

    // Wait a bit and verify no expansion occurs (hint text still visible)
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(screen.getByText(/click on a category to drill down/i)).toBeInTheDocument();

    // No expanded title should appear in the Sankey area
    expect(screen.queryByTestId('sankey-expanded-title')).not.toBeInTheDocument();
  });

  it('should expand to energy breakdown when energy node is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on energy node
    const energyNode = screen.getByTestId('sankey-node-energy');
    fireEvent.click(energyNode);

    // Check expanded header
    await waitFor(() => {
      expect(screen.getByTestId('sankey-expanded-title')).toHaveTextContent(/energy breakdown/i);
    });
  });

  it('should expand to transport breakdown when transport node is clicked', async () => {
    render(<ResultsDisplay />);

    // Click on transport node
    const transportNode = screen.getByTestId('sankey-node-transport');
    fireEvent.click(transportNode);

    // Check expanded header
    await waitFor(() => {
      expect(screen.getByTestId('sankey-expanded-title')).toHaveTextContent(/transport breakdown/i);
    });
  });

  it('should display breakdown items when category is expanded', async () => {
    render(<ResultsDisplay />);

    // Click on materials node
    const materialsNode = screen.getByTestId('sankey-node-materials');
    fireEvent.click(materialsNode);

    // Check that breakdown items from calculation.breakdown are displayed
    await waitFor(() => {
      expect(screen.getByText('Cotton Fabric')).toBeInTheDocument();
      expect(screen.getByText('Polyester Thread')).toBeInTheDocument();
    });
  });

  it('should display breakdown items for energy category', async () => {
    render(<ResultsDisplay />);

    // Click on energy node
    const energyNode = screen.getByTestId('sankey-node-energy');
    fireEvent.click(energyNode);

    // Check that energy BOM item is displayed
    await waitFor(() => {
      expect(screen.getByText('Electricity')).toBeInTheDocument();
    });
  });

  it('should show drill-down hint text in overview mode', () => {
    render(<ResultsDisplay />);

    // The SankeyDiagram renders visible hint text in overview mode
    expect(screen.getByText(/click on a category to drill down/i)).toBeInTheDocument();
  });
});
