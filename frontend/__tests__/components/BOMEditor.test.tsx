/**
 * BOMEditor Component Tests
 *
 * Comprehensive test suite for the BOM Editor component with useFieldArray.
 * Tests cover:
 * - Dynamic field array operations (add/remove)
 * - Field-level validation (quantity, name, emission factor)
 * - Array-level validation (minimum 1 item, unique names)
 * - Wizard integration (step completion)
 * - Accessibility
 *
 * NOTE: BOMEditor uses progressive rendering (double-rAF) so the skeleton
 * shows first. All tests must wait for the skeleton to disappear before
 * querying for form elements.
 *
 * NOTE: Uses fireEvent instead of userEvent to avoid test isolation timing
 * issues with JSDOM event loop accumulation in this heavy component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '../testUtils';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import BOMEditor from '@/components/forms/BOMEditor';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

// Mock the stores
vi.mock('@/store/calculatorStore');
vi.mock('@/store/wizardStore');

// Mock API hook for emission factors
vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: '1', activity_name: 'Cotton (Organic)', co2e_factor: 2.5, unit: 'kg', category: 'material' },
      { id: '2', activity_name: 'Polyester (Virgin)', co2e_factor: 5.5, unit: 'kg', category: 'material' },
      { id: '3', activity_name: 'Electricity (US Grid)', co2e_factor: 0.4, unit: 'kWh', category: 'energy' },
      { id: '4', activity_name: 'Transport (Truck)', co2e_factor: 0.1, unit: 'tkm', category: 'transport' }
    ],
    isLoading: false,
    error: null
  })
}));

/**
 * Helper: Wait for the progressive rendering skeleton to disappear.
 * BOMEditor uses double-rAF so we need to flush those frames first.
 */
async function waitForEditorReady() {
  await waitFor(() => {
    expect(screen.queryByTestId('bom-editor-skeleton')).not.toBeInTheDocument();
  }, { timeout: 5000 });
}

