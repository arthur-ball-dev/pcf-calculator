/**
 * ResultsDisplay Component Tests
 *
 * TASK-FE-P8-006: Test LicenseFooter integration in ResultsDisplay
 *
 * Test Scenarios:
 * 1. LicenseFooter renders when calculation is completed
 * 2. Footer links have correct href attributes
 * 3. Edge case - LicenseFooter not rendered when no calculation results
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import ResultsDisplay from '../ResultsDisplay';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { Calculation, Product, BOMItem } from '@/types/store.types';

// Mock the SankeyDiagram component to avoid nivo rendering issues in tests
vi.mock('@/components/visualizations/SankeyDiagram', () => ({
  default: () => <div data-testid="mock-sankey-diagram">Sankey Diagram</div>,
}));

// Mock ExportButton to simplify testing
vi.mock('@/components/ExportButton', () => ({
  ExportButton: () => <button data-testid="mock-export-button">Export</button>,
}));

// Mock ResultsSummary to simplify testing
vi.mock('../ResultsSummary', () => ({
  default: ({ totalCO2e }: { totalCO2e: number }) => (
    <div data-testid="mock-results-summary">Total: {totalCO2e} kg CO2e</div>
  ),
}));

// Mock BreakdownTable to simplify testing
vi.mock('../BreakdownTable', () => ({
  default: () => <div data-testid="mock-breakdown-table">Breakdown Table</div>,
}));

/**
 * Factory function to create a completed calculation
 */
const createCompletedCalculation = (
  overrides: Partial<Calculation> = {}
): Calculation => ({
  id: 'calc-uuid-123',
  status: 'completed',
  total_co2e_kg: 150.5,
  materials_co2e: 100,
  energy_co2e: 30,
  transport_co2e: 20.5,
  created_at: '2026-01-09T10:00:00Z',
  breakdown: {
    steel: 50,
    aluminum: 50,
    electricity: 30,
    transport_truck: 20.5,
  },
  ...overrides,
});

/**
 * Factory function to create a test product
 */
const createTestProduct = (overrides: Partial<Product> = {}): Product => ({
  id: 'product-uuid-123',
  code: 'TEST-001',
  name: 'Test Product',
  category: 'electronics',
  unit: 'unit',
  is_finished_product: true,
  ...overrides,
});

/**
 * Factory function to create BOM items
 */
const createBOMItems = (): BOMItem[] => [
  {
    id: 'bom-1',
    name: 'steel',
    quantity: 10,
    unit: 'kg',
    category: 'material',
    emissionFactorId: 'ef-1',
  },
  {
    id: 'bom-2',
    name: 'aluminum',
    quantity: 5,
    unit: 'kg',
    category: 'material',
    emissionFactorId: 'ef-2',
  },
  {
    id: 'bom-3',
    name: 'electricity',
    quantity: 100,
    unit: 'kWh',
    category: 'energy',
    emissionFactorId: 'ef-3',
  },
  {
    id: 'bom-4',
    name: 'transport_truck',
    quantity: 500,
    unit: 'tkm',
    category: 'transport',
    emissionFactorId: 'ef-4',
  },
];

