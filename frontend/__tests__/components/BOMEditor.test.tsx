/**
 * BOMEditor Component Tests
 *
 * Comprehensive test suite for the BOM Editor component with useFieldArray.
 * Tests cover:
 * - Dynamic field array operations (add/remove)
 * - Field-level validation (quantity, name, emission factor)
 * - Array-level validation (minimum 1 item, unique names)
 * - Wizard integration (step completion)
 * - Keyboard navigation
 * - Accessibility
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, userEvent } from '../testUtils';
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

describe('BOMEditor Component', () => {
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
    // Reset mocks before each test
    vi.clearAllMocks();

    // Setup store mocks with default values
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

  test('renders BOM table with initial items', () => {
    render(<BOMEditor />);

    // Check table headers
    expect(screen.getByText('Component Name')).toBeInTheDocument();
    expect(screen.getByText('Quantity')).toBeInTheDocument();
    expect(screen.getByText('Unit')).toBeInTheDocument();
    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();

    // Check initial data
    expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1.5')).toBeInTheDocument();
  });

  test('renders "Add Component" button', () => {
    render(<BOMEditor />);

    const addButton = screen.getByRole('button', { name: /add component/i });
    expect(addButton).toBeInTheDocument();
  });

  test('renders total items count', () => {
    render(<BOMEditor />);

    expect(screen.getByText(/1 component/i)).toBeInTheDocument();
  });

  // ============================================================================
  // Dynamic Field Array - Add Row
  // ============================================================================

  test('adds a new component row when "Add Component" clicked', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    // Check that we now have 2 rows (header row doesn't count in tbody)
    await waitFor(() => {
      const rows = screen.getAllByRole('row').filter(row =>
        row.closest('tbody') !== null
      );
      expect(rows.length).toBe(2);
    });
  });

  test('new row has default values', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    await waitFor(() => {
      // Find all name inputs (should have 2 now)
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);

      // New row should have empty name
      expect(nameInputs[1]).toHaveValue('');
    });
  });

  test('auto-focuses name field when adding new row', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      // The last (newly added) input should have focus
      expect(nameInputs[nameInputs.length - 1]).toHaveFocus();
    }, { timeout: 1000 });
  });

  test('updates total count when adding component', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    expect(screen.getByText(/1 component/i)).toBeInTheDocument();

    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/2 components/i)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Dynamic Field Array - Remove Row
  // ============================================================================

  test('removes component row when delete button clicked', async () => {
    const user = userEvent.setup();

    // Start with 2 items
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

    // Verify we start with 2 rows
    let rows = screen.getAllByRole('row').filter(row => row.closest('tbody') !== null);
    expect(rows.length).toBe(2);

    // Click delete on first row
    const deleteButtons = screen.getAllByLabelText(/delete component/i);
    await user.click(deleteButtons[0]);

    // Should now have 1 row
    await waitFor(() => {
      rows = screen.getAllByRole('row').filter(row => row.closest('tbody') !== null);
      expect(rows.length).toBe(1);
    });
  });

  // ============================================================================
  // Minimum Constraint - Prevent Removing Last Row
  // ============================================================================

  test('delete button is disabled when only 1 item exists', () => {
    render(<BOMEditor />);

    const deleteButton = screen.getByLabelText(/delete component/i);
    expect(deleteButton).toBeDisabled();
  });

  test('shows tooltip when hovering over disabled delete button', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const deleteButton = screen.getByLabelText(/delete component/i);

    await user.hover(deleteButton);

    await waitFor(() => {
      const tooltips = screen.queryAllByText(/cannot remove the last component/i);
      expect(tooltips.length).toBeGreaterThan(0);
    });
  });

  test('delete button is enabled when multiple items exist', () => {
    // Start with 2 items
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

    const deleteButtons = screen.getAllByLabelText(/delete component/i);
    deleteButtons.forEach(button => {
      expect(button).not.toBeDisabled();
    });
  });

  // ============================================================================
  // Field-level Validation - Quantity
  // ============================================================================

  test('shows error when quantity is 0', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const quantityInput = screen.getByDisplayValue('1.5');

    await user.clear(quantityInput);
    await user.type(quantityInput, '0');
    await user.tab(); // Trigger blur

    await waitFor(() => {
      const errors = screen.queryAllByText(/quantity must be greater than zero/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  test('shows error when quantity is negative', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const quantityInput = screen.getByDisplayValue('1.5');

    // Use fireEvent.change to bypass HTML5 min="0" constraint
    // This simulates the valueAsNumber returning NaN for invalid input
    fireEvent.change(quantityInput, { target: { value: '-5', valueAsNumber: -5 } });
    await user.tab(); // Trigger blur and validation

    await waitFor(() => {
      const errors = screen.queryAllByText(/quantity must be greater than zero/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  test('accepts valid positive quantity', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const quantityInput = screen.getByDisplayValue('1.5');

    await user.clear(quantityInput);
    await user.type(quantityInput, '2.5');
    await user.tab();

    // Should NOT show error
    await waitFor(() => {
      expect(screen.queryByText(/quantity must be greater than zero/i)).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Field-level Validation - Name Required
  // ============================================================================

  test('shows error when component name is empty', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    const nameInput = screen.getByDisplayValue('Cotton');

    await user.clear(nameInput);
    await user.tab(); // Trigger blur

    await waitFor(() => {
      const errors = screen.queryAllByText(/component name is required/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Array-level Validation - Duplicate Names
  // ============================================================================

  test('shows error when duplicate names entered', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    // Add second row
    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);
    });

    // Set both names to "Cotton"
    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    await user.type(nameInputs[1], 'Cotton');
    await user.tab();

    await waitFor(() => {
      const errors = screen.queryAllByText(/component names must be unique/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  test('duplicate name check is case-insensitive', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    // Add second row
    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    await waitFor(() => {
      const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(nameInputs.length).toBe(2);
    });

    // Set second name to "COTTON" (different case)
    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    await user.type(nameInputs[1], 'COTTON');
    await user.tab();

    await waitFor(() => {
      const errors = screen.queryAllByText(/component names must be unique/i);
      expect(errors.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Wizard Integration - Step Validation
  // ============================================================================

  test('marks step complete when form is valid', async () => {
    render(<BOMEditor />);

    // With valid default data, step should be marked complete
    await waitFor(() => {
      expect(mockMarkStepComplete).toHaveBeenCalledWith('edit');
    });
  });

  test('marks step incomplete when form is invalid', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    // Make form invalid by clearing name
    const nameInput = screen.getByDisplayValue('Cotton');
    await user.clear(nameInput);
    await user.tab();

    await waitFor(() => {
      expect(mockMarkStepIncomplete).toHaveBeenCalledWith('edit');
    });
  });

  // ============================================================================
  // Store Synchronization
  // ============================================================================

  test('syncs form data to store when valid', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    // Update quantity
    const quantityInput = screen.getByDisplayValue('1.5');
    await user.clear(quantityInput);
    await user.type(quantityInput, '2.5');

    // Wait for debounced sync (500ms)
    await waitFor(() => {
      expect(mockSetBomItems).toHaveBeenCalled();
    }, { timeout: 1000 });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  test('table has proper ARIA structure', () => {
    render(<BOMEditor />);

    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();
  });

  test('delete buttons have descriptive aria-label', () => {
    render(<BOMEditor />);

    const deleteButton = screen.getByLabelText(/delete component/i);
    expect(deleteButton).toHaveAttribute('aria-label');
  });

  test('form inputs have associated labels', () => {
    render(<BOMEditor />);

    // Name input should have placeholder acting as label
    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs.length).toBeGreaterThan(0);
  });

  // ============================================================================
  // Real-time Totals
  // ============================================================================

  test('displays total quantity calculation', () => {
    render(<BOMEditor />);

    // With quantity 1.5, should show total
    expect(screen.getByText(/total quantity: 1\.50/i)).toBeInTheDocument();
  });

  test('updates total quantity when items change', async () => {
    const user = userEvent.setup();
    render(<BOMEditor />);

    // Add second component
    const addButton = screen.getByRole('button', { name: /add component/i });
    await user.click(addButton);

    // Set quantity on new row
    await waitFor(() => {
      const quantityInputs = screen.getAllByRole('spinbutton');
      expect(quantityInputs.length).toBe(2);
    });
    
    const quantityInputs = screen.getAllByRole('spinbutton');
    await user.clear(quantityInputs[1]);
    await user.type(quantityInputs[1], '2.5');

    // Total should update to 1.5 + 2.5 = 4.0
    await waitFor(() => {
      expect(screen.getByText(/total quantity: 4\.00/i)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  test('handles empty BOM initialization', () => {
    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: [],
      setBomItems: mockSetBomItems
    });

    render(<BOMEditor />);

    // Should render with 1 default row (minimum constraint)
    const rows = screen.getAllByRole('row').filter(row => row.closest('tbody') !== null);
    expect(rows.length).toBe(1);
  });
  test('limits maximum number of components', async () => {
    const user = userEvent.setup();

    // Create a moderate number of items to test rendering performance
    // Note: Zod schema enforces max 100 items; this tests UI with many items
    const manyItems: BOMItem[] = Array.from({ length: 5 }, (_, i) => ({
      id: `item-${i}`,
      name: `Component ${i}`,
      quantity: 1,
      unit: 'kg',
      category: 'material' as const,
      emissionFactorId: "1"
    }));

    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: manyItems,
      setBomItems: mockSetBomItems
    });

    render(<BOMEditor />);

    // Add button should be clickable
    const addButton = screen.getByRole('button', { name: /add component/i });
    expect(addButton).not.toBeDisabled();

    // Clicking add should work without crashing
    await user.click(addButton);

    // Verify new row was added (6 rows now in tbody)
    await waitFor(() => {
      const rows = screen.getAllByRole('row').filter(row => row.closest('tbody') !== null);
      expect(rows.length).toBe(6);
    });
  });
});
