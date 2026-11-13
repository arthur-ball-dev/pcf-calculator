/**
 * BOMCardList (phones): a card is as editable as a desktop row (#195, TASK-FE-P9-006)
 *
 * Name, category, unit and emission factor can be changed on a card, with the same rules as
 * the desktop row: units limited to the factor's kind, a factor of another kind switches the
 * unit, a missing factor is pointed out, and the CO2e preview converts units.
 */
import { render, screen, fireEvent, waitFor } from '../../testUtils';
import { describe, test, expect, vi } from 'vitest';
import { BOMCardList } from '@/components/calculator/BOMCardList';
import type { EmissionFactor } from '@/hooks/useEmissionFactors';

const factors = [
  { id: 'ef-steel', activity_name: 'Steel Production', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
  { id: 'ef-grid', activity_name: 'Electricity Grid', co2e_factor: 0.4, unit: 'kWh', category: 'energy', data_source: 'EPA' },
] as unknown as EmissionFactor[];

type Card = Parameters<typeof BOMCardList>[0]['items'][number];

function card(overrides: Partial<Card> = {}): Card {
  return {
    id: 'card-1',
    name: 'Steel Sheet',
    quantity: 2,
    unit: 'kg',
    category: 'material',
    emissionFactorId: 'ef-steel',
    ...overrides,
  };
}

function renderCards(items: Card[]) {
  const onUpdate = vi.fn();
  render(<BOMCardList items={items} onUpdate={onUpdate} onRemove={() => {}} emissionFactors={factors} />);
  return onUpdate;
}

async function choose(name: RegExp, option: RegExp | string) {
  fireEvent.click(screen.getByRole('combobox', { name }));
  fireEvent.click(await screen.findByRole('option', { name: option }));
}

describe('BOMCardList editing', { timeout: 20000 }, () => {
  test('renames a component', () => {
    const onUpdate = renderCards([card()]);
    fireEvent.change(screen.getByRole('textbox', { name: /component name/i }), {
      target: { value: 'Stainless Steel' },
    });
    expect(onUpdate).toHaveBeenCalledWith('card-1', { name: 'Stainless Steel' });
  });

  test('changes the category', async () => {
    const onUpdate = renderCards([card()]);
    await choose(/^category$/i, 'Transport');
    expect(onUpdate).toHaveBeenCalledWith('card-1', { category: 'transport' });
  });

  test('offers only units of the factor kind and changes the unit', async () => {
    const onUpdate = renderCards([card({ unit: 'kg', emissionFactorId: 'ef-steel' })]);
    fireEvent.click(screen.getByRole('combobox', { name: /^unit$/i }));
    const options = (await screen.findAllByRole('option')).map((o) => o.textContent);
    expect(options).toEqual(['kg', 'g', 't']);
    fireEvent.click(screen.getByRole('option', { name: 'g' }));
    expect(onUpdate).toHaveBeenCalledWith('card-1', { unit: 'g' });
  });

  test("choosing a factor of another kind also switches to the factor's unit", async () => {
    const onUpdate = renderCards([card({ unit: 'kg', emissionFactorId: 'ef-steel' })]);
    await choose(/emission factor/i, /Electricity Grid/);
    expect(onUpdate).toHaveBeenCalledWith('card-1', { emissionFactorId: 'ef-grid', unit: 'kWh' });
  });

  test('choosing a factor of the same kind keeps the unit', async () => {
    const onUpdate = renderCards([card({ unit: 'g', emissionFactorId: null })]);
    await choose(/emission factor/i, /Steel Production/);
    expect(onUpdate).toHaveBeenCalledWith('card-1', { emissionFactorId: 'ef-steel' });
  });

  test('says a factor is needed when a card has none', () => {
    renderCards([card({ emissionFactorId: null })]);
    expect(screen.getByText(/choose an emission factor to calculate/i)).toBeInTheDocument();
  });

  test("converts the quantity to the factor's unit in the CO2e preview", async () => {
    // 500 g at 2.5 kg CO2e/kg = 1.25 kg CO2e
    renderCards([card({ quantity: 500, unit: 'g', emissionFactorId: 'ef-steel' })]);
    await waitFor(() => expect(screen.getAllByText('1.25').length).toBeGreaterThan(0));
  });
});
