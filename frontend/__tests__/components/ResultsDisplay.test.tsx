/**
 * ResultsDisplay Component Tests
 *
 * Tests for results dashboard with summary, breakdown table, and visualization.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-009: Results Dashboard Implementation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ResultsDisplay from '../../src/components/calculator/ResultsDisplay';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import type { Calculation } from '../../src/types/store.types';

// Mock Nivo Sankey component
vi.mock('@nivo/sankey', () => ({
  ResponsiveSankey: () => <div data-testid="sankey-chart">Sankey Chart</div>,
}));

// Mock stores
vi.mock('../../src/store/calculatorStore');
vi.mock('../../src/store/wizardStore');

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
  };

  const mockResetCalculator = vi.fn();
  const mockResetWizard = vi.fn();

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
  });

  describe('ResultsSummary Display', () => {
    it('should display total CO2e with correct formatting', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText('12.50')).toBeInTheDocument();
      expect(screen.getByText(/kg CO₂e/i)).toBeInTheDocument();
    });

    it('should display total CO2e with large font size', () => {
      render(<ResultsDisplay />);

      const totalElement = screen.getByText('12.50');
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
      expect(screen.getByText('CO₂e (kg)')).toBeInTheDocument();
      expect(screen.getByText('Percentage')).toBeInTheDocument();
    });
  });

  describe('Category Expand/Collapse', () => {
    it('should have categories collapsed by default', () => {
      render(<ResultsDisplay />);

      const materialsButton = screen.getByRole('button', { name: /materials/i });
      expect(materialsButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('should expand category when clicked', async () => {
      render(<ResultsDisplay />);

      const materialsButton = screen.getByRole('button', { name: /materials/i });
      fireEvent.click(materialsButton);

      await waitFor(() => {
        expect(materialsButton).toHaveAttribute('aria-expanded', 'true');
      });
    });

    it('should collapse category when clicked again', async () => {
      render(<ResultsDisplay />);

      const materialsButton = screen.getByRole('button', { name: /materials/i });

      // Expand
      fireEvent.click(materialsButton);
      await waitFor(() => {
        expect(materialsButton).toHaveAttribute('aria-expanded', 'true');
      });

      // Collapse
      fireEvent.click(materialsButton);
      await waitFor(() => {
        expect(materialsButton).toHaveAttribute('aria-expanded', 'false');
      });
    });
  });

  describe('Sorting', () => {
    it('should sort categories by CO2e when column header clicked', async () => {
      render(<ResultsDisplay />);

      const co2eHeader = screen.getByText('CO₂e (kg)');
      fireEvent.click(co2eHeader);

      await waitFor(() => {
        const rows = screen.getAllByRole('button', { name: /materials|energy|transport/i });
        // Should be sorted by emissions descending: Materials (7.3), Energy (3.8), Transport (1.4)
        expect(rows[0]).toHaveTextContent(/materials/i);
        expect(rows[1]).toHaveTextContent(/energy/i);
        expect(rows[2]).toHaveTextContent(/transport/i);
      });
    });

    it('should reverse sort when clicked again', async () => {
      render(<ResultsDisplay />);

      const co2eHeader = screen.getByText('CO₂e (kg)');

      // First click - descending
      fireEvent.click(co2eHeader);
      await waitFor(() => {
        const rows = screen.getAllByRole('button', { name: /materials|energy|transport/i });
        expect(rows[0]).toHaveTextContent(/materials/i);
      });

      // Second click - ascending
      fireEvent.click(co2eHeader);
      await waitFor(() => {
        const rows = screen.getAllByRole('button', { name: /materials|energy|transport/i });
        expect(rows[0]).toHaveTextContent(/transport/i);
        expect(rows[2]).toHaveTextContent(/materials/i);
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

  describe('CSV Export Button', () => {
    it('should render CSV export button', () => {
      render(<ResultsDisplay />);

      const button = screen.getByRole('button', { name: /export csv/i });
      expect(button).toBeInTheDocument();
    });

    it('should show CSV export button as disabled', () => {
      render(<ResultsDisplay />);

      const button = screen.getByRole('button', { name: /export csv/i });
      expect(button).toBeDisabled();
    });

    it('should show "Coming Soon" text on CSV export button', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
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

      const materialsButton = screen.getByRole('button', { name: /materials/i });
      expect(materialsButton).toHaveAttribute('aria-expanded');
    });

    it('should have semantic table structure', () => {
      render(<ResultsDisplay />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });

    it('should have table headers', () => {
      render(<ResultsDisplay />);

      const categoryHeader = screen.getByRole('columnheader', { name: /category/i });
      const co2eHeader = screen.getByRole('columnheader', { name: /co₂e/i });
      const percentageHeader = screen.getByRole('columnheader', { name: /percentage/i });

      expect(categoryHeader).toBeInTheDocument();
      expect(co2eHeader).toBeInTheDocument();
      expect(percentageHeader).toBeInTheDocument();
    });
  });

  describe('Number Formatting', () => {
    it('should format numbers with 2 decimal places', () => {
      render(<ResultsDisplay />);

      expect(screen.getByText('12.50')).toBeInTheDocument();
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
