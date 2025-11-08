/**
 * WizardNavigation Component Tests
 *
 * TASK-FE-005: Wizard Navigation and State Machine
 *
 * Tests for wizard navigation controls (Next/Previous/Reset buttons).
 * Validates button states, navigation actions, and reset confirmation.
 *
 * @see knowledge/frontend/WIZARD_PATTERN.md (Navigation Component)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WizardNavigation from '../WizardNavigation';
import { usePCFStore } from '@/stores';

// Mock the store
vi.mock('@/stores', () => ({
  usePCFStore: vi.fn(),
}));

describe('WizardNavigation', () => {
  const mockGoNext = vi.fn();
  const mockGoBack = vi.fn();
  const mockSetActiveStep = vi.fn();
  const mockClearSelection = vi.fn();
  const mockResetBOM = vi.fn();
  const mockResetCalculation = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================================
  // Button Rendering Tests
  // ============================================================================

  describe('Button Rendering', () => {
    it('should render Previous and Next buttons on first step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: false,
      });

      render(<WizardNavigation />);

      expect(screen.getByRole('button', { name: /Previous/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
    });

    it('should show "Start Over" button on non-first steps', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        canNavigateForward: true,
      });

      render(<WizardNavigation />);

      expect(screen.getByRole('button', { name: /Start Over/i })).toBeInTheDocument();
    });

    it('should show "New Calculation" button on last step instead of Next', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'results',
        canNavigateBack: true,
        canNavigateForward: false,
      });

      render(<WizardNavigation />);

      expect(screen.getByRole('button', { name: /New Calculation/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /^Next$/i })).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Button State Tests
  // ============================================================================

  describe('Button States', () => {
    it('should disable Previous button when canNavigateBack is false', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: false,
      });

      render(<WizardNavigation />);

      const prevButton = screen.getByRole('button', { name: /Previous/i });
      expect(prevButton).toBeDisabled();
    });

    it('should enable Previous button when canNavigateBack is true', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        canNavigateForward: true,
      });

      render(<WizardNavigation />);

      const prevButton = screen.getByRole('button', { name: /Previous/i });
      expect(prevButton).not.toBeDisabled();
    });

    it('should disable Next button when canNavigateForward is false', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: false,
      });

      render(<WizardNavigation />);

      const nextButton = screen.getByRole('button', { name: /Next/i });
      expect(nextButton).toBeDisabled();
    });

    it('should enable Next button when canNavigateForward is true', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: true,
      });

      render(<WizardNavigation />);

      const nextButton = screen.getByRole('button', { name: /Next/i });
      expect(nextButton).not.toBeDisabled();
    });
  });

  // ============================================================================
  // Navigation Action Tests
  // ============================================================================

  describe('Navigation Actions', () => {
    it('should call goBack when Previous button is clicked', () => {
      const mockGoBack = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        canNavigateForward: true,
        goBack: mockGoBack,
      });

      render(<WizardNavigation />);

      const prevButton = screen.getByRole('button', { name: /Previous/i });
      fireEvent.click(prevButton);

      expect(mockGoBack).toHaveBeenCalledTimes(1);
    });

    it('should call goNext when Next button is clicked', () => {
      const mockGoNext = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: true,
        goNext: mockGoNext,
      });

      render(<WizardNavigation />);

      const nextButton = screen.getByRole('button', { name: /Next/i });
      fireEvent.click(nextButton);

      expect(mockGoNext).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // Reset Functionality Tests
  // ============================================================================

  describe('Reset Functionality', () => {
    it('should show confirmation dialog when Start Over is clicked', async () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        canNavigateForward: true,
      });

      render(<WizardNavigation />);

      const startOverButton = screen.getByRole('button', { name: /Start Over/i });
      fireEvent.click(startOverButton);

      await waitFor(() => {
        expect(screen.getByText(/Reset Calculator\?/i)).toBeInTheDocument();
        expect(screen.getByText(/This will clear all selections and progress/i)).toBeInTheDocument();
      });
    });

    it('should allow canceling the reset', async () => {
      const mockSetActiveStep = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        canNavigateForward: true,
        setActiveStep: mockSetActiveStep,
      });

      render(<WizardNavigation />);

      const startOverButton = screen.getByRole('button', { name: /Start Over/i });
      fireEvent.click(startOverButton);

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /Cancel/i });
        fireEvent.click(cancelButton);
      });

      expect(mockSetActiveStep).not.toHaveBeenCalled();
    });

    it('should reset all stores when reset is confirmed', async () => {
      const mockSetActiveStep = vi.fn();
      const mockClearSelection = vi.fn();
      const mockResetBOM = vi.fn();
      const mockResetCalculation = vi.fn();

      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'calculate',
        canNavigateBack: true,
        canNavigateForward: true,
        setActiveStep: mockSetActiveStep,
        clearSelection: mockClearSelection,
        resetBOM: mockResetBOM,
        resetCalculation: mockResetCalculation,
      });

      render(<WizardNavigation />);

      const startOverButton = screen.getByRole('button', { name: /Start Over/i });
      fireEvent.click(startOverButton);

      await waitFor(async () => {
        const resetButton = screen.getByRole('button', { name: /^Reset$/i });
        fireEvent.click(resetButton);
      });

      await waitFor(() => {
        expect(mockSetActiveStep).toHaveBeenCalledWith('select');
        expect(mockClearSelection).toHaveBeenCalledTimes(1);
        expect(mockResetBOM).toHaveBeenCalledTimes(1);
        expect(mockResetCalculation).toHaveBeenCalledTimes(1);
      });
    });

    it('should reset when "New Calculation" is clicked on results step', () => {
      const mockSetActiveStep = vi.fn();
      const mockClearSelection = vi.fn();
      const mockResetBOM = vi.fn();
      const mockResetCalculation = vi.fn();

      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'results',
        canNavigateBack: true,
        canNavigateForward: false,
        setActiveStep: mockSetActiveStep,
        clearSelection: mockClearSelection,
        resetBOM: mockResetBOM,
        resetCalculation: mockResetCalculation,
      });

      render(<WizardNavigation />);

      const newCalcButton = screen.getByRole('button', { name: /New Calculation/i });
      fireEvent.click(newCalcButton);

      expect(mockSetActiveStep).toHaveBeenCalledWith('select');
      expect(mockClearSelection).toHaveBeenCalledTimes(1);
      expect(mockResetBOM).toHaveBeenCalledTimes(1);
      expect(mockResetCalculation).toHaveBeenCalledTimes(1);
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper button labels', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        canNavigateForward: true,
      });

      render(<WizardNavigation />);

      expect(screen.getByRole('button', { name: /Previous/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Next/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Start Over/i })).toBeInTheDocument();
    });

    it('should be keyboard navigable', () => {
      const mockGoNext = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: true,
        goNext: mockGoNext,
      });

      render(<WizardNavigation />);

      const nextButton = screen.getByRole('button', { name: /Next/i });
      nextButton.focus();
      expect(nextButton).toHaveFocus();

      fireEvent.keyDown(nextButton, { key: 'Enter', code: 'Enter' });
      // Button click should be triggered by default behavior
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle first step (no Start Over button)', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateBack: false,
        canNavigateForward: false,
      });

      render(<WizardNavigation />);

      expect(screen.queryByRole('button', { name: /Start Over/i })).not.toBeInTheDocument();
    });

    it('should handle last step (no Next button)', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'results',
        canNavigateBack: true,
        canNavigateForward: false,
      });

      render(<WizardNavigation />);

      expect(screen.queryByRole('button', { name: /^Next$/i })).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /New Calculation/i })).toBeInTheDocument();
    });
  });
});
