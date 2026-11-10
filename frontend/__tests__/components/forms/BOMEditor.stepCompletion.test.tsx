/**
 * BOM edit step completion (TASK-FE-FIX-004, issue #133)
 *
 * The edit step's completion has one owner: the BOM editor's form validation.
 *
 * Before the fix, two owners raced. CalculationWizard marked the step complete from its own
 * simple BOM check as soon as the step opened, then BOMEditor mounted with react-hook-form's
 * initial isValid=false and marked it incomplete, then marked it complete again once the async
 * validation finished. The Calculate button went enabled -> disabled -> enabled; a click in the
 * disabled window was lost (seen under CPU load in wizardFlow and the e2e suite). The wizard's
 * simple check also accepted BOMs the form rejects, such as duplicate component names.
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen, waitFor } from '../../testUtils';
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import BOMEditor from '@/components/forms/BOMEditor';
import CalculationWizard from '@/components/calculator/CalculationWizard';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: 'ef-1', activity_name: 'Cotton (Organic)', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
      { id: 'ef-2', activity_name: 'Polyester (Virgin)', co2e_factor: 5.5, unit: 'kg', category: 'material', data_source: 'EPA' },
    ],
    isLoading: false,
    error: null,
  }),
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

const VALID_ITEMS: BOMItem[] = [
  { id: 'item-1', name: 'Cotton', quantity: 1.5, unit: 'kg', category: 'material', emissionFactorId: 'ef-1' },
  { id: 'item-2', name: 'Polyester', quantity: 0.5, unit: 'kg', category: 'material', emissionFactorId: 'ef-2' },
];

// Passes the old wizard check (names present, quantities > 0) but not the form: names must be unique
const DUPLICATE_NAME_ITEMS: BOMItem[] = [
  { id: 'item-1', name: 'Cotton', quantity: 1.5, unit: 'kg', category: 'material', emissionFactorId: 'ef-1' },
  { id: 'item-2', name: 'cotton', quantity: 0.5, unit: 'kg', category: 'material', emissionFactorId: 'ef-2' },
];

async function waitForEditorReady() {
  await waitFor(() => {
    expect(screen.queryByRole('status', { name: 'Loading bill of materials' })).not.toBeInTheDocument();
  }, { timeout: 5000 });
}

describe('BOM edit step completion (TASK-FE-FIX-004)', { timeout: 20000 }, () => {
  let canProceedHistory: boolean[] = [];
  let unsubscribe: () => void = () => {};

  beforeEach(() => {
    canProceedHistory = [];
  });

  afterEach(() => {
    unsubscribe();
  });

  test('a valid BOM never makes the step incomplete on the way to complete', async () => {
    useCalculatorStore.setState({ bomItems: VALID_ITEMS, selectedProductId: 'product-1' });
    // As setStep('edit') leaves it: on the edit step, canProceed true, edit not yet complete
    useWizardStore.setState({ currentStep: 'edit', completedSteps: ['select'], canProceed: true });
    unsubscribe = useWizardStore.subscribe((state) => canProceedHistory.push(state.canProceed));

    render(<BOMEditor />);
    await waitForEditorReady();
    await waitFor(() => expect(useWizardStore.getState().completedSteps).toContain('edit'));
    await new Promise((resolve) => setTimeout(resolve, 200));

    expect(canProceedHistory).not.toContain(false);
    expect(useWizardStore.getState().canProceed).toBe(true);
  });

  test('the wizard does not complete the edit step when the form rejects the BOM', async () => {
    useCalculatorStore.setState({ bomItems: DUPLICATE_NAME_ITEMS, selectedProductId: 'product-1' });
    useWizardStore.setState({ currentStep: 'edit', completedSteps: ['select'], canProceed: true });
    const editCompleteHistory: boolean[] = [];
    unsubscribe = useWizardStore.subscribe((state) => editCompleteHistory.push(state.completedSteps.includes('edit')));

    render(<CalculationWizard />);
    await waitForEditorReady();
    // Validation errors only show after an edit, so give validation time to settle instead
    await screen.findByRole('button', { name: 'Calculate carbon footprint' });
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Not even briefly: a Calculate click in that window would submit a BOM the form rejects
    expect(editCompleteHistory).not.toContain(true);
    expect(useWizardStore.getState().completedSteps).not.toContain('edit');
    expect(screen.getByRole('button', { name: 'Calculate carbon footprint' })).toBeDisabled();
  });
});
