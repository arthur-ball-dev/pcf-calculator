/**
 * BOMEditor and product selection keep the BOM as edited (#195, TASK-FE-P9-006)
 *
 * - The edit step (and so Calculate) stays incomplete while any row has no emission factor.
 * - A category the user chose survives leaving the editor and coming back: the editor no
 *   longer re-derives every category from the name when it loads.
 * - The estimated total converts each quantity to its factor's unit.
 * - On phones, editing a card's name, category, unit and factor reaches the BOM.
 */
import { render, screen, fireEvent, waitFor } from '../../testUtils';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import BOMEditor from '@/components/forms/BOMEditor';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

const breakpoints = vi.hoisted(() => ({ isMobile: false }));

vi.mock('@/hooks/useBreakpoints', () => ({
  useBreakpoints: () => ({ isMobile: breakpoints.isMobile, isTablet: false, isDesktop: !breakpoints.isMobile }),
}));

vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: 'ef-steel', activity_name: 'Steel Production', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
      { id: 'ef-grid', activity_name: 'Electricity Grid', co2e_factor: 0.4, unit: 'kWh', category: 'energy', data_source: 'EPA' },
    ],
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/services/api/emissionFactors', () => ({
  emissionFactorsAPI: { suggest: vi.fn().mockResolvedValue(null) },
}));

function item(overrides: Partial<BOMItem> = {}): BOMItem {
  return {
    id: 'row-1',
    name: 'Steel Sheet',
    quantity: 2,
    unit: 'kg',
    category: 'material',
    emissionFactorId: 'ef-steel',
    ...overrides,
  };
}

async function renderEditor(items: BOMItem[]) {
  useCalculatorStore.setState({ selectedProductId: 'prod-1', bomItems: items });
  const view = render(<BOMEditor />);
  await waitFor(() => {
    expect(screen.queryByRole('status', { name: 'Loading bill of materials' })).not.toBeInTheDocument();
  }, { timeout: 5000 });
  return view;
}

const editComplete = () => useWizardStore.getState().completedSteps.includes('edit');

describe('BOMEditor with the edited BOM', { timeout: 20000 }, () => {
  beforeEach(() => {
    breakpoints.isMobile = false;
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
  });

  test('the edit step is complete when every row has an emission factor', async () => {
    await renderEditor([item(), item({ id: 'row-2', name: 'Grid Power', unit: 'kWh', category: 'energy', emissionFactorId: 'ef-grid' })]);
    await waitFor(() => expect(editComplete()).toBe(true));
  });

  test('the edit step stays incomplete while a row has no emission factor', async () => {
    await renderEditor([item(), item({ id: 'row-2', name: 'New Part', emissionFactorId: null })]);
    await screen.findByText(/choose an emission factor to calculate/i);
    expect(editComplete()).toBe(false);
  });

  test('a category the user chose survives coming back to the editor', async () => {
    // "Steel Sheet" would classify as Materials; the user had set it to Other
    const view = await renderEditor([item({ category: 'other' })]);
    expect(screen.getByRole('combobox', { name: /^category$/i })).toHaveTextContent('Other');
    view.unmount();

    await renderEditor(useCalculatorStore.getState().bomItems);
    expect(screen.getByRole('combobox', { name: /^category$/i })).toHaveTextContent('Other');
    expect(useCalculatorStore.getState().bomItems[0].category).toBe('other');
  });

  test("the estimated total converts quantities to each factor's unit", async () => {
    // 500 g of steel at 2.5 kg CO2e/kg + 36 MJ at 0.4 kg CO2e/kWh = 1.25 + 4 = 5.25
    await renderEditor([
      item({ quantity: 500, unit: 'g' }),
      item({ id: 'row-2', name: 'Grid Power', quantity: 36, unit: 'MJ', category: 'energy', emissionFactorId: 'ef-grid' }),
    ]);
    expect(await screen.findByText('5.25')).toBeInTheDocument();
  });
});

describe('BOMEditor on phones', { timeout: 20000 }, () => {
  beforeEach(() => {
    breakpoints.isMobile = true;
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
  });

  test('renaming a card reaches the BOM and re-derives its category', async () => {
    await renderEditor([item({ name: 'Steel Sheet', category: 'material' })]);
    fireEvent.change(screen.getByRole('textbox', { name: /component name/i }), {
      target: { value: 'Truck Transport' },
    });
    await waitFor(() => {
      const [row] = useCalculatorStore.getState().bomItems;
      expect(row.name).toBe('Truck Transport');
      expect(row.category).toBe('transport');
    });
  });

  test("choosing a card's factor of another kind reaches the BOM with the factor's unit", async () => {
    await renderEditor([item({ unit: 'kg', emissionFactorId: 'ef-steel' })]);
    fireEvent.click(screen.getByRole('combobox', { name: /emission factor/i }));
    fireEvent.click(await screen.findByRole('option', { name: /Electricity Grid/ }));
    await waitFor(() => {
      const [row] = useCalculatorStore.getState().bomItems;
      expect(row.emissionFactorId).toBe('ef-grid');
      expect(row.unit).toBe('kWh');
    });
  });

  test("changing a card's category reaches the BOM", async () => {
    await renderEditor([item({ category: 'material' })]);
    fireEvent.click(screen.getByRole('combobox', { name: /^category$/i }));
    fireEvent.click(await screen.findByRole('option', { name: 'Combustion' }));
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0].category).toBe('combustion'));
  });
});