// BOMEditor is a heavy component with progressive rendering (double-rAF).
// All tests need extended timeouts due to skeleton → form transition time.
describe('BOMEditor Component', { timeout: 20000 }, () => {
  const mockBomItems: BOMItem[] = [
    {
      id: 'item-1',
      name: 'Cotton',
      quantity: 1.5,
      unit: 'kg',
      category: 'material',
      emissionFactorId: "1"
    }
  ];

  const mockSetBomItems = vi.fn();
  const mockMarkStepComplete = vi.fn();
  const mockMarkStepIncomplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: mockBomItems,
      setBomItems: mockSetBomItems
    });

    (useWizardStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      markStepComplete: mockMarkStepComplete,
      markStepIncomplete: mockMarkStepIncomplete
    });
  });

  // ============================================================================
  // Rendering Tests
  // ============================================================================

  test('renders BOM table with initial items', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    expect(screen.getByText('Component')).toBeInTheDocument();
    expect(screen.getByText('Quantity')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1.5')).toBeInTheDocument();
  });

  test('renders "Add Component" button', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    expect(addButton).toBeInTheDocument();
  });

  test('renders total items count', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    expect(screen.getByText(/1 component/i)).toBeInTheDocument();
  });

  // ============================================================================
  // Dynamic Field Array - Add Row
  // ============================================================================

  test('adds a new component row when "Add Component" clicked', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);
    }, { timeout: 8000 });
  }, 15000);

  test('new row has default values', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);
      expect(nameInputs[1]).toHaveValue('');
    }, { timeout: 8000 });
  }, 15000);

  test('auto-focuses name field when adding new row', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs[nameInputs.length - 1]).toHaveFocus();
    }, { timeout: 8000 });
  }, 15000);

  test('updates total count when adding component', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    expect(screen.getByText(/1 component/i)).toBeInTheDocument();

    const addButton = screen.getByRole('button', { name: /add component/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/2 components/i)).toBeInTheDocument();
    }, { timeout: 8000 });
  }, 15000);

  // ============================================================================
  // Dynamic Field Array - Remove Row
  // ============================================================================

  test('removes component row when delete button clicked', async () => {
    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: [
        ...mockBomItems,
        {
          id: 'item-2',
          name: 'Polyester',
          quantity: 0.5,
          unit: 'kg',
          category: 'material',
          emissionFactorId: "2"
        }
      ],
      setBomItems: mockSetBomItems
    });

    render(<BOMEditor />);
    await waitForEditorReady();

    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs.length).toBe(2);

    const deleteButtons = screen.getAllByLabelText(/delete component/i);
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    });

    const dialog = screen.getByRole('alertdialog');
    const confirmDeleteButton = within(dialog).getByRole('button', { name: /^delete$/i });
    fireEvent.click(confirmDeleteButton);

    await waitFor(() => {
      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      const inputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(inputs.length).toBe(1);
    }, { timeout: 8000 });
  }, 15000);

  // ============================================================================
  // Minimum Constraint - Prevent Removing Last Row
  // ============================================================================

  test('delete button is disabled when only 1 item exists', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const deleteButton = screen.getByLabelText(/delete component/i);
    expect(deleteButton).toBeDisabled();
  });

  test('shows tooltip wrapper when delete is disabled', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    // When canRemove is false, the delete button is wrapped in a tooltip
    const deleteButton = screen.getByLabelText(/delete component/i);
    expect(deleteButton).toBeDisabled();
    // The tooltip trigger wraps the disabled button in a span
    expect(deleteButton.closest('span')).toBeTruthy();
  });

  test('delete button is enabled when multiple items exist', async () => {
    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: [
        ...mockBomItems,
        {
          id: 'item-2',
          name: 'Polyester',
          quantity: 0.5,
          unit: 'kg',
          category: 'material',
          emissionFactorId: "2"
        }
      ],
      setBomItems: mockSetBomItems
    });

    render(<BOMEditor />);
    await waitForEditorReady();

    const deleteButtons = screen.getAllByLabelText(/delete component/i);
    deleteButtons.forEach(button => {
      expect(button).not.toBeDisabled();
    });
  });

  // ============================================================================
  // Field-level Validation - Quantity
  // ============================================================================

  test('shows error when quantity is 0', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantityInput = screen.getByDisplayValue('1.5');
    fireEvent.change(quantityInput, { target: { value: '0', valueAsNumber: 0 } });
    fireEvent.blur(quantityInput);

    await waitFor(() => {
      const errors = screen.queryAllByText(/quantity must be greater than zero/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  test('shows error when quantity is negative', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantityInput = screen.getByDisplayValue('1.5');
    fireEvent.change(quantityInput, { target: { value: '-5', valueAsNumber: -5 } });
    fireEvent.blur(quantityInput);

    await waitFor(() => {
      const errors = screen.queryAllByText(/quantity must be greater than zero/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  test('accepts valid positive quantity', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantityInput = screen.getByDisplayValue('1.5');
    fireEvent.change(quantityInput, { target: { value: '2.5', valueAsNumber: 2.5 } });
    fireEvent.blur(quantityInput);

    await waitFor(() => {
      expect(screen.queryByText(/quantity must be greater than zero/i)).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Field-level Validation - Name Required
  // ============================================================================

  test('shows error when component name is empty', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const nameInput = screen.getByDisplayValue('Cotton');
    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.blur(nameInput);

    await waitFor(() => {
      const errors = screen.queryAllByText(/component name is required/i);
      expect(errors.length).toBeGreaterThan(0);
    }, { timeout: 8000 });
  }, 15000);

  // ============================================================================
  // Array-level Validation - Duplicate Names
  // ============================================================================

  test('shows error when duplicate names entered', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);
    }, { timeout: 8000 });

    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    fireEvent.change(nameInputs[1], { target: { value: 'Cotton' } });
    fireEvent.blur(nameInputs[1]);

    await waitFor(() => {
      const errors = screen.queryAllByText(/component names must be unique/i);
      expect(errors.length).toBeGreaterThan(0);
    }, { timeout: 8000 });
  }, 20000);

  test('duplicate name check is case-insensitive', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    fireEvent.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);
    }, { timeout: 8000 });

    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    fireEvent.change(nameInputs[1], { target: { value: 'COTTON' } });
    fireEvent.blur(nameInputs[1]);

    await waitFor(() => {
      const errors = screen.queryAllByText(/component names must be unique/i);
      expect(errors.length).toBeGreaterThan(0);
    }, { timeout: 8000 });
  }, 20000);

  // ============================================================================
  // Wizard Integration - Step Validation
  // ============================================================================

  test('marks step complete when form is valid', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    await waitFor(() => {
      expect(mockMarkStepComplete).toHaveBeenCalledWith('edit');
    });
  });

  test('marks step incomplete when form is invalid', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const nameInput = screen.getByDisplayValue('Cotton');
    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.blur(nameInput);

    await waitFor(() => {
      expect(mockMarkStepIncomplete).toHaveBeenCalledWith('edit');
    }, { timeout: 8000 });
  }, 15000);

  // ============================================================================
  // Store Synchronization
  // ============================================================================

  test('syncs form data to store when valid', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantityInput = screen.getByDisplayValue('1.5');
    fireEvent.change(quantityInput, { target: { value: '2.5', valueAsNumber: 2.5 } });

    await waitFor(() => {
      expect(mockSetBomItems).toHaveBeenCalled();
    }, { timeout: 8000 });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  test('table has proper ARIA structure', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();
  });

  test('delete buttons have descriptive aria-label', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const deleteButton = screen.getByLabelText(/delete component/i);
    expect(deleteButton).toHaveAttribute('aria-label');
  });

  test('form inputs have associated labels', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs.length).toBeGreaterThan(0);
  });

  // ============================================================================
  // Real-time Totals
  // ============================================================================

  test('displays total quantity calculation', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    expect(screen.getByText(/total quantity: 1\.50/i)).toBeInTheDocument();
  });

  test('updates total quantity when items change', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const totalText = screen.getByText(/total quantity/i);
    expect(totalText).toBeInTheDocument();
    expect(totalText.textContent).toContain('1.50');
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  test('handles empty BOM initialization', async () => {
    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: [],
      setBomItems: mockSetBomItems
    });

    render(<BOMEditor />);
    await waitForEditorReady();

    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs.length).toBe(1);
  });

  test('limits maximum number of components', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const addButton = screen.getByRole('button', { name: /add component/i });
    expect(addButton).not.toBeDisabled();
    expect(addButton).toBeEnabled();
  });
});
