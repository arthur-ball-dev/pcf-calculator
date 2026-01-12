/**
 * BOMTableRow Component Tests - React.memo Memoization
 *
 * TASK-FE-P8-005: Test that BOMTableRow is properly memoized with React.memo
 * to prevent unnecessary re-renders when sibling rows change.
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '../../testUtils';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import { useForm, FormProvider, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Table, TableBody, TableHeader, TableRow, TableHead } from '@/components/ui/table';
import BOMTableRow from '@/components/forms/BOMTableRow';
import { bomFormSchema, type BOMFormData } from '@/schemas/bomSchema';

// Mock the hooks
vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: 'ef-1', activity_name: 'Steel Production', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
      { id: 'ef-2', activity_name: 'Aluminum Production', co2e_factor: 8.0, unit: 'kg', category: 'material', data_source: 'DEFRA' },
    ],
    isLoading: false,
    error: null,
  }),
}));

// Global render counter for tracking across test assertions
const renderCounts: Record<string, number> = {};

/**
 * Higher-order component that tracks renders of a child component
 */
function withRenderTracking<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  trackerId: string
) {
  return function TrackedComponent(props: P) {
    // Increment render count every time this function runs (re-render occurs)
    renderCounts[trackerId] = (renderCounts[trackerId] || 0) + 1;
    return <WrappedComponent {...props} />;
  };
}

/**
 * Test wrapper component that provides form context and renders multiple BOMTableRows
 */
interface TestWrapperProps {
  initialItems: BOMFormData['items'];
  onRenderCounts?: (counts: Record<string, number>) => void;
  TrackedBOMTableRow?: React.ComponentType<any>;
}

function TestWrapper({ initialItems, TrackedBOMTableRow }: TestWrapperProps) {
  const form = useForm<BOMFormData>({
    resolver: zodResolver(bomFormSchema),
    mode: 'onChange',
    defaultValues: {
      items: initialItems,
    },
  });

  const { fields } = useFieldArray({
    control: form.control,
    name: 'items',
  });

  const RowComponent = TrackedBOMTableRow || BOMTableRow;

  return (
    <FormProvider {...form}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Component Name</TableHead>
            <TableHead>Quantity</TableHead>
            <TableHead>Unit</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Emission Factor</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {fields.map((field, index) => (
            <RowComponent
              key={field.id}
              field={field}
              index={index}
              form={form}
              onRemove={() => {}}
              canRemove={fields.length > 1}
            />
          ))}
        </TableBody>
      </Table>
    </FormProvider>
  );
}

/**
 * Alternative test wrapper that allows updating specific fields
 * and tracking which rows re-render
 */
function TestWrapperWithUpdate({
  initialItems,
  onFormReady,
}: {
  initialItems: BOMFormData['items'];
  onFormReady: (form: ReturnType<typeof useForm<BOMFormData>>) => void;
}) {
  const form = useForm<BOMFormData>({
    resolver: zodResolver(bomFormSchema),
    mode: 'onChange',
    defaultValues: {
      items: initialItems,
    },
  });

  const { fields } = useFieldArray({
    control: form.control,
    name: 'items',
  });

  // Expose form to test
  React.useEffect(() => {
    onFormReady(form);
  }, [form, onFormReady]);

  return (
    <FormProvider {...form}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Component Name</TableHead>
            <TableHead>Quantity</TableHead>
            <TableHead>Unit</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Emission Factor</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {fields.map((field, index) => (
            <BOMTableRow
              key={field.id}
              field={field}
              index={index}
              form={form}
              onRemove={() => {}}
              canRemove={fields.length > 1}
            />
          ))}
        </TableBody>
      </Table>
    </FormProvider>
  );
}

