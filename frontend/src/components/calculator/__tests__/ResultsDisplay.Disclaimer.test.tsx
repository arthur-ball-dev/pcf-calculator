/**
 * ResultsDisplay - Disclaimer Integration Tests
 *
 * TASK-FE-P8-007: Test Disclaimer integration in ResultsDisplay
 *
 * Test Scenarios:
 * 1. Disclaimer renders with completed calculation (variant="full", defaultExpanded=true)
 * 2. Disclaimer expand/collapse works (click toggle)
 * 3. Disclaimer has correct content (informational purposes, no warranty, etc.)
 * 4. Edge case - Disclaimer NOT rendered when no calculation results
 *
 * Per the SPEC, the Disclaimer should:
 * - Render at the TOP of ResultsDisplay (before ResultsSummary)
 * - Use variant="full" and defaultExpanded=true
 * - Have id="disclaimer" for anchor linking from LicenseFooter
 * - Support expand/collapse functionality
 * - Display legal disclaimer text about data accuracy
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

// Mock LicenseFooter to avoid duplicate text matches with Disclaimer
vi.mock('@/components/attribution/LicenseFooter', () => ({
  LicenseFooter: () => <footer data-testid="mock-license-footer">License Footer</footer>,
  default: () => <footer data-testid="mock-license-footer">License Footer</footer>,
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

describe('ResultsDisplay - Disclaimer Integration (TASK-FE-P8-007)', () => {
  beforeEach(() => {
    // Reset stores before each test
    localStorage.clear();
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
  });

  describe('Scenario 1: Disclaimer renders with completed calculation', () => {
    it('should render Disclaimer component when calculation is completed', () => {
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

      // Assert: Disclaimer should be visible with id="disclaimer"
      const disclaimer = screen.getByRole('alert');
      expect(disclaimer).toBeInTheDocument();
      expect(disclaimer).toHaveAttribute('id', 'disclaimer');
    });

    it('should render Disclaimer with full variant (amber warning styling)', () => {
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

      // Assert: Disclaimer should have amber/warning styling (full variant)
      const disclaimer = screen.getByRole('alert');
      expect(disclaimer).toHaveClass('border-amber-200');
      expect(disclaimer).toHaveClass('bg-amber-50');

      // Should have DISCLAIMER title (all caps for full variant)
      expect(screen.getByText('DISCLAIMER')).toBeInTheDocument();
    });

    it('should render Disclaimer expanded by default (defaultExpanded=true)', () => {
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

      // Assert: Full disclaimer content should be visible (expanded state)
      // Check for text that appears in expanded state
      expect(screen.getByText(/informational purposes only/i)).toBeInTheDocument();

      // The expand/collapse button should have aria-expanded="true"
      const toggleButton = screen.getByRole('button', { name: /collapse/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });

    it('should render Disclaimer at the top of results (before ResultsSummary)', () => {
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

      // Assert: Disclaimer should appear before ResultsSummary in DOM order
      const resultsDisplay = screen.getByTestId('results-display');
      const disclaimer = screen.getByRole('alert');
      const resultsSummary = screen.getByTestId('mock-results-summary');

      // Get all children of results display and check order
      const children = Array.from(resultsDisplay.children);
      const disclaimerIndex = children.findIndex(child =>
        child.contains(disclaimer)
      );
      const summaryIndex = children.findIndex(child =>
        child.contains(resultsSummary)
      );

      // Disclaimer should come before ResultsSummary
      expect(disclaimerIndex).toBeLessThan(summaryIndex);
    });

    it('should render Disclaimer within the results display container', () => {
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

      // Assert: Disclaimer should be within results-display
      const resultsDisplay = screen.getByTestId('results-display');
      const disclaimer = screen.getByRole('alert');
      expect(resultsDisplay).toContainElement(disclaimer);
    });
  });

  describe('Scenario 2: Disclaimer expand/collapse works', () => {
    it('should collapse when clicking collapse button', async () => {
      // Arrange
      const user = userEvent.setup();
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

      // Initially expanded - full text visible
      expect(screen.getByText(/informational purposes only/i)).toBeInTheDocument();

      // Click collapse button
      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      // Assert: Full text should be hidden, collapsed text shown
      expect(screen.queryByText(/informational purposes only/i)).not.toBeInTheDocument();
      expect(screen.getByText(/Click to expand full disclaimer/i)).toBeInTheDocument();
    });

    it('should expand when clicking expand button after collapsing', async () => {
      // Arrange
      const user = userEvent.setup();
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

      // Collapse first
      const collapseButton = screen.getByRole('button', { name: /collapse/i });
      await user.click(collapseButton);

      // Now expand
      const expandButton = screen.getByRole('button', { name: /expand/i });
      await user.click(expandButton);

      // Assert: Full text should be visible again
      expect(screen.getByText(/informational purposes only/i)).toBeInTheDocument();
    });

    it('should update aria-expanded attribute on toggle', async () => {
      // Arrange
      const user = userEvent.setup();
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

      // Initially aria-expanded="true"
      const toggleButton = screen.getByRole('button', { name: /collapse/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');

      // Click to collapse
      await user.click(toggleButton);

      // After collapse, button changes to expand and aria-expanded="false"
      const expandButton = screen.getByRole('button', { name: /expand/i });
      expect(expandButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should be toggleable via keyboard (Enter key)', async () => {
      // Arrange
      const user = userEvent.setup();
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

      // Focus the toggle button and press Enter
      const toggleButton = screen.getByRole('button', { name: /collapse/i });
      toggleButton.focus();
      await user.keyboard('{Enter}');

      // Assert: Should be collapsed
      expect(screen.getByText(/Click to expand full disclaimer/i)).toBeInTheDocument();
    });

    it('should be toggleable via keyboard (Space key)', async () => {
      // Arrange
      const user = userEvent.setup();
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

      // Focus the toggle button and press Space
      const toggleButton = screen.getByRole('button', { name: /collapse/i });
      toggleButton.focus();
      await user.keyboard(' ');

      // Assert: Should be collapsed
      expect(screen.getByText(/Click to expand full disclaimer/i)).toBeInTheDocument();
    });
  });

  describe('Scenario 3: Disclaimer has correct content', () => {
    it('should contain text about "informational purposes only"', () => {
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
      expect(screen.getByText(/informational purposes only/i)).toBeInTheDocument();
    });

    it('should contain text about "no warranty"', () => {
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
      expect(screen.getByText(/no warranty/i)).toBeInTheDocument();
    });

    it('should reference EPA data source', () => {
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

      // Assert: EPA should be mentioned in disclaimer content
      expect(screen.getByText(/EPA/)).toBeInTheDocument();
    });

    it('should reference DEFRA data source', () => {
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

      // Assert: DEFRA should be mentioned in disclaimer content
      // Note: The disclaimer text mentions "UK Government (DEFRA/DESNZ)"
      expect(screen.getByText(/DEFRA/)).toBeInTheDocument();
    });

    it('should reference EXIOBASE data source', () => {
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

      // Assert: EXIOBASE should be mentioned in disclaimer content
      expect(screen.getByText(/EXIOBASE/)).toBeInTheDocument();
    });

    it('should display warning icon (amber colored)', () => {
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

      // Assert: Alert with warning styling should exist
      const disclaimer = screen.getByRole('alert');
      expect(disclaimer).toHaveClass('border-amber-200');
      expect(disclaimer).toHaveClass('bg-amber-50');
    });
  });

  describe('Scenario 4: Edge case - no calculation results (Disclaimer NOT rendered)', () => {
    it('should NOT render Disclaimer when calculation is null', () => {
      // Arrange: No calculation in store
      useCalculatorStore.setState({
        calculation: null,
        selectedProduct: null,
        bomItems: [],
      });

      // Act
      render(<ResultsDisplay />);

      // Assert: Empty state message shown, no Disclaimer
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      // Disclaimer should NOT be present
      const disclaimer = screen.queryByRole('alert');
      expect(disclaimer).not.toBeInTheDocument();

      // Disclaimer content should NOT be present
      expect(screen.queryByText(/informational purposes only/i)).not.toBeInTheDocument();
      expect(screen.queryByText('DISCLAIMER')).not.toBeInTheDocument();
    });

    it('should NOT render Disclaimer when calculation status is pending', () => {
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

      // Assert: Empty state shown, no Disclaimer
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      const disclaimer = screen.queryByRole('alert');
      expect(disclaimer).not.toBeInTheDocument();
    });

    it('should NOT render Disclaimer when calculation status is in_progress', () => {
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

      // Assert: Empty state shown, no Disclaimer
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      const disclaimer = screen.queryByRole('alert');
      expect(disclaimer).not.toBeInTheDocument();
    });

    it('should NOT render Disclaimer when calculation status is failed', () => {
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

      // Assert: Empty state shown, no Disclaimer
      expect(screen.getByText(/No calculation results available/i)).toBeInTheDocument();

      const disclaimer = screen.queryByRole('alert');
      expect(disclaimer).not.toBeInTheDocument();
    });
  });

  describe('Additional Accessibility Requirements', () => {
    it('should have proper ARIA attributes on toggle button', () => {
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

      // Assert: Toggle button should have aria-expanded and aria-controls
      const toggleButton = screen.getByRole('button', { name: /collapse/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
      expect(toggleButton).toHaveAttribute('aria-controls', 'disclaimer-content');
    });

    it('should have role="alert" for screen reader announcement', () => {
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

      // Assert: Disclaimer should have alert role
      const disclaimer = screen.getByRole('alert');
      expect(disclaimer).toBeInTheDocument();
    });

    it('should not break existing results display functionality', () => {
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

      // Assert: All main components should still render with Disclaimer present
      expect(screen.getByTestId('results-display')).toBeInTheDocument();
      expect(screen.getByTestId('mock-results-summary')).toBeInTheDocument();
      expect(screen.getByTestId('mock-sankey-diagram')).toBeInTheDocument();
      expect(screen.getByTestId('mock-breakdown-table')).toBeInTheDocument();
      expect(screen.getByTestId('new-calculation-action-button')).toBeInTheDocument();
      expect(screen.getByTestId('mock-export-button')).toBeInTheDocument();
      expect(screen.getByTestId('mock-license-footer')).toBeInTheDocument(); // LicenseFooter (mocked)

      // Disclaimer should also be present
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
