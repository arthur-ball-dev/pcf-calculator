/**
 * BOMEditor quantity-zero regression (TASK-FE-FIX-002)
 *
 * Entering 0 in a quantity field must show the validation error and keep the editor
 * responsive. Before the fix the editor locked up: the form's internal items array was
 * handed to the calculator store, immer froze it, and the next write into the form threw
 * "Cannot assign to read only property '0' of object '[object Array]'".
 *
 * These tests use the real calculator store (not a mock) because the freeze is the bug.
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '../../testUtils';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import BOMEditor from '@/components/forms/BOMEditor';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

// Mock API hook for emission factors
vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: '1', activity_name: 'Cotton (Organic)', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
    ],
    isLoading: false,
    error: null,
  }),
}));

// Desktop layout (table rows with the quantity input)
vi.mock('@/hooks/useBreakpoints', () => ({
  useBreakpoints: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    breakpoint: 'lg',
    width: 1200,
  }),
}));

// JSDOM has no layout; the editor is below the virtualization threshold anyway
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({ count, estimateSize }: { count: number; estimateSize: () => number }) => ({
    getVirtualItems: () =>
      Array.from({ length: count }, (_, i) => ({ index: i, start: i * estimateSize(), size: estimateSize(), key: i })),
    getTotalSize: () => count * estimateSize(),
    scrollToIndex: vi.fn(),
    measure: vi.fn(),
  }),
}));

const ITEM: BOMItem = {
  id: 'item-1',
  name: 'Cotton (Organic)',
  quantity: 2,
  unit: 'kg',
  category: 'material',
  emissionFactorId: '1',
};

const QUANTITY_ERROR = 'Quantity must be greater than zero';

/**
 * Wait for the skeleton to go and for the form's first validation to settle
 * (the editor marks the step complete once the initial BOM validates).
 */
async function waitForEditorReady() {
  await waitFor(() => {
    expect(screen.queryByRole('status', { name: 'Loading bill of materials' })).not.toBeInTheDocument();
  }, { timeout: 5000 });
  await waitFor(() => {
    expect(useWizardStore.getState().completedSteps).toContain('edit');
  }, { timeout: 5000 });
}

describe('BOMEditor quantity zero (TASK-FE-FIX-002)', () => {
  const pageErrors: string[] = [];
  const onWindowError = (event: ErrorEvent) => {
    pageErrors.push(String(event.error ?? event.message));
    event.preventDefault();
  };

  beforeEach(() => {
    pageErrors.length = 0;
    window.addEventListener('error', onWindowError);
    useCalculatorStore.setState({ bomItems: [ITEM], selectedProductId: 'product-1' });
    useWizardStore.setState({ currentStep: 'edit', completedSteps: ['select'] });
  });

  afterEach(() => {
    window.removeEventListener('error', onWindowError);
  });

  test('typing 0 shows the validation error and the next keystroke still works', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantity = screen.getByRole('spinbutton', { name: 'Quantity' }) as HTMLInputElement;
    expect(quantity.value).toBe('2');

    fireEvent.change(quantity, { target: { value: '0' } });
    await screen.findByText(QUANTITY_ERROR);

    fireEvent.change(quantity, { target: { value: '5' } });
    await waitFor(() => expect(quantity.value).toBe('5'));
    await waitFor(() => expect(screen.queryByText(QUANTITY_ERROR)).not.toBeInTheDocument());
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(5));

    expect(pageErrors).toEqual([]);
  });

  test('typing 0 then using the increase button still works', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantity = screen.getByRole('spinbutton', { name: 'Quantity' }) as HTMLInputElement;
    fireEvent.change(quantity, { target: { value: '0' } });
    await screen.findByText(QUANTITY_ERROR);

    fireEvent.click(screen.getByRole('button', { name: 'Increase quantity' }));
    await waitFor(() => expect(quantity.value).toBe('1'));
    await waitFor(() => expect(screen.queryByText(QUANTITY_ERROR)).not.toBeInTheDocument());

    expect(pageErrors).toEqual([]);
  });

  test('the store never receives the form\'s own items array', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const quantity = screen.getByRole('spinbutton', { name: 'Quantity' }) as HTMLInputElement;
    fireEvent.change(quantity, { target: { value: '3' } });
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(3));
    const storedItems = useCalculatorStore.getState().bomItems;

    // A second edit must still be possible after the store froze what it was given.
    fireEvent.change(quantity, { target: { value: '4' } });
    await waitFor(() => expect(quantity.value).toBe('4'));
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(4));
    expect(useCalculatorStore.getState().bomItems).not.toBe(storedItems);

    expect(pageErrors).toEqual([]);
  });
});
