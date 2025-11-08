/**
 * CalculationWizard Component Tests
 *
 * TASK-FE-005: Wizard Navigation and State Machine
 *
 * Tests for the main wizard orchestration component.
 * Validates step rendering, keyboard shortcuts, and full wizard flow.
 *
 * @see knowledge/frontend/WIZARD_PATTERN.md (Main Wizard Component)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CalculationWizard from '../CalculationWizard';
import { usePCFStore } from '@/stores';

// Mock the store
vi.mock('@/stores', () => ({
  usePCFStore: vi.fn(),
}));

// Mock child components
vi.mock('../ProductSelector', () => ({
  default: () => <div data-testid="product-selector">Product Selector Step</div>,
}));

vi.mock('../BOMEditor', () => ({
  default: () => <div data-testid="bom-editor">BOM Editor Step</div>,
}));

vi.mock('../CalculateView', () => ({
  default: () => <div data-testid="calculate-view">Calculate Step</div>,
}));

vi.mock('../ResultsDisplay', () => ({
  default: () => <div data-testid="results-display">Results Step</div>,
}));

vi.mock('../WizardProgress', () => ({
  default: () => <div data-testid="wizard-progress">Progress Indicator</div>,
}));

vi.mock('../WizardNavigation', () => ({
  default: () => <div data-testid="wizard-navigation">Navigation Controls</div>,
}));

describe('CalculationWizard', () => {
  const mockGoNext = vi.fn();
  const mockGoBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up event listeners
    vi.restoreAllMocks();
  });

  // ============================================================================
  // Component Structure Tests
  // ============================================================================

  describe('Component Structure', () => {
    it('should render wizard with header, main content, and footer', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        goNext: mockGoNext,
        goBack: mockGoBack,
      });

      const { container } = render(<CalculationWizard />);

      // Check for header with title and progress
      expect(screen.getByText('PCF Calculator')).toBeInTheDocument();
      expect(screen.getByTestId('wizard-progress')).toBeInTheDocument();

      // Check for main content area
      const main = container.querySelector('main');
      expect(main).toBeInTheDocument();

      // Check for footer with navigation
      expect(screen.getByTestId('wizard-navigation')).toBeInTheDocument();
    });

    it('should use flexbox layout for full-height design', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      const { container } = render(<CalculationWizard />);

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('h-screen', 'flex', 'flex-col');
    });
  });

  // ============================================================================
  // Step Rendering Tests
  // ============================================================================

  describe('Step Rendering', () => {
    it('should render ProductSelector for "select" step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      render(<CalculationWizard />);

      expect(screen.getByTestId('product-selector')).toBeInTheDocument();
      expect(screen.queryByTestId('bom-editor')).not.toBeInTheDocument();
      expect(screen.queryByTestId('calculate-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('results-display')).not.toBeInTheDocument();
    });

    it('should render BOMEditor for "edit" step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
      });

      render(<CalculationWizard />);

      expect(screen.getByTestId('bom-editor')).toBeInTheDocument();
      expect(screen.queryByTestId('product-selector')).not.toBeInTheDocument();
      expect(screen.queryByTestId('calculate-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('results-display')).not.toBeInTheDocument();
    });

    it('should render CalculateView for "calculate" step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'calculate',
      });

      render(<CalculationWizard />);

      expect(screen.getByTestId('calculate-view')).toBeInTheDocument();
      expect(screen.queryByTestId('product-selector')).not.toBeInTheDocument();
      expect(screen.queryByTestId('bom-editor')).not.toBeInTheDocument();
      expect(screen.queryByTestId('results-display')).not.toBeInTheDocument();
    });

    it('should render ResultsDisplay for "results" step', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'results',
      });

      render(<CalculationWizard />);

      expect(screen.getByTestId('results-display')).toBeInTheDocument();
      expect(screen.queryByTestId('product-selector')).not.toBeInTheDocument();
      expect(screen.queryByTestId('bom-editor')).not.toBeInTheDocument();
      expect(screen.queryByTestId('calculate-view')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Keyboard Shortcuts Tests
  // ============================================================================

  describe('Keyboard Shortcuts', () => {
    it('should call goNext when Alt+→ is pressed', () => {
      const mockGoNext = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        canNavigateForward: true,
        goNext: mockGoNext,
        goBack: vi.fn(),
      });

      render(<CalculationWizard />);

      fireEvent.keyDown(window, {
        key: 'ArrowRight',
        code: 'ArrowRight',
        altKey: true,
      });

      expect(mockGoNext).toHaveBeenCalledTimes(1);
    });

    it('should call goBack when Alt+← is pressed', () => {
      const mockGoBack = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'edit',
        canNavigateBack: true,
        goNext: vi.fn(),
        goBack: mockGoBack,
      });

      render(<CalculationWizard />);

      fireEvent.keyDown(window, {
        key: 'ArrowLeft',
        code: 'ArrowLeft',
        altKey: true,
      });

      expect(mockGoBack).toHaveBeenCalledTimes(1);
    });

    it('should not trigger navigation without Alt key', () => {
      const mockGoNext = vi.fn();
      const mockGoBack = vi.fn();

      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        goNext: mockGoNext,
        goBack: mockGoBack,
      });

      render(<CalculationWizard />);

      fireEvent.keyDown(window, {
        key: 'ArrowRight',
        code: 'ArrowRight',
        altKey: false,
      });

      fireEvent.keyDown(window, {
        key: 'ArrowLeft',
        code: 'ArrowLeft',
        altKey: false,
      });

      expect(mockGoNext).not.toHaveBeenCalled();
      expect(mockGoBack).not.toHaveBeenCalled();
    });

    it('should prevent default behavior for keyboard shortcuts', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        goNext: vi.fn(),
        goBack: vi.fn(),
      });

      render(<CalculationWizard />);

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowRight',
        code: 'ArrowRight',
        altKey: true,
        bubbles: true,
        cancelable: true,
      });

      const preventDefaultSpy = vi.spyOn(event, 'preventDefault');
      window.dispatchEvent(event);

      expect(preventDefaultSpy).toHaveBeenCalled();
    });

    it('should clean up keyboard listeners on unmount', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        goNext: mockGoNext,
        goBack: mockGoBack,
      });

      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
      const { unmount } = render(<CalculationWizard />);

      unmount();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    });
  });

  // ============================================================================
  // Integration Tests
  // ============================================================================

  describe('Integration', () => {
    it('should integrate WizardProgress component', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      render(<CalculationWizard />);

      expect(screen.getByTestId('wizard-progress')).toBeInTheDocument();
    });

    it('should integrate WizardNavigation component', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      render(<CalculationWizard />);

      expect(screen.getByTestId('wizard-navigation')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      render(<CalculationWizard />);

      const heading = screen.getByRole('heading', { name: /PCF Calculator/i });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should use semantic HTML5 elements', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      const { container } = render(<CalculationWizard />);

      expect(container.querySelector('header')).toBeInTheDocument();
      expect(container.querySelector('main')).toBeInTheDocument();
      expect(container.querySelector('footer')).toBeInTheDocument();
    });

    it('should have proper landmark roles', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
      });

      render(<CalculationWizard />);

      expect(screen.getByRole('banner')).toBeInTheDocument(); // header
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle undefined activeStep gracefully', () => {
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: undefined,
      });

      render(<CalculationWizard />);

      // Should not crash, but may show nothing in main content
      expect(screen.getByText('PCF Calculator')).toBeInTheDocument();
    });

    it('should handle rapid keyboard shortcut presses', () => {
      const mockGoNext = vi.fn();
      (usePCFStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        activeStep: 'select',
        goNext: mockGoNext,
        goBack: vi.fn(),
      });

      render(<CalculationWizard />);

      // Simulate rapid key presses
      for (let i = 0; i < 5; i++) {
        fireEvent.keyDown(window, {
          key: 'ArrowRight',
          code: 'ArrowRight',
          altKey: true,
        });
      }

      expect(mockGoNext).toHaveBeenCalledTimes(5);
    });
  });
});
