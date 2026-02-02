/**
 * CalculationOverlay Component Tests
 *
 * Tests for the modal overlay displayed during PCF calculation.
 * Covers:
 * - Rendering states (calculating, error)
 * - User interactions (cancel, retry)
 * - Accessibility attributes
 * - Elapsed time display
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CalculationOverlay } from '../../src/components/calculator/CalculationOverlay';

describe('CalculationOverlay', () => {
  const defaultProps = {
    isOpen: true,
    isCalculating: true,
    elapsedSeconds: 0,
    error: null,
    onCancel: vi.fn(),
    onRetry: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Visibility', () => {
    it('renders nothing when isOpen is false', () => {
      render(<CalculationOverlay {...defaultProps} isOpen={false} />);

      expect(screen.queryByTestId('calculation-overlay')).not.toBeInTheDocument();
    });

    it('renders overlay when isOpen is true', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByTestId('calculation-overlay')).toBeInTheDocument();
    });
  });

  describe('Calculating State', () => {
    it('displays calculating title', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByText('Calculating Carbon Footprint')).toBeInTheDocument();
    });

    it('displays calculating description', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByText(/Analyzing your Bill of Materials/)).toBeInTheDocument();
    });

    it('shows spinner during calculation', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByTestId('overlay-spinner')).toBeInTheDocument();
    });

    it('shows cancel button during calculation', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByTestId('overlay-cancel-button')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('calls onCancel when cancel button is clicked', () => {
      const onCancel = vi.fn();
      render(<CalculationOverlay {...defaultProps} onCancel={onCancel} />);

      fireEvent.click(screen.getByTestId('overlay-cancel-button'));

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe('Elapsed Time', () => {
    it('does not show elapsed time when 0 seconds', () => {
      render(<CalculationOverlay {...defaultProps} elapsedSeconds={0} />);

      expect(screen.queryByTestId('overlay-elapsed-time')).not.toBeInTheDocument();
    });

    it('shows elapsed time when greater than 0', () => {
      render(<CalculationOverlay {...defaultProps} elapsedSeconds={5} />);

      const elapsedTime = screen.getByTestId('overlay-elapsed-time');
      expect(elapsedTime).toBeInTheDocument();
      expect(elapsedTime).toHaveTextContent('5s elapsed');
    });

    it('updates elapsed time display', () => {
      const { rerender } = render(
        <CalculationOverlay {...defaultProps} elapsedSeconds={5} />
      );

      expect(screen.getByTestId('overlay-elapsed-time')).toHaveTextContent('5s');

      rerender(<CalculationOverlay {...defaultProps} elapsedSeconds={10} />);

      expect(screen.getByTestId('overlay-elapsed-time')).toHaveTextContent('10s');
    });
  });

  describe('Error State', () => {
    const errorProps = {
      ...defaultProps,
      isCalculating: false,
      error: 'Calculation failed: Invalid emission factor',
    };

    it('displays error title', () => {
      render(<CalculationOverlay {...errorProps} />);

      expect(screen.getByText('Calculation Failed')).toBeInTheDocument();
    });

    it('displays error message', () => {
      render(<CalculationOverlay {...errorProps} />);

      expect(screen.getByTestId('overlay-error-message')).toBeInTheDocument();
    });

    it('shows retry button in error state', () => {
      render(<CalculationOverlay {...errorProps} />);

      expect(screen.getByTestId('overlay-retry-button')).toBeInTheDocument();
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    it('shows close button in error state', () => {
      render(<CalculationOverlay {...errorProps} />);

      expect(screen.getByTestId('overlay-close-button')).toBeInTheDocument();
      expect(screen.getByText('Close')).toBeInTheDocument();
    });

    it('calls onRetry when retry button is clicked', () => {
      const onRetry = vi.fn();
      render(<CalculationOverlay {...errorProps} onRetry={onRetry} />);

      fireEvent.click(screen.getByTestId('overlay-retry-button'));

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('calls onCancel when close button is clicked in error state', () => {
      const onCancel = vi.fn();
      render(<CalculationOverlay {...errorProps} onCancel={onCancel} />);

      fireEvent.click(screen.getByTestId('overlay-close-button'));

      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    it('does not show spinner in error state', () => {
      render(<CalculationOverlay {...errorProps} />);

      expect(screen.queryByTestId('overlay-spinner')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has dialog role', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('has aria-modal attribute', () => {
      render(<CalculationOverlay {...defaultProps} />);

      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('has aria-labelledby pointing to title', () => {
      render(<CalculationOverlay {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'calculation-overlay-title');
    });

    it('elapsed time has aria-live attribute for screen readers', () => {
      render(<CalculationOverlay {...defaultProps} elapsedSeconds={5} />);

      const elapsedTime = screen.getByTestId('overlay-elapsed-time');
      expect(elapsedTime).toHaveAttribute('aria-live', 'polite');
      expect(elapsedTime).toHaveAttribute('aria-atomic', 'true');
    });
  });

  describe('Visual States', () => {
    it('shows backdrop', () => {
      render(<CalculationOverlay {...defaultProps} />);

      // Backdrop is the first child of the overlay with bg-black/50 class
      const overlay = screen.getByTestId('calculation-overlay');
      const backdrop = overlay.querySelector('[aria-hidden="true"]');
      expect(backdrop).toBeInTheDocument();
    });

    it('renders modal content centered', () => {
      render(<CalculationOverlay {...defaultProps} />);

      const overlay = screen.getByTestId('calculation-overlay');
      expect(overlay).toHaveClass('flex', 'items-center', 'justify-center');
    });
  });
});
