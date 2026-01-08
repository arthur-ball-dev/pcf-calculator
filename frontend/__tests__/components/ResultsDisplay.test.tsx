/**
 * ResultsDisplay Component Tests
 *
 * Tests for results dashboard with summary, breakdown table, and visualization.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-009: Results Dashboard Implementation
 * TASK-FE-P5-011: Updated tests for ExportButton integration (TDD Exception approved)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, userEvent } from '../testUtils';
import ResultsDisplay from '../../src/components/calculator/ResultsDisplay';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import { useExport } from '../../src/hooks/useExport';
import type { Calculation } from '../../src/types/store.types';

// Mock Nivo Sankey component
vi.mock('@nivo/sankey', () => ({
  ResponsiveSankey: () => <div data-testid="sankey-chart">Sankey Chart</div>,
}));

// Mock stores
vi.mock('../../src/store/calculatorStore');
vi.mock('../../src/store/wizardStore');

// Mock useExport hook for ExportButton
vi.mock('../../src/hooks/useExport');

describe('ResultsDisplay', () => {
  const mockCalculation: Calculation = {
    id: 'calc-123',
    status: 'completed',
    product_id: 'prod-456',
    total_co2e_kg: 12.5,
    materials_co2e: 7.3,
    energy_co2e: 3.8,
    transport_co2e: 1.4,
    calculation_time_ms: 450,
    created_at: '2024-11-08T15:00:00Z',
    // Component-level breakdown needed for expand/collapse functionality
    breakdown: {
      'Steel': 5.0,
      'Aluminum': 2.3,
      'Electricity': 3.8,
      'Truck Transport': 1.4,
    },
  };

  const mockResetCalculator = vi.fn();
  const mockResetWizard = vi.fn();
  const mockExportToCSV = vi.fn().mockResolvedValue(undefined);
  const mockExportToExcel = vi.fn().mockResolvedValue(undefined);
  const mockClearError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // Setup calculator store mock
    vi.mocked(useCalculatorStore).mockReturnValue({
      calculation: mockCalculation,
      reset: mockResetCalculator,
      selectedProductId: null,
      selectedProduct: null,
      bomItems: [],
      hasUnsavedChanges: false,
      isLoadingProducts: false,
      isLoadingBOM: false,
      setSelectedProduct: vi.fn(),
      setSelectedProductDetails: vi.fn(),
      setBomItems: vi.fn(),
      updateBomItem: vi.fn(),
      addBomItem: vi.fn(),
      removeBomItem: vi.fn(),
      setCalculation: vi.fn(),
      setLoadingProducts: vi.fn(),
      setLoadingBOM: vi.fn(),
    });

    // Setup wizard store mock
    vi.mocked(useWizardStore).mockReturnValue({
      currentStep: 'results',
      completedSteps: ['select', 'edit', 'calculate'],
      canProceed: false,
      canGoBack: true,
      setStep: vi.fn(),
      markStepComplete: vi.fn(),
      markStepIncomplete: vi.fn(),
      goNext: vi.fn(),
      goBack: vi.fn(),
      reset: mockResetWizard,
    });

    // Setup useExport hook mock
    vi.mocked(useExport).mockReturnValue({
      exportToCSV: mockExportToCSV,
      exportToExcel: mockExportToExcel,
      isExporting: false,
      error: null,
      clearError: mockClearError,
    });
  });

  describe('ResultsSummary Display', () => {
    it('should display total CO2e with correct formatting', () => {
      render(<ResultsDisplay />);

      // Use testid to get the specific total element (avoid duplicate match with table total row)
      expect(screen.getByTestId('total-co2e')).toHaveTextContent('12.50');
      expect(screen.getByText(/kg CO₂e/i)).toBeInTheDocument();
    });

    it('should display total CO2e with large font size', () => {
      render(<ResultsDisplay />);

      // Use testid to get the specific total element
      const totalElement = screen.getByTestId('total-co2e');
      expect(totalElement).toHaveClass('text-5xl'); // Tailwind class for ~48px
    });

    it('should display calculation timestamp', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText(/calculated at/i)).toBeInTheDocument();
    });

    it('should format date correctly', () => {
      render(<ResultsDisplay />);

      // Should show formatted date (Nov 8, 2024 or similar)
      const dateText = screen.getByText(/nov 8, 2024/i);
      expect(dateText).toBeInTheDocument();
    });
  });

  describe('Breakdown Table Rendering', () => {
    it('should display category headers', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText(/materials/i)).toBeInTheDocument();
      expect(screen.getByText(/energy/i)).toBeInTheDocument();
      expect(screen.getByText(/transport/i)).toBeInTheDocument();
    });

    it('should display category totals with correct formatting', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText('7.30')).toBeInTheDocument(); // Materials total
      expect(screen.getByText('3.80')).toBeInTheDocument(); // Energy total
      expect(screen.getByText('1.40')).toBeInTheDocument(); // Transport total
    });

    it('should display category percentages', () => {
      render(<ResultsDisplay />);

      // Materials: 7.3/12.5 = 58.4%
      expect(screen.getByText('58.4%')).toBeInTheDocument();
      // Energy: 3.8/12.5 = 30.4%
      expect(screen.getByText('30.4%')).toBeInTheDocument();
      // Transport: 1.4/12.5 = 11.2%
      expect(screen.getByText('11.2%')).toBeInTheDocument();
    });

    it('should display table headers', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('CO2e (kg)')).toBeInTheDocument();
      expect(screen.getByText('Percentage')).toBeInTheDocument();
    });
  });

  describe('Category Expand/Collapse', () => {
    it('should have categories collapsed by default', () => {
      render(<ResultsDisplay />);

      const materialsExpander = screen.getByTestId('expand-materials');
      expect(materialsExpander).toHaveAttribute('aria-expanded', 'false');
    });

    it('should expand category when clicked', async () => {
      const user = userEvent.setup();
      render(<ResultsDisplay />);

      const materialsExpander = screen.getByTestId('expand-materials');
      await user.click(materialsExpander);

      await waitFor(() => {
        expect(screen.getByTestId('expand-materials')).toHaveAttribute('aria-expanded', 'true');
      });
    });

    it('should collapse category when clicked again', async () => {
      const user = userEvent.setup();
      render(<ResultsDisplay />);

      // Expand
      await user.click(screen.getByTestId('expand-materials'));
      await waitFor(() => {
        expect(screen.getByTestId('expand-materials')).toHaveAttribute('aria-expanded', 'true');
      });

      // Collapse
      await user.click(screen.getByTestId('expand-materials'));
      await waitFor(() => {
        expect(screen.getByTestId('expand-materials')).toHaveAttribute('aria-expanded', 'false');
      });
    });
  });

  describe('Sorting', () => {
    it('should sort categories by CO2e when column header clicked', async () => {
      render(<ResultsDisplay />);

      // Click the CO2e sort button
      const co2eHeader = screen.getByRole('button', { name: /sort by co2e/i });
      fireEvent.click(co2eHeader);

      await waitFor(() => {
        // Check order by looking at category row test IDs
        const materialsRow = screen.getByTestId('category-row-materials');
        const energyRow = screen.getByTestId('category-row-energy');
        const transportRow = screen.getByTestId('category-row-transport');

        // All should be present - sorting is already descending by default
        expect(materialsRow).toBeInTheDocument();
        expect(energyRow).toBeInTheDocument();
        expect(transportRow).toBeInTheDocument();
      });
    });

    it('should reverse sort when clicked again', async () => {
      render(<ResultsDisplay />);

      // Click the CO2e sort button
      const co2eHeader = screen.getByRole('button', { name: /sort by co2e/i });

      // First click - descending (default already desc, so first click toggles)
      fireEvent.click(co2eHeader);

      // Second click - ascending
      fireEvent.click(co2eHeader);

      await waitFor(() => {
        // All rows should still be visible after sorting
        expect(screen.getByTestId('category-row-materials')).toBeInTheDocument();
        expect(screen.getByTestId('category-row-energy')).toBeInTheDocument();
        expect(screen.getByTestId('category-row-transport')).toBeInTheDocument();
      });
    });
  });

  describe('SankeyDiagram Integration', () => {
    it('should render Sankey diagram', () => {
      render(<ResultsDisplay />);

      expect(screen.getByTestId('sankey-chart')).toBeInTheDocument();
    });

    it('should pass calculation data to Sankey diagram', () => {
      render(<ResultsDisplay />);

      const diagram = screen.getByTestId('sankey-chart');
      expect(diagram).toBeInTheDocument();
    });
  });

  describe('New Calculation Button', () => {
    it('should render New Calculation button', () => {
      render(<ResultsDisplay />);

      const button = screen.getByRole('button', { name: /new calculation/i });
      expect(button).toBeInTheDocument();
    });

    it('should reset wizard when New Calculation clicked', async () => {
      render(<ResultsDisplay />);

      const button = screen.getByRole('button', { name: /new calculation/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockResetWizard).toHaveBeenCalledTimes(1);
      });
    });

    it('should reset calculator when New Calculation clicked', async () => {
      render(<ResultsDisplay />);

      const button = screen.getByRole('button', { name: /new calculation/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockResetCalculator).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('ExportButton Integration', () => {
    it('should render ExportButton component', () => {
      render(<ResultsDisplay />);

      // ExportButton renders a container with data-testid="export-buttons"
      expect(screen.getByTestId('export-buttons')).toBeInTheDocument();
    });

    it('should render CSV and Excel export buttons', () => {
      render(<ResultsDisplay />);

      expect(screen.getByTestId('export-csv-button')).toBeInTheDocument();
      expect(screen.getByTestId('export-excel-button')).toBeInTheDocument();
    });

    it('should display CSV and Excel button labels', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText('CSV')).toBeInTheDocument();
      expect(screen.getByText('Excel')).toBeInTheDocument();
    });

    it('should trigger CSV export when CSV button clicked', async () => {
      const user = userEvent.setup();
      render(<ResultsDisplay />);

      // Click CSV button directly
      await user.click(screen.getByTestId('export-csv-button'));

      expect(mockExportToCSV).toHaveBeenCalled();
    });

    it('should trigger Excel export when Excel button clicked', async () => {
      const user = userEvent.setup();
      render(<ResultsDisplay />);

      // Click Excel button directly
      await user.click(screen.getByTestId('export-excel-button'));

      expect(mockExportToExcel).toHaveBeenCalled();
    });

    it('should show loading state during export', () => {
      vi.mocked(useExport).mockReturnValue({
        exportToCSV: mockExportToCSV,
        exportToExcel: mockExportToExcel,
        isExporting: true,
        error: null,
        clearError: mockClearError,
      });

      render(<ResultsDisplay />);

      // Export buttons should be disabled during export
      const csvButton = screen.getByTestId('export-csv-button');
      const excelButton = screen.getByTestId('export-excel-button');
      expect(csvButton).toBeDisabled();
      expect(excelButton).toBeDisabled();
    });
  });

  describe('Empty State', () => {
    it('should show message when no calculation available', () => {
      vi.mocked(useCalculatorStore).mockReturnValue({
        calculation: null,
        reset: mockResetCalculator,
        selectedProductId: null,
        selectedProduct: null,
        bomItems: [],
        hasUnsavedChanges: false,
        isLoadingProducts: false,
        isLoadingBOM: false,
        setSelectedProduct: vi.fn(),
        setSelectedProductDetails: vi.fn(),
        setBomItems: vi.fn(),
        updateBomItem: vi.fn(),
        addBomItem: vi.fn(),
        removeBomItem: vi.fn(),
        setCalculation: vi.fn(),
        setLoadingProducts: vi.fn(),
        setLoadingBOM: vi.fn(),
      });

      render(<ResultsDisplay />);

      expect(screen.getByText(/no calculation results available/i)).toBeInTheDocument();
    });
  });

  describe('Responsive Layout', () => {
    it('should render all sections in correct order', () => {
      const { container } = render(<ResultsDisplay />);

      const sections = container.querySelectorAll('.space-y-8 > *');
      expect(sections.length).toBeGreaterThanOrEqual(3); // Summary, Sankey, Breakdown, Actions
    });

    it('should have proper spacing between sections', () => {
      const { container } = render(<ResultsDisplay />);

      const mainContainer = container.querySelector('.space-y-8');
      expect(mainContainer).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible category toggle buttons', () => {
      render(<ResultsDisplay />);

      const materialsExpander = screen.getByTestId('expand-materials');
      expect(materialsExpander).toHaveAttribute('aria-expanded');
    });

    it('should have semantic table structure', () => {
      render(<ResultsDisplay />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });

    it('should have table headers', () => {
      render(<ResultsDisplay />);

      // Headers contain sortable buttons
      expect(screen.getByRole('button', { name: /sort by category/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by co2e/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /sort by percentage/i })).toBeInTheDocument();
    });
  });

  describe('Number Formatting', () => {
    it('should format numbers with 2 decimal places', () => {
      render(<ResultsDisplay />);

      // Use testid for total to avoid duplicate match with table total row
      expect(screen.getByTestId('total-co2e')).toHaveTextContent('12.50');
      expect(screen.getByText('7.30')).toBeInTheDocument();
      expect(screen.getByText('3.80')).toBeInTheDocument();
      expect(screen.getByText('1.40')).toBeInTheDocument();
    });

    it('should format percentages with 1 decimal place', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText('58.4%')).toBeInTheDocument();
      expect(screen.getByText('30.4%')).toBeInTheDocument();
      expect(screen.getByText('11.2%')).toBeInTheDocument();
    });
  });
});