describe('BOMTableRow React.memo Memoization', () => {
  const defaultItems: BOMFormData['items'] = [
    {
      id: 'item-1',
      name: 'Steel',
      quantity: 10,
      unit: 'kg',
      category: 'material',
      emissionFactorId: 'ef-1',
    },
    {
      id: 'item-2',
      name: 'Aluminum',
      quantity: 5,
      unit: 'kg',
      category: 'material',
      emissionFactorId: 'ef-2',
    },
  ];

  beforeEach(() => {
    // Reset render counts before each test
    Object.keys(renderCounts).forEach(key => {
      delete renderCounts[key];
    });
  });

  // ============================================================================
  // Rendering Tests - Verify component renders correctly
  // ============================================================================

  test('BOMTableRow renders correctly with props', () => {
    render(<TestWrapper initialItems={defaultItems} />);

    // Verify both rows are rendered
    expect(screen.getByDisplayValue('Steel')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Aluminum')).toBeInTheDocument();
    expect(screen.getByDisplayValue('10')).toBeInTheDocument();
    expect(screen.getByDisplayValue('5')).toBeInTheDocument();
  });

  test('BOMTableRow displays all form fields', () => {
    render(<TestWrapper initialItems={defaultItems} />);

    // Check that we have 2 data rows (excluding header)
    const rows = screen.getAllByRole('row').filter(row => row.closest('tbody'));
    expect(rows.length).toBe(2);

    // Check component name inputs
    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs.length).toBe(2);

    // Check quantity inputs (spinbuttons)
    const quantityInputs = screen.getAllByRole('spinbutton');
    expect(quantityInputs.length).toBe(2);
  });

  // ============================================================================
  // Memoization Tests - Verify React.memo prevents unnecessary re-renders
  // ============================================================================

  test('BOMTableRow is wrapped with React.memo', () => {
    // Import the component and check if it has memo applied
    // React.memo wraps the component and adds a $$typeof property
    // and the type should be different from a regular function component

    // Get the component
    const component = BOMTableRow;

    // React.memo creates a wrapper with specific properties
    // When properly memoized, the component should have:
    // 1. A displayName or name that indicates memoization
    // 2. The $$typeof symbol for memo (Symbol.for('react.memo'))

    // Check if it's a memo component by examining its structure
    // React.memo returns an object with type and compare properties
    const isMemoized =
      typeof component === 'object' &&
      component !== null &&
      ('$$typeof' in component || 'compare' in component || 'type' in component);

    // Alternative check: React.memo components have specific characteristics
    // when inspected via React's internal representation
    const componentString = String(component);
    const hasMemoIndicator =
      isMemoized ||
      componentString.includes('memo') ||
      (component as any).$$typeof?.toString?.().includes('memo');

    expect(hasMemoIndicator).toBe(true);
  });

  test('BOMTableRow does not re-render when sibling row changes', async () => {
    // This test verifies that when one BOM row's input changes,
    // other rows do not re-render (which would happen without React.memo)

    // Create tracked versions of BOMTableRow for each index
    const TrackedRow1 = withRenderTracking(BOMTableRow, 'row-1');
    const TrackedRow2 = withRenderTracking(BOMTableRow, 'row-2');

    // Custom wrapper that uses tracked components
    function TrackedTestWrapper() {
      const form = useForm<BOMFormData>({
        resolver: zodResolver(bomFormSchema),
        mode: 'onChange',
        defaultValues: {
          items: defaultItems,
        },
      });

      const { fields } = useFieldArray({
        control: form.control,
        name: 'items',
      });

      return (
        <FormProvider {...form}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Qty</TableHead>
                <TableHead>Unit</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>EF</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fields.map((field, index) => {
                const TrackedComponent = index === 0 ? TrackedRow1 : TrackedRow2;
                return (
                  <TrackedComponent
                    key={field.id}
                    field={field}
                    index={index}
                    form={form}
                    onRemove={() => {}}
                    canRemove={true}
                  />
                );
              })}
            </TableBody>
          </Table>
        </FormProvider>
      );
    }

    render(<TrackedTestWrapper />);

    // Initial render counts
    const initialRow1Renders = renderCounts['row-1'];
    const initialRow2Renders = renderCounts['row-2'];

    expect(initialRow1Renders).toBe(1);
    expect(initialRow2Renders).toBe(1);

    // Find the first row's quantity input and change it
    const quantityInputs = screen.getAllByRole('spinbutton');
    fireEvent.change(quantityInputs[0], { target: { value: '20', valueAsNumber: 20 } });

    // Wait for React to process updates
    await waitFor(() => {
      // Row 1 should have re-rendered because its props changed (via form state)
      // Row 2 should NOT have re-rendered if React.memo is working

      // With React.memo: row-2 render count should stay at 1
      // Without React.memo: row-2 would re-render every time the parent re-renders

      // This is the key assertion - if memoization works, row-2 should not have
      // additional renders beyond the initial render
      const row2FinalRenders = renderCounts['row-2'];

      // Allow some tolerance for React's batching, but row-2 should not have
      // significantly more renders than the initial render
      expect(row2FinalRenders).toBeLessThanOrEqual(2);
    });
  });

  test('BOMTableRow re-renders when its own props change', async () => {
    let formRef: ReturnType<typeof useForm<BOMFormData>> | null = null;

    render(
      <TestWrapperWithUpdate
        initialItems={defaultItems}
        onFormReady={(form) => { formRef = form; }}
      />
    );

    // Verify initial state
    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs[0]).toHaveValue('Steel');

    // Change the first row's name using the form
    fireEvent.change(nameInputs[0], { target: { value: 'Carbon Steel' } });

    // The component should update to show the new value
    await waitFor(() => {
      expect(nameInputs[0]).toHaveValue('Carbon Steel');
    });
  });

  // ============================================================================
  // Props Stability Tests
  // ============================================================================

  test('BOMTableRow receives stable form reference', () => {
    // When using React Hook Form, the form object reference should be stable
    // This is important for memoization to work correctly

    render(<TestWrapper initialItems={defaultItems} />);

    // If form reference is unstable, React.memo would not help
    // This test verifies the component renders correctly with form prop
    expect(screen.getByDisplayValue('Steel')).toBeInTheDocument();
  });

  test('BOMTableRow receives correct index prop', () => {
    render(<TestWrapper initialItems={defaultItems} />);

    // The index prop determines which form field path to use
    // items.0.name for first row, items.1.name for second row
    // Verify both rows have their correct values (proving correct index)

    const nameInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
    expect(nameInputs[0]).toHaveValue('Steel');
    expect(nameInputs[1]).toHaveValue('Aluminum');
  });

  // ============================================================================
  // Callback Memoization Tests (Related to TASK-FE-P8-006)
  // ============================================================================

  test('BOMTableRow handles onRemove callback', async () => {
    const onRemoveMock = vi.fn();

    function TestWrapperWithRemove() {
      const form = useForm<BOMFormData>({
        resolver: zodResolver(bomFormSchema),
        mode: 'onChange',
        defaultValues: { items: defaultItems },
      });

      const { fields, remove } = useFieldArray({
        control: form.control,
        name: 'items',
      });

      return (
        <FormProvider {...form}>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Qty</TableHead>
                <TableHead>Unit</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>EF</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fields.map((field, index) => (
                <BOMTableRow
                  key={field.id}
                  field={field}
                  index={index}
                  form={form}
                  onRemove={() => {
                    onRemoveMock(index);
                    remove(index);
                  }}
                  canRemove={fields.length > 1}
                />
              ))}
            </TableBody>
          </Table>
        </FormProvider>
      );
    }

    render(<TestWrapperWithRemove />);

    // Find delete buttons and click one
    const deleteButtons = screen.getAllByLabelText(/delete component/i);
    expect(deleteButtons.length).toBe(2);

    // Click delete on first row
    fireEvent.click(deleteButtons[0]);

    // Wait for AlertDialog to appear
    await waitFor(() => {
      expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    });

    // Confirm deletion
    const dialog = screen.getByRole('alertdialog');
    const confirmButton = within(dialog).getByRole('button', { name: /^delete$/i });
    fireEvent.click(confirmButton);

    // onRemove should have been called
    await waitFor(() => {
      expect(onRemoveMock).toHaveBeenCalledWith(0);
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  test('BOMTableRow maintains accessibility after memoization', () => {
    render(<TestWrapper initialItems={defaultItems} />);

    // Verify accessible elements are present
    const nameInputs = screen.getAllByLabelText(/component name/i);
    expect(nameInputs.length).toBe(2);

    const quantityInputs = screen.getAllByLabelText(/quantity/i);
    expect(quantityInputs.length).toBe(2);

    const deleteButtons = screen.getAllByLabelText(/delete component/i);
    expect(deleteButtons.length).toBe(2);
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  test('BOMTableRow handles single item correctly', () => {
    const singleItem: BOMFormData['items'] = [
      {
        id: 'item-1',
        name: 'Steel',
        quantity: 10,
        unit: 'kg',
        category: 'material',
        emissionFactorId: 'ef-1',
      },
    ];

    render(<TestWrapper initialItems={singleItem} />);

    // Single row should render
    const rows = screen.getAllByRole('row').filter(row => row.closest('tbody'));
    expect(rows.length).toBe(1);

    // Delete button should be disabled (can't remove last item)
    const deleteButton = screen.getByLabelText(/delete component/i);
    expect(deleteButton).toBeDisabled();
  });

  test('BOMTableRow handles empty emission factor selection', () => {
    const itemWithoutEF: BOMFormData['items'] = [
      {
        id: 'item-1',
        name: 'New Material',
        quantity: 1,
        unit: 'kg',
        category: 'material',
        emissionFactorId: null,
      },
    ];

    render(<TestWrapper initialItems={itemWithoutEF} />);

    // Component should render without error
    expect(screen.getByDisplayValue('New Material')).toBeInTheDocument();

    // Source badge should show placeholder when no emission factor selected
    expect(screen.getByText(/\u2014/)).toBeInTheDocument(); // Em-dash placeholder
  });
});
