/**
 * WizardProgress Component Tests
 *
 * TASK-FE-005: Wizard Navigation and State Machine
 *
 * Tests for the wizard progress indicator component.
 * Validates step visualization, navigation, and accessibility.
 *
 * @see knowledge/frontend/WIZARD_PATTERN.md (Progress Indicator Component)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import WizardProgress from '../WizardProgress';
import { usePCFStore } from '@/stores';

// Mock the store
vi.mock('@/stores', () => ({
  usePCFStore: vi.fn(),
}));

describe('WizardProgress', () => {
  const mockSetActiveStep = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================================
  // Rendering Tests
  // ============================================================================

  describe('Rendering', () => {
    it('should render all 4 wizard steps', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'select',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      expect(screen.getByText('Select Product')).toBeInTheDocument();
      expect(screen.getByText('Edit BOM')).toBeInTheDocument();
      expect(screen.getByText('Calculate')).toBeInTheDocument();
      expect(screen.getByText('Results')).toBeInTheDocument();
    });

    it('should highlight current step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'edit',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      const editButton = screen.getByRole('button', { name: /Edit BOM.*current/i });
      expect(editButton).toHaveClass('border-primary', 'bg-primary');
    });

    it('should show progress line width based on current step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'calculate',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      const { container } = render(<WizardProgress />);

      // Calculate step is index 2, so progress should be (2/3) * 100 = 66.67%
      const progressLine = container.querySelector('.bg-primary');
      expect(progressLine).toHaveStyle({ width: '66.66666666666666%' });
    });
  });

  // ============================================================================
  // Navigation Tests
  // ============================================================================

  describe('Navigation', () => {
    it('should allow clicking on first step (always accessible)', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'edit',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      const selectButton = screen.getByRole('button', { name: /Select Product/i });
      fireEvent.click(selectButton);

      expect(mockSetActiveStep).toHaveBeenCalledWith('select');
    });

    it('should prevent clicking on inaccessible steps (skip prevention)', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'select',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      // Try to click on "Edit BOM" (step 2) - should be disabled
      const editButton = screen.getByRole('button', { name: /Edit BOM/i });
      expect(editButton).toBeDisabled();

      fireEvent.click(editButton);
      expect(mockSetActiveStep).not.toHaveBeenCalled();
    });

    it('should allow navigation to completed steps', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'calculate',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      // Both "Select Product" and "Edit BOM" should be clickable
      const selectButton = screen.getByRole('button', { name: /Select Product/i });
      const editButton = screen.getByRole('button', { name: /Edit BOM/i });

      expect(selectButton).not.toBeDisabled();
      expect(editButton).not.toBeDisabled();

      fireEvent.click(editButton);
      expect(mockSetActiveStep).toHaveBeenCalledWith('edit');
    });
  });

  // ============================================================================
  // Visual State Tests
  // ============================================================================

  describe('Visual States', () => {
    it('should show completed steps with check icon', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'calculate',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      // Previous steps should have completed styling
      const selectButton = screen.getByRole('button', { name: /Select Product.*completed/i });
      expect(selectButton).toHaveClass('border-primary', 'bg-background', 'text-primary');
    });

    it('should show incomplete steps with muted styling', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'select',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      // Future steps should have muted styling
      const resultsButton = screen.getByRole('button', { name: /Results/i });
      expect(resultsButton).toHaveClass('border-muted', 'bg-background', 'text-muted-foreground');
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA labels for each step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'edit',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      expect(screen.getByRole('button', { name: /Select Product.*completed/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Edit BOM.*current/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Calculate/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Results/i })).toBeInTheDocument();
    });

    it('should mark current step with aria-current="step"', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'calculate',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      const calculateButton = screen.getByRole('button', { name: /Calculate.*current/i });
      expect(calculateButton).toHaveAttribute('aria-current', 'step');
    });

    it('should be keyboard navigable', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'select',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      const selectButton = screen.getByRole('button', { name: /Select Product.*current/i });

      // Should be focusable
      selectButton.focus();
      expect(selectButton).toHaveFocus();
    });

    it('should have focus-visible styling', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'select',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      render(<WizardProgress />);

      const selectButton = screen.getByRole('button', { name: /Select Product.*current/i });
      expect(selectButton).toHaveClass('focus-visible:outline-none', 'focus-visible:ring-2');
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle last step correctly', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'results',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      const { container } = render(<WizardProgress />);

      // Progress line should be 100%
      const progressLine = container.querySelector('.bg-primary');
      expect(progressLine).toHaveStyle({ width: '100%' });

      // Current step should be "Results"
      const resultsButton = screen.getByRole('button', { name: /Results.*current/i });
      expect(resultsButton).toHaveClass('border-primary', 'bg-primary');
    });

    it('should handle first step correctly', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockImplementation((selector: any) => {
        const state = {
          activeStep: 'select',
          setActiveStep: mockSetActiveStep,
        };
        return selector(state);
      });

      const { container } = render(<WizardProgress />);

      // Progress line should be 0%
      const progressLine = container.querySelector('.bg-primary');
      expect(progressLine).toHaveStyle({ width: '0%' });
    });
  });
});
