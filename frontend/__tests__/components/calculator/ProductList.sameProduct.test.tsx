/**
 * ProductList: re-selecting the product being edited keeps the edits (#195, TASK-FE-P9-006)
 *
 * Going back to step 1 and clicking the same product again must not reload its catalog BOM
 * over the user's edits. Choosing a different product does load that product's BOM.
 */
import { render, screen, fireEvent, waitFor } from '../../testUtils';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import ProductList from '@/components/calculator/ProductList';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import { productsAPI } from '@/services/api/products';

vi.mock('@/services/api/emissionFactors', () => ({
  emissionFactorsAPI: { list: vi.fn().mockResolvedValue([]), suggest: vi.fn().mockResolvedValue(null) },
}));

vi.mock('@/services/api/products', () => ({
  productsAPI: { search: vi.fn(), getById: vi.fn() },
}));

const searchItem = (id: string, name: string) => ({
  id, code: id.toUpperCase(), name, description: null, unit: 'unit',
  category: { id: 'cat-1', code: 'ELEC', name: 'Electronics', industry: 'electronics' },
  manufacturer: null, country_of_origin: null, is_finished_product: true,
  relevance_score: null, created_at: '2026-01-01T00:00:00Z',
});

const detail = (id: string, name: string, componentName: string) => ({
  id, code: id.toUpperCase(), name, description: null, unit: 'unit', category: 'electronics',
  is_finished_product: true, created_at: '2026-01-01T00:00:00Z',
  bill_of_materials: [{
    id: `${id}-bom`, child_product_id: `${id}-child`, child_product_name: componentName,
    quantity: 1, unit: 'kg', notes: null, emission_factor_id: 'ef-1',
  }],
});

describe('ProductList re-selection', { timeout: 20000 }, () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
    vi.mocked(productsAPI.search).mockResolvedValue({
      items: [searchItem('p1', 'Laptop'), searchItem('p2', 'Phone')],
      total: 2, limit: 50, offset: 0, has_more: false,
    } as never);
    vi.mocked(productsAPI.getById).mockImplementation(async (id: string) =>
      (id === 'p1' ? detail('p1', 'Laptop', 'Aluminium Case') : detail('p2', 'Phone', 'Glass Panel')) as never);
  });

  test('clicking the selected product again keeps the edited BOM', async () => {
    render(<ProductList />);
    fireEvent.click(await screen.findByRole('option', { name: /Laptop/ }));
    await waitFor(() => expect(useCalculatorStore.getState().bomItems).toHaveLength(1));

    // The user edits the BOM in step 2
    const [row] = useCalculatorStore.getState().bomItems;
    useCalculatorStore.getState().setBomItems([{ ...row, quantity: 7 }]);

    fireEvent.click(screen.getByRole('option', { name: /Laptop/ }));
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(productsAPI.getById).toHaveBeenCalledTimes(1);
    expect(useCalculatorStore.getState().bomItems[0].quantity).toBe(7);
    expect(useWizardStore.getState().completedSteps).toContain('select');
  });

  test('choosing another product loads its BOM', async () => {
    render(<ProductList />);
    fireEvent.click(await screen.findByRole('option', { name: /Laptop/ }));
    await waitFor(() => expect(useCalculatorStore.getState().bomItems).toHaveLength(1));

    fireEvent.click(screen.getByRole('option', { name: /Phone/ }));
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0].name).toBe('Glass Panel'));
    expect(productsAPI.getById).toHaveBeenCalledTimes(2);
  });

  test('the catalog BOM is categorised from component names when it loads', async () => {
    vi.mocked(productsAPI.getById).mockResolvedValue({
      ...detail('p1', 'Laptop', 'Truck Transport'),
    } as never);
    render(<ProductList />);
    fireEvent.click(await screen.findByRole('option', { name: /Laptop/ }));
    await waitFor(() => expect(useCalculatorStore.getState().bomItems[0]?.category).toBe('transport'));
  });
});