describe('ResultsDisplay - LicenseFooter Integration', () => {
  beforeEach(() => {
    // Reset stores before each test
    localStorage.clear();
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
  });

  describe('Scenario 1: LicenseFooter renders when calculation completed', () => {
    it('should render LicenseFooter at the bottom of results when calculation is completed', () => {
      // Arrange: Set up store with completed calculation
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act: Render the component
      render(<ResultsDisplay />);

      // Assert: LicenseFooter should be visible
      const footer = screen.getByRole('contentinfo');
      expect(footer).toBeInTheDocument();

      // Verify footer contains expected data source text
      expect(screen.getByText(/Data sources:/i)).toBeInTheDocument();

      // Verify footer contains links to EPA, DEFRA
      expect(screen.getByRole('link', { name: /EPA/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /DEFRA/i })).toBeInTheDocument();

      // Verify footer contains disclaimer link
      expect(screen.getByRole('link', { name: /Disclaimer/i })).toBeInTheDocument();
    });

    it('should render LicenseFooter with correct structure containing attribution links', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Footer structure should contain the expected sections
      const footer = screen.getByRole('contentinfo');

      // Footer should contain text about data sources
      expect(within(footer).getByText(/Data sources:/i)).toBeInTheDocument();

      // Footer should contain text about disclaimer
      expect(within(footer).getByText(/See/i)).toBeInTheDocument();
      expect(within(footer).getByText(/for important usage information/i)).toBeInTheDocument();
    });

    it('should render LicenseFooter after the action buttons section', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Results display container should exist
      const resultsDisplay = screen.getByTestId('results-display');
      expect(resultsDisplay).toBeInTheDocument();

      // LicenseFooter should be within the results display
      const footer = screen.getByRole('contentinfo');
      expect(resultsDisplay).toContainElement(footer);
    });
  });

  describe('Scenario 2: Footer links have correct href attributes', () => {
    it('should have EPA link with href="#epa-attribution"', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert
      const epaLink = screen.getByRole('link', { name: /EPA/i });
      expect(epaLink).toHaveAttribute('href', '#epa-attribution');
    });

    it('should have DEFRA link with href="#defra-attribution"', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert
      const defraLink = screen.getByRole('link', { name: /DEFRA/i });
      expect(defraLink).toHaveAttribute('href', '#defra-attribution');
    });

    it('should have Disclaimer link with href="#disclaimer"', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert
      const disclaimerLink = screen.getByRole('link', { name: /Disclaimer/i });
      expect(disclaimerLink).toHaveAttribute('href', '#disclaimer');
    });

    it('should have all attribution links with correct hrefs', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: All links should have correct hrefs
      const expectedLinks = [
        { name: /EPA/i, href: '#epa-attribution' },
        { name: /DEFRA/i, href: '#defra-attribution' },
        { name: /Disclaimer/i, href: '#disclaimer' },
      ];

      expectedLinks.forEach(({ name, href }) => {
        const link = screen.getByRole('link', { name });
        expect(link).toHaveAttribute('href', href);
      });
    });
  });

  describe('Scenario 3: Edge case - no calculation results', () => {
    it('should NOT render LicenseFooter when calculation is null', () => {
      // Arrange: No calculation in store
      useCalculatorStore.setState({
        calculation: null,
        selectedProduct: null,
        bomItems: [],
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Empty state message should be shown
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      // LicenseFooter should NOT be present
      const footer = screen.queryByRole('contentinfo');
      expect(footer).not.toBeInTheDocument();

      // Attribution links should NOT be present
      expect(screen.queryByRole('link', { name: /EPA/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /DEFRA/i })).not.toBeInTheDocument();
    });

    it('should NOT render LicenseFooter when calculation status is not completed', () => {
      // Arrange: Calculation with pending status
      const pendingCalculation: Calculation = {
        id: 'calc-pending-123',
        status: 'pending',
      };

      useCalculatorStore.setState({
        calculation: pendingCalculation,
        selectedProduct: createTestProduct(),
        bomItems: [],
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Empty state message should be shown (status is not 'completed')
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      // LicenseFooter should NOT be present
      const footer = screen.queryByRole('contentinfo');
      expect(footer).not.toBeInTheDocument();
    });

    it('should NOT render LicenseFooter when calculation status is in_progress', () => {
      // Arrange: Calculation with in_progress status
      const inProgressCalculation: Calculation = {
        id: 'calc-in-progress-123',
        status: 'in_progress',
      };

      useCalculatorStore.setState({
        calculation: inProgressCalculation,
        selectedProduct: createTestProduct(),
        bomItems: [],
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Empty state message should be shown
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      // LicenseFooter should NOT be present
      const footer = screen.queryByRole('contentinfo');
      expect(footer).not.toBeInTheDocument();
    });

    it('should NOT render LicenseFooter when calculation status is failed', () => {
      // Arrange: Calculation with failed status
      const failedCalculation: Calculation = {
        id: 'calc-failed-123',
        status: 'failed',
        error_message: 'Calculation failed due to missing emission factors',
      };

      useCalculatorStore.setState({
        calculation: failedCalculation,
        selectedProduct: createTestProduct(),
        bomItems: [],
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Empty state message should be shown
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      // LicenseFooter should NOT be present
      const footer = screen.queryByRole('contentinfo');
      expect(footer).not.toBeInTheDocument();
    });
  });

  describe('Additional Test Requirements', () => {
    it('should render footer correctly with valid calculation data', () => {
      // Arrange: Valid completed calculation
      const calculation = createCompletedCalculation({
        total_co2e_kg: 250.75,
        materials_co2e: 150,
        energy_co2e: 50,
        transport_co2e: 50.75,
      });
      const product = createTestProduct({ name: 'Widget Pro' });
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Footer renders correctly
      const footer = screen.getByRole('contentinfo');
      expect(footer).toBeInTheDocument();

      // All expected links are present
      expect(screen.getByRole('link', { name: /EPA/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /DEFRA/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Disclaimer/i })).toBeInTheDocument();
    });

    it('should not break results display when footer is rendered', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: All main components should still render
      expect(screen.getByTestId('results-display')).toBeInTheDocument();
      expect(screen.getByTestId('mock-results-summary')).toBeInTheDocument();
      expect(screen.getByTestId('mock-sankey-diagram')).toBeInTheDocument();
      expect(screen.getByTestId('mock-breakdown-table')).toBeInTheDocument();
      expect(screen.getByTestId('new-calculation-action-button')).toBeInTheDocument();
      expect(screen.getByTestId('mock-export-button')).toBeInTheDocument();

      // Footer should also be present
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('should have Full Attribution link pointing to /about#data-sources', () => {
      // Arrange
      const calculation = createCompletedCalculation();
      const product = createTestProduct();
      const bomItems = createBOMItems();

      useCalculatorStore.setState({
        calculation,
        selectedProduct: product,
        bomItems,
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Full Attribution link should have correct href
      const fullAttributionLink = screen.getByRole('link', { name: /Full Attribution/i });
      expect(fullAttributionLink).toHaveAttribute('href', '/about#data-sources');
    });
  });
});
