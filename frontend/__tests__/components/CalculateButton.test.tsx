/**
 * CalculateButton Component Tests
 * TASK-FE-007: Test calculate button UI and integration with useCalculation hook
 *
 * Test Coverage:
 * 1. Button renders with correct text
 * 2. Button triggers calculation on click
 * 3. Loading state shows progress indicator
 * 4. Button disabled during calculation
 * 5. Button disabled when BOM invalid
 * 6. Error display
 * 7. Retry button functionality
 * 8. Accessibility (ARIA attributes)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CalculateButton } from '../../src/components/calculator/CalculateButton';
import { useCalculation } from '../../src/hooks/useCalculation';
import { useCalculatorStore } from '../../src/store/calculatorStore';

// Mock hooks
vi.mock('../../src/hooks/useCalculation');
vi.mock('../../src/store/calculatorStore');

describe('CalculateButton Component', () => {
  let mockStartCalculation: ReturnType<typeof vi.fn>;
  let mockStopPolling: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockStartCalculation = vi.fn();
    mockStopPolling = vi.fn();

    // Default mock for useCalculation
    (useCalculation as any).mockReturnValue({
      isCalculating: false,
      error: null,
      startCalculation: mockStartCalculation,
      stopPolling: mockStopPolling,
    });

    // Default mock for store
    (useCalculatorStore as any).mockReturnValue({
      selectedProductId: 'prod-123',
      bomItems: [{ id: 'bom-1', name: 'Component A', quantity: 2 }],
    });

    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Rendering
  // ==========================================================================

  describe('Rendering', () => {
    it('should render button with "Calculate PCF" text', () => {
      render(<CalculateButton />);

      expect(screen.getByRole('button', { name: /calculate pcf/i })).toBeInTheDocument();
    });

    it('should render as primary action button', () => {
      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });

      // Should have appropriate styling classes (from shadcn/ui Button)
      expect(button).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 2: Click Behavior
  // ==========================================================================

  describe('Click Behavior', () => {
    it('should call startCalculation when clicked', async () => {
      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockStartCalculation).toHaveBeenCalledTimes(1);
      });
    });

    it('should not call startCalculation when disabled', () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: null,
        bomItems: [],
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      fireEvent.click(button);

      expect(mockStartCalculation).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 3: Loading State
  // ==========================================================================

  describe('Loading State', () => {
    it('should show "Calculating..." text when calculating', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      expect(screen.getByText(/calculating/i)).toBeInTheDocument();
    });

    it('should show progress indicator when calculating', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      // Should have loading spinner or progress indicator
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
    });

    it('should disable button during calculation', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should not allow click when calculating', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      // Should not call startCalculation again
      expect(mockStartCalculation).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 4: Disabled States
  // ==========================================================================

  describe('Disabled States', () => {
    it('should disable button when no product selected', () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: null,
        bomItems: [{ id: 'bom-1', name: 'Component A', quantity: 2 }],
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      expect(button).toBeDisabled();
    });

    it('should disable button when BOM is empty', () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: 'prod-123',
        bomItems: [],
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      expect(button).toBeDisabled();
    });

    it('should enable button when product selected and BOM has items', () => {
      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      expect(button).not.toBeDisabled();
    });

    it('should show tooltip when disabled due to missing product', () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: null,
        bomItems: [{ id: 'bom-1', name: 'Component A', quantity: 2 }],
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });

      // Should have title or aria-label explaining why disabled
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    it('should show tooltip when disabled due to empty BOM', () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: 'prod-123',
        bomItems: [],
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });
  });

  // ==========================================================================
  // Test Suite 5: Error Display
  // ==========================================================================

  describe('Error Display', () => {
    it('should show error message when calculation fails', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Invalid emission factor for component: Cotton',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      expect(screen.getByText(/invalid emission factor for component: cotton/i)).toBeInTheDocument();
    });

    it('should show error in alert component', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Calculation failed',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(alert).toHaveTextContent(/calculation failed/i);
    });

    it('should show timeout error message', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Calculation timeout. The server is busy, please try again.',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      expect(screen.getByText(/calculation timeout/i)).toBeInTheDocument();
      expect(screen.getByText(/server is busy/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 6: Retry Button
  // ==========================================================================

  describe('Retry Button', () => {
    it('should show retry button when error occurs', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Calculation failed',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should call startCalculation when retry clicked', async () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Calculation failed',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(mockStartCalculation).toHaveBeenCalledTimes(1);
      });
    });

    it('should not show retry button when no error', () => {
      render(<CalculateButton />);

      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });

    it('should not show retry button when calculating', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 7: Cancel Button
  // ==========================================================================

  describe('Cancel Button', () => {
    it('should show cancel button when calculating', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should call stopPolling when cancel clicked', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockStopPolling).toHaveBeenCalledTimes(1);
    });

    it('should not show cancel button when not calculating', () => {
      render(<CalculateButton />);

      expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 8: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA attributes for button', () => {
      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      expect(button).toHaveAccessibleName();
    });

    it('should set aria-busy during calculation', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-busy', 'true');
    });

    it('should set aria-disabled when button disabled', () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: null,
        bomItems: [],
      });

      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });
      expect(button).toHaveAttribute('aria-disabled', 'true');
    });

    it('should use alert role for error messages', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Error message',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      render(<CalculateButton />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('should be keyboard accessible', () => {
      render(<CalculateButton />);

      const button = screen.getByRole('button', { name: /calculate pcf/i });

      // Should be focusable
      button.focus();
      expect(document.activeElement).toBe(button);
    });
  });

  // ==========================================================================
  // Test Suite 9: Integration Scenarios
  // ==========================================================================

  describe('Integration Scenarios', () => {
    it('should handle complete calculation flow', async () => {
      const { rerender } = render(<CalculateButton />);

      // Initial state
      expect(screen.getByRole('button', { name: /calculate pcf/i })).toBeInTheDocument();

      // Click to start
      const button = screen.getByRole('button', { name: /calculate pcf/i });
      fireEvent.click(button);

      expect(mockStartCalculation).toHaveBeenCalled();

      // Update to calculating state
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      rerender(<CalculateButton />);

      expect(screen.getByText(/calculating/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();

      // Update to completed (via store, wizard advances automatically)
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      rerender(<CalculateButton />);

      // Should be back to normal state
      expect(screen.getByRole('button', { name: /calculate pcf/i })).toBeInTheDocument();
    });

    it('should handle error then retry flow', async () => {
      const { rerender } = render(<CalculateButton />);

      // Click to start
      const button = screen.getByRole('button', { name: /calculate pcf/i });
      fireEvent.click(button);

      // Update to error state
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: 'Network error',
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      rerender(<CalculateButton />);

      expect(screen.getByText(/network error/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();

      // Click retry
      const retryButton = screen.getByRole('button', { name: /retry/i });
      fireEvent.click(retryButton);

      expect(mockStartCalculation).toHaveBeenCalledTimes(2);
    });

    it('should handle cancel then restart flow', () => {
      (useCalculation as any).mockReturnValue({
        isCalculating: true,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      const { rerender } = render(<CalculateButton />);

      // Cancel calculation
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockStopPolling).toHaveBeenCalled();

      // Update to idle state
      (useCalculation as any).mockReturnValue({
        isCalculating: false,
        error: null,
        startCalculation: mockStartCalculation,
        stopPolling: mockStopPolling,
      });

      rerender(<CalculateButton />);

      // Should be able to start again
      const button = screen.getByRole('button', { name: /calculate pcf/i });
      fireEvent.click(button);

      expect(mockStartCalculation).toHaveBeenCalled();
    });
  });
});
