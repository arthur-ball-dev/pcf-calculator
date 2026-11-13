/**
 * Results and exports group components by their BOM row's category (#195, TASK-FE-P9-006)
 *
 * The category is the one in the BOM editor (which the user can change), not a guess from the
 * component name. A component with no matching BOM row falls back to the name.
 */
import { render, screen, within } from '../../testUtils';
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '../../testUtils';
import { categoryLookup } from '@/utils/bomRow';
import { transformToSankeyData, transformToExpandedSankeyData } from '@/utils/sankeyTransform';
import BreakdownTable from '@/components/calculator/BreakdownTable';
import { useExport } from '@/hooks/useExport';
import type { BOMItem } from '@/types/store.types';
import type { Calculation } from '@/types/store.types';

vi.mock('@/utils/export/csvExport', () => ({ exportToCSV: vi.fn() }));
vi.mock('@/utils/export/excelExport', () => ({ exportToExcel: vi.fn() }));
import { exportToCSV } from '@/utils/export/csvExport';
import { exportToExcel } from '@/utils/export/excelExport';

const bom: BOMItem[] = [
  // Names that the classifier would put elsewhere
  { id: '1', name: 'Electricity Cable', quantity: 1, unit: 'kg', category: 'material', emissionFactorId: 'ef-1' },
  { id: '2', name: 'Steel Frame', quantity: 1, unit: 'kg', category: 'transport', emissionFactorId: 'ef-1' },
  { id: '3', name: 'Packaging Film', quantity: 1, unit: 'kg', category: 'combustion', emissionFactorId: 'ef-1' },
];

describe('categoryLookup', () => {
  test("returns the row's category, as a result category", () => {
    const categoryOf = categoryLookup(bom);
    expect(categoryOf('Electricity Cable')).toBe('materials');
    expect(categoryOf('Steel Frame')).toBe('transport');
    expect(categoryOf('Packaging Film')).toBe('combustion');
  });

  test('matches names ignoring case, spaces, underscores and dashes', () => {
    expect(categoryLookup(bom)('electricity_cable')).toBe('materials');
    expect(categoryLookup(bom)('STEEL-FRAME')).toBe('transport');
  });

  test('returns undefined for a name with no BOM row', () => {
    expect(categoryLookup(bom)('Unknown Part')).toBeUndefined();
  });
});

const calculation = {
  id: 'calc-1',
  status: 'completed',
  total_co2e_kg: 10,
  materials_co2e: 10,
  energy_co2e: 0,
  transport_co2e: 0,
  breakdown: { 'Electricity Cable': 5, 'Steel Frame': 3, 'Packaging Film': 2 },
} as unknown as Calculation;

describe('Sankey diagram', () => {
  test('groups components by row category', () => {
    const data = transformToSankeyData(calculation, categoryLookup(bom));
    const value = (id: string) => data.links.find((l) => l.source === id || l.target === id)?.value;
    expect(value('materials')).toBe(5);
    expect(value('transport')).toBe(3);
    expect(value('combustion')).toBe(2);
    expect(data.nodes.find((n) => n.id === 'energy')).toBeUndefined();
  });

  test('expands a category to the components with that row category', () => {
    const data = transformToExpandedSankeyData(calculation, 'transport', categoryLookup(bom));
    const names = data.nodes.map((n) => n.label ?? n.id).join(' ');
    expect(names).toMatch(/Steel Frame/);
    expect(names).not.toMatch(/Electricity Cable/);
  });

  test('falls back to the name without a lookup', () => {
    const data = transformToSankeyData(calculation);
    expect(data.nodes.find((n) => n.id === 'energy')).toBeDefined();
  });
});

describe('Breakdown table', () => {
  test('lists components under their row category', () => {
    render(
      <BreakdownTable
        totalCO2e={10}
        breakdown={{ 'Electricity Cable': 5, 'Steel Frame': 3, 'Packaging Film': 2 }}
        categoryOf={categoryLookup(bom)}
      />,
    );
    const table = screen.getByRole('table');
    expect(within(table).getByText(/^materials$/i)).toBeInTheDocument();
    expect(within(table).getByText(/^transport$/i)).toBeInTheDocument();
    expect(within(table).getByText(/^combustion$/i)).toBeInTheDocument();
    expect(within(table).queryByText(/^energy$/i)).not.toBeInTheDocument();
  });
});

describe('Exports', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const results = {
    calculation_id: 'calc-1',
    status: 'completed',
    total_co2e_kg: 8,
    bom_details: [
      { component_name: 'Electricity Cable', category: 'material', quantity: 1, unit: 'kg', emission_factor: 5, emissions: 5 },
      { component_name: 'Steel Frame', category: 'transport', quantity: 1, unit: 'kg', emission_factor: 3, emissions: 3 },
    ],
  };

  test('the CSV Category column uses the row category', async () => {
    const { result } = renderHook(() => useExport(results as never, { name: 'Widget', code: 'W-1' }));
    await act(async () => {
      await result.current.exportToCSV();
    });
    const rows = vi.mocked(exportToCSV).mock.calls[0][0] as Array<Record<string, unknown>>;
    expect(rows.find((r) => r.Component === 'Electricity Cable')?.Category).toBe('Materials');
    expect(rows.find((r) => r.Component === 'Steel Frame')?.Category).toBe('Transport');
  });

  test('the Excel BOM entries use the row category', async () => {
    const { result } = renderHook(() => useExport(results as never, { name: 'Widget', code: 'W-1' }));
    await act(async () => {
      await result.current.exportToExcel();
    });
    const data = vi.mocked(exportToExcel).mock.calls[0][0] as { bomEntries: Array<{ component: string; category: string }> };
    expect(data.bomEntries.find((e) => e.component === 'Electricity Cable')?.category).toBe('materials');
    expect(data.bomEntries.find((e) => e.component === 'Steel Frame')?.category).toBe('transport');
  });
});
