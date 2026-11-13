/**
 * BOMTableRow: editing a row for the calculation (#195, TASK-FE-P9-006)
 *
 * - The unit picklist offers only units of the selected factor's kind (every unit with no factor).
 * - Choosing a factor whose unit is of another kind switches the row to the factor's unit.
 * - The category is a picker. Renaming a row re-derives its category from the name only while
 *   the user hasn't chosen one.
 * - A row without a factor says one is needed.
 * - The row's CO2e preview converts the quantity to the factor's unit.
 */
import { useEffect } from 'react';
import { render, screen, fireEvent, waitFor } from '../../testUtils';
import { describe, test, expect, vi } from 'vitest';
import { useForm, FormProvider, useFieldArray, type UseFormReturn } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Table, TableBody } from '@/components/ui/table';
import BOMTableRow from '@/components/forms/BOMTableRow';
import { bomFormSchema, type BOMFormData } from '@/schemas/bomSchema';
import type { EmissionFactor } from '@/hooks/useEmissionFactors';

vi.mock('@/services/api/emissionFactors', () => ({
  emissionFactorsAPI: { suggest: vi.fn().mockResolvedValue(null) },
}));

const factors = [
  { id: 'ef-steel', activity_name: 'Steel Production', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
  { id: 'ef-alu', activity_name: 'Aluminum Production', co2e_factor: 8, unit: 'kg', category: 'material', data_source: 'EPA' },
  { id: 'ef-grid', activity_name: 'Electricity Grid', co2e_factor: 0.4, unit: 'kWh', category: 'energy', data_source: 'EPA' },
] as unknown as EmissionFactor[];

type Item = BOMFormData['items'][number];

function row(overrides: Partial<Item> = {}): Item {
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

let form: UseFormReturn<BOMFormData>;

/** Keeps the rendered form instance where the tests can read its values */
function captureForm(instance: UseFormReturn<BOMFormData>) {
  form = instance;
}

function Wrapper({ items }: { items: Item[] }) {
  const methods = useForm<BOMFormData>({
    resolver: zodResolver(bomFormSchema),
    mode: 'onChange',
    defaultValues: { items },
  });
  useEffect(() => {
    captureForm(methods);
  }, [methods]);
  const { fields } = useFieldArray({ control: methods.control, name: 'items' });
  return (
    <FormProvider {...methods}>
      <Table>
        <TableBody>
          {fields.map((field, index) => (
            <BOMTableRow
              key={field.id}
              field={field}
              index={index}
              form={methods}
              onRemove={() => {}}
              canRemove={false}
              emissionFactors={factors}
            />
          ))}
        </TableBody>
      </Table>
    </FormProvider>
  );
}

async function openAndListOptions(name: RegExp): Promise<string[]> {
  fireEvent.click(screen.getByRole('combobox', { name }));
  const options = await screen.findAllByRole('option');
  return options.map((o) => o.textContent ?? '');
}

async function choose(name: RegExp, option: RegExp | string) {
  fireEvent.click(screen.getByRole('combobox', { name }));
  fireEvent.click(await screen.findByRole('option', { name: option }));
}

describe('BOMTableRow unit picklist', { timeout: 20000 }, () => {
  test('offers only units of the selected factor kind', async () => {
    render(<Wrapper items={[row({ emissionFactorId: 'ef-steel' })]} />);
    expect(await openAndListOptions(/^unit$/i)).toEqual(['kg', 'g', 't']);
  });

  test('offers every unit when no factor is selected', async () => {
    render(<Wrapper items={[row({ emissionFactorId: null })]} />);
    expect(await openAndListOptions(/^unit$/i)).toEqual(
      ['kg', 'g', 't', 'L', 'mL', 'kWh', 'MJ', 'tkm', 'unit', 'm', 'cm'],
    );
  });

  test("choosing a factor of another kind switches the row to the factor's unit", async () => {
    render(<Wrapper items={[row({ unit: 'kg', emissionFactorId: 'ef-steel' })]} />);
    await choose(/emission factor/i, /Electricity Grid/);
    await waitFor(() => expect(form.getValues('items.0.unit')).toBe('kWh'));
    expect(form.getValues('items.0.emissionFactorId')).toBe('ef-grid');
  });

  test('choosing a factor of the same kind keeps the row unit', async () => {
    render(<Wrapper items={[row({ unit: 'g', emissionFactorId: 'ef-steel' })]} />);
    await choose(/emission factor/i, /Aluminum Production/);
    await waitFor(() => expect(form.getValues('items.0.emissionFactorId')).toBe('ef-alu'));
    expect(form.getValues('items.0.unit')).toBe('g');
  });
});

describe('BOMTableRow category picker', { timeout: 20000 }, () => {
  test('sets the row category', async () => {
    render(<Wrapper items={[row({ category: 'material' })]} />);
    await choose(/^category$/i, 'Transport');
    await waitFor(() => expect(form.getValues('items.0.category')).toBe('transport'));
  });

  test("renaming re-derives the category while the user hasn't chosen one", async () => {
    render(<Wrapper items={[row({ name: 'Steel Sheet', category: 'material' })]} />);
    fireEvent.change(screen.getByRole('textbox', { name: /component name/i }), {
      target: { value: 'Truck Transport' },
    });
    await waitFor(() => expect(form.getValues('items.0.category')).toBe('transport'));
  });

  test('renaming keeps a category the user chose', async () => {
    render(<Wrapper items={[row({ name: 'Steel Sheet', category: 'material' })]} />);
    await choose(/^category$/i, 'Other');
    await waitFor(() => expect(form.getValues('items.0.category')).toBe('other'));

    fireEvent.change(screen.getByRole('textbox', { name: /component name/i }), {
      target: { value: 'Electricity Cable' },
    });
    await waitFor(() => expect(form.getValues('items.0.name')).toBe('Electricity Cable'));
    expect(form.getValues('items.0.category')).toBe('other');
  });
});

describe('BOMTableRow without an emission factor', { timeout: 20000 }, () => {
  test('says a factor is needed', async () => {
    render(<Wrapper items={[row({ emissionFactorId: null })]} />);
    expect(await screen.findByText(/choose an emission factor to calculate/i)).toBeInTheDocument();
  });

  test('says nothing once a factor is chosen', async () => {
    render(<Wrapper items={[row({ emissionFactorId: 'ef-steel' })]} />);
    await screen.findByRole('combobox', { name: /emission factor/i });
    expect(screen.queryByText(/choose an emission factor to calculate/i)).not.toBeInTheDocument();
  });
});

describe('BOMTableRow CO2e preview', { timeout: 20000 }, () => {
  test("converts the quantity to the factor's unit", async () => {
    // 500 g at 2.5 kg CO2e/kg = 1.25 kg CO2e
    render(<Wrapper items={[row({ quantity: 500, unit: 'g', emissionFactorId: 'ef-steel' })]} />);
    expect(await screen.findByText('1.25')).toBeInTheDocument();
  });
});
