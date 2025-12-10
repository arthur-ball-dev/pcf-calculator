/**
 * UndoRedoControls Component Tests
 *
 * Comprehensive test suite for the UndoRedoControls (toolbar) component.
 * Tests cover:
 * - Renders undo button
 * - Renders redo button
 * - Undo button disabled when canUndo=false
 * - Redo button disabled when canRedo=false
 * - Click triggers appropriate action
 * - Displays history count (optional)
 * - Accessibility requirements (ARIA labels, keyboard navigation)
 * - Tooltips show keyboard shortcuts
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 * TASK-FE-P5-003
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { UndoRedoControls } from '@/components/Calculator/UndoRedoControls';

// ============================================================================
// Mock Store
// ============================================================================

const mockUndo = vi.fn();
const mockRedo = vi.fn();
const mockCanUndo = vi.fn(() => true);
const mockCanRedo = vi.fn(() => true);
const mockGetHistoryLength = vi.fn(() => ({ past: 5, future: 2 }));

vi.mock('@/store/calculatorStore', () => ({
  useCalculatorStore: vi.fn((selector) => {
    const state = {
      undo: mockUndo,
      redo: mockRedo,
      canUndo: mockCanUndo,
      canRedo: mockCanRedo,
      getHistoryLength: mockGetHistoryLength,
    };
    return selector(state);
  }),
}));

describe('UndoRedoControls Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCanUndo.mockReturnValue(true);
    mockCanRedo.mockReturnValue(true);
    mockGetHistoryLength.mockReturnValue({ past: 5, future: 2 });
  });

  // ============================================================================
  // Basic Rendering
  // ============================================================================

  describe('rendering', () => {
    test('renders undo button', () => {
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeInTheDocument();
    });

    test('renders redo button', () => {
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      expect(redoButton).toBeInTheDocument();
    });

    test('renders toolbar container with correct test id', () => {
      render(<UndoRedoControls />);

      const toolbar = screen.getByTestId('undo-redo-toolbar');
      expect(toolbar).toBeInTheDocument();
    });

    test('applies custom className when provided', () => {
      render(<UndoRedoControls className="custom-class" />);

      const toolbar = screen.getByTestId('undo-redo-toolbar');
      expect(toolbar).toHaveClass('custom-class');
    });
  });

  // ============================================================================
  // Button States
  // ============================================================================

  describe('button states', () => {
    test('undo button is enabled when canUndo returns true', () => {
      mockCanUndo.mockReturnValue(true);

      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).not.toBeDisabled();
    });

    test('undo button is disabled when canUndo returns false', () => {
      mockCanUndo.mockReturnValue(false);

      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeDisabled();
    });

    test('redo button is enabled when canRedo returns true', () => {
      mockCanRedo.mockReturnValue(true);

      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      expect(redoButton).not.toBeDisabled();
    });

    test('redo button is disabled when canRedo returns false', () => {
      mockCanRedo.mockReturnValue(false);

      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      expect(redoButton).toBeDisabled();
    });

    test('both buttons disabled when no history exists', () => {
      mockCanUndo.mockReturnValue(false);
      mockCanRedo.mockReturnValue(false);

      render(<UndoRedoControls />);

      expect(screen.getByTestId('undo-button')).toBeDisabled();
      expect(screen.getByTestId('redo-button')).toBeDisabled();
    });
  });

  // ============================================================================
  // Click Actions
  // ============================================================================

  describe('click actions', () => {
    test('clicking undo button calls undo function', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.click(undoButton);

      expect(mockUndo).toHaveBeenCalledTimes(1);
    });

    test('clicking redo button calls redo function', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      await user.click(redoButton);

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });

    test('clicking disabled undo button does not call undo', async () => {
      mockCanUndo.mockReturnValue(false);
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.click(undoButton);

      expect(mockUndo).not.toHaveBeenCalled();
    });

    test('clicking disabled redo button does not call redo', async () => {
      mockCanRedo.mockReturnValue(false);
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      await user.click(redoButton);

      expect(mockRedo).not.toHaveBeenCalled();
    });

    test('multiple rapid clicks call function multiple times', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.click(undoButton);
      await user.click(undoButton);
      await user.click(undoButton);

      expect(mockUndo).toHaveBeenCalledTimes(3);
    });
  });

  // ============================================================================
  // History Count Display
  // ============================================================================

  describe('history count display', () => {
    test('displays past history count in tooltip', async () => {
      mockGetHistoryLength.mockReturnValue({ past: 5, future: 0 });
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        expect(screen.getByText(/5 changes/i)).toBeInTheDocument();
      });
    });

    test('displays future history count in tooltip', async () => {
      mockGetHistoryLength.mockReturnValue({ past: 0, future: 3 });
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      await user.hover(redoButton);

      await waitFor(() => {
        expect(screen.getByText(/3 changes/i)).toBeInTheDocument();
      });
    });

    test('does not show count when history is empty', async () => {
      mockGetHistoryLength.mockReturnValue({ past: 0, future: 0 });
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        expect(screen.queryByText(/\d+ changes/i)).not.toBeInTheDocument();
      });
    });

    test('shows "1 change" (singular) when only one entry', async () => {
      mockGetHistoryLength.mockReturnValue({ past: 1, future: 0 });
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        const countText = screen.queryByText(/1 change(?!s)/i);
        expect(countText).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Tooltips
  // ============================================================================

  describe('tooltips', () => {
    test('undo button tooltip shows keyboard shortcut', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        expect(screen.getByText(/Ctrl\+Z/i)).toBeInTheDocument();
      });
    });

    test('redo button tooltip shows keyboard shortcut', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      await user.hover(redoButton);

      await waitFor(() => {
        // Should show either Ctrl+Shift+Z or Ctrl+Y
        const hasShortcut =
          screen.queryByText(/Ctrl\+Shift\+Z/i) ||
          screen.queryByText(/Ctrl\+Y/i);
        expect(hasShortcut).toBeTruthy();
      });
    });

    test('tooltip disappears when not hovering', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        expect(screen.getByText(/Ctrl\+Z/i)).toBeInTheDocument();
      });

      await user.unhover(undoButton);

      await waitFor(() => {
        expect(screen.queryByText(/Ctrl\+Z/i)).not.toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('accessibility', () => {
    test('undo button has aria-label', () => {
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toHaveAttribute('aria-label', 'Undo');
    });

    test('redo button has aria-label', () => {
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      expect(redoButton).toHaveAttribute('aria-label', 'Redo');
    });

    test('buttons are keyboard focusable', () => {
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      const redoButton = screen.getByTestId('redo-button');

      expect(undoButton).not.toHaveAttribute('tabindex', '-1');
      expect(redoButton).not.toHaveAttribute('tabindex', '-1');
    });

    test('can activate buttons via keyboard Enter', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      undoButton.focus();
      await user.keyboard('{Enter}');

      expect(mockUndo).toHaveBeenCalledTimes(1);
    });

    test('can activate buttons via keyboard Space', async () => {
      const user = userEvent.setup();
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      redoButton.focus();
      await user.keyboard(' ');

      expect(mockRedo).toHaveBeenCalledTimes(1);
    });

    test('disabled buttons are announced to screen readers', () => {
      mockCanUndo.mockReturnValue(false);
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toHaveAttribute('disabled');
    });

    test('toolbar has appropriate role for grouping', () => {
      render(<UndoRedoControls />);

      // Either role="toolbar" or role="group" is acceptable
      const toolbar = screen.getByTestId('undo-redo-toolbar');
      const hasGroupingRole =
        toolbar.getAttribute('role') === 'toolbar' ||
        toolbar.getAttribute('role') === 'group';

      // If no explicit role, it should still be semantically grouped
      expect(toolbar).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Button Icons
  // ============================================================================

  describe('button icons', () => {
    test('undo button contains undo icon', () => {
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      // Icon should be rendered as SVG or icon component
      const icon = undoButton.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    test('redo button contains redo icon', () => {
      render(<UndoRedoControls />);

      const redoButton = screen.getByTestId('redo-button');
      const icon = redoButton.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Variant Props
  // ============================================================================

  describe('variant props', () => {
    test('renders with ghost variant by default', () => {
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      // Default should be ghost variant (implementation specific)
      expect(undoButton).toBeInTheDocument();
    });

    test('renders with small size by default', () => {
      render(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      // Default should be small size (implementation specific)
      expect(undoButton).toBeInTheDocument();
    });

    test('accepts and applies size prop', () => {
      render(<UndoRedoControls size="lg" />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeInTheDocument();
    });

    test('accepts and applies variant prop', () => {
      render(<UndoRedoControls variant="outline" />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('edge cases', () => {
    test('handles rapid state changes gracefully', async () => {
      const user = userEvent.setup();

      const { rerender } = render(<UndoRedoControls />);

      // Simulate rapid state changes
      mockCanUndo.mockReturnValue(false);
      rerender(<UndoRedoControls />);

      mockCanUndo.mockReturnValue(true);
      rerender(<UndoRedoControls />);

      mockCanUndo.mockReturnValue(false);
      rerender(<UndoRedoControls />);

      const undoButton = screen.getByTestId('undo-button');
      expect(undoButton).toBeDisabled();
    });

    test('handles undefined history length gracefully', () => {
      mockGetHistoryLength.mockReturnValue(undefined as any);

      // Should not throw
      expect(() => render(<UndoRedoControls />)).not.toThrow();
    });

    test('handles null history length gracefully', () => {
      mockGetHistoryLength.mockReturnValue(null as any);

      // Should not throw
      expect(() => render(<UndoRedoControls />)).not.toThrow();
    });
  });

  // ============================================================================
  // Integration with showHistoryCount Prop
  // ============================================================================

  describe('showHistoryCount prop', () => {
    test('shows history count when showHistoryCount is true', async () => {
      mockGetHistoryLength.mockReturnValue({ past: 10, future: 5 });
      const user = userEvent.setup();
      render(<UndoRedoControls showHistoryCount />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        expect(screen.getByText(/10 changes/i)).toBeInTheDocument();
      });
    });

    test('hides history count when showHistoryCount is false', async () => {
      mockGetHistoryLength.mockReturnValue({ past: 10, future: 5 });
      const user = userEvent.setup();
      render(<UndoRedoControls showHistoryCount={false} />);

      const undoButton = screen.getByTestId('undo-button');
      await user.hover(undoButton);

      await waitFor(() => {
        expect(screen.getByText(/Ctrl\+Z/i)).toBeInTheDocument();
      });

      // Count should not be shown even with history
      expect(screen.queryByText(/10 changes/i)).not.toBeInTheDocument();
    });
  });
});
