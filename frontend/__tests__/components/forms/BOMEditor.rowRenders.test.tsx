/**
 * BOMEditor row re-renders (TASK-FE-FIX-003, issue #133)
 *
 * Editing one BOM row must re-render that row only. Before the fix, every BOMEditorForm
 * render re-rendered all rows: BOMEditor passed each row a new inline onRemove, so
 * React.memo on BOMTableRow never skipped one. Opening the edit step with a 12-row BOM
 * blocked the main thread for 5.4 s on the dev server (0.4 s in a production build), long
 * enough under load for the Calculate button to stay disabled past the e2e timeouts.
 *
 * The rows read their own values, so they must keep updating once the parent stops
 * re-rendering them: the edited row's CO2e and the delete dialog's name stay current.
 *
 * A row renders its SourceBadge on every render, so a counting SourceBadge stub records
 * which rows rendered. Each row's factor has its own data_source code.
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen, waitFor, fireEvent, within } from '../../testUtils';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import BOMEditor from '@/components/forms/BOMEditor';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

const ROW_COUNT = 6;

const FACTORS = Array.from({ length: ROW_COUNT }, (_, i) => ({
  id: `ef-${i}`,
  activity_name: `Factor ${i}`,
  co2e_factor: i + 1,
  unit: 'kg',
  category: 'material',
  data_source: `SRC-${i}`,
}));

vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({ data: FACTORS, isLoading: false, error: null }),
}));

// Desktop layout (table rows)
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

// Records the source code of every SourceBadge render, i.e. which rows rendered
const badgeRenders: string[] = [];
vi.mock('@/components/attribution/SourceBadge', () => {
  const SourceBadge = ({ sourceCode }: { sourceCode: string }) => {
    badgeRenders.push(sourceCode);
    return <span data-testid="source-badge">{sourceCode}</span>;
  };
  return { SourceBadge, default: SourceBadge };
});

const ITEMS: BOMItem[] = FACTORS.map((factor, i) => ({
  id: `item-${i}`,
  name: `Component ${i}`,
  quantity: 1,
  unit: 'kg',
  category: 'material',
  emissionFactorId: factor.id,
}));

/** Wait for the skeleton to go and for the form's first validation to settle */
async function waitForEditorReady() {
  await waitFor(() => {
    expect(screen.queryByRole('status', { name: 'Loading bill of materials' })).not.toBeInTheDocument();
  }, { timeout: 5000 });
  await waitFor(() => {
    expect(useWizardStore.getState().completedSteps).toContain('edit');
  }, { timeout: 5000 });
}

/** Table row (tr) holding the quantity input of BOM row `index` */
function rowOf(index: number): HTMLElement {
  const quantity = screen.getAllByRole('spinbutton', { name: 'Quantity' })[index];
  return quantity.closest('tr') as HTMLElement;
}

/** Let pending validation and store syncs finish, then start counting afresh */
async function settleAndResetCount() {
  await new Promise((resolve) => setTimeout(resolve, 100));
  badgeRenders.length = 0;
}

describe('BOMEditor row re-renders (TASK-FE-FIX-003)', { timeout: 20000 }, () => {
  beforeEach(() => {
    badgeRenders.length = 0;
    useCalculatorStore.setState({ bomItems: ITEMS, selectedProductId: 'product-1' });
    useWizardStore.setState({ currentStep: 'edit', completedSteps: ['select'] });
  });

  test('typing a quantity in one row re-renders that row only', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();
    await settleAndResetCount();

    fireEvent.change(screen.getAllByRole('spinbutton', { name: 'Quantity' })[0], { target: { value: '3' } });
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(3));
    await new Promise((resolve) => setTimeout(resolve, 100));

    const otherRows = badgeRenders.filter((code) => code !== 'SRC-0');
    expect(otherRows).toEqual([]);
  });

  test('the edited row still shows its new CO2e', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    // Row 2: factor 3 kg CO2e/kg, quantity 1 -> 3.00, then quantity 4 -> 12.00
    expect(within(rowOf(2)).getByText('3.00')).toBeInTheDocument();
    fireEvent.change(screen.getAllByRole('spinbutton', { name: 'Quantity' })[2], { target: { value: '4' } });
    await waitFor(() => expect(within(rowOf(2)).getByText('12.00')).toBeInTheDocument());
  });

  test('the increase button re-renders its own row only and updates its CO2e', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();
    await settleAndResetCount();

    // Row 4: factor 5 kg CO2e/kg, quantity 1 -> 2 gives 10.00
    fireEvent.click(within(rowOf(4)).getByRole('button', { name: 'Increase quantity' }));
    await waitFor(() => expect(within(rowOf(4)).getByText('10.00')).toBeInTheDocument());
    await new Promise((resolve) => setTimeout(resolve, 100));

    const otherRows = badgeRenders.filter((code) => code !== 'SRC-4');
    expect(otherRows).toEqual([]);
  });

  test('the delete dialog names the row as it is now, after a rename', async () => {
    render(<BOMEditor />);
    await waitForEditorReady();

    const name = within(rowOf(1)).getByRole('textbox', { name: 'Component name' });
    fireEvent.change(name, { target: { value: 'Renamed part' } });
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[1].name).toBe('Renamed part'));

    fireEvent.click(within(rowOf(1)).getByRole('button', { name: 'Delete component' }));
    const dialog = await screen.findByRole('alertdialog');
    expect(within(dialog).getByText(/Renamed part/)).toBeInTheDocument();
  });
});
