/**
 * useCalculation sends the BOM as edited (#195, TASK-FE-P9-006)
 *
 * The calculation request carries every row of the edited BOM (name, quantity, unit, category,
 * emission factor), read from the store when Calculate is clicked, so the backend calculates
 * what the user sees instead of the catalog BOM.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '../testUtils';
import { useCalculation } from '../../src/hooks/useCalculation';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import api from '../../src/services/api';

vi.mock('../../src/services/api', () => ({
  default: {
    calculations: {
      submit: vi.fn(),
      getStatus: vi.fn(),
    },
  },
}));

describe('useCalculation submits the edited BOM', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalculatorStore.getState().reset();
    vi.mocked(api.calculations.submit).mockResolvedValue({
      calculation_id: 'calc-1',
      status: 'pending',
    });
  });

  it('sends every row with its name, quantity, unit, category and emission factor', async () => {
    useCalculatorStore.setState({
      selectedProductId: 'prod-1',
      bomItems: [
        { id: 'a', name: 'Recycled Steel', quantity: 500, unit: 'g', category: 'material', emissionFactorId: 'ef-steel' },
        { id: 'b', name: 'Grid Power', quantity: 36, unit: 'MJ', category: 'energy', emissionFactorId: 'ef-grid' },
        { id: 'c', name: 'Courier', quantity: 4, unit: 'tkm', category: 'other', emissionFactorId: 'ef-truck' },
      ],
    });
    const { result } = renderHook(() => useCalculation());

    await act(async () => {
      await result.current.startCalculation();
    });

    expect(api.calculations.submit).toHaveBeenCalledTimes(1);
    expect(api.calculations.submit).toHaveBeenCalledWith({
      product_id: 'prod-1',
      bom: [
        { name: 'Recycled Steel', quantity: 500, unit: 'g', category: 'material', emission_factor_id: 'ef-steel' },
        { name: 'Grid Power', quantity: 36, unit: 'MJ', category: 'energy', emission_factor_id: 'ef-grid' },
        { name: 'Courier', quantity: 4, unit: 'tkm', category: 'other', emission_factor_id: 'ef-truck' },
      ],
    });
  });

  it('sends the rows as they are when Calculate is clicked, not as first rendered', async () => {
    useCalculatorStore.setState({
      selectedProductId: 'prod-1',
      bomItems: [
        { id: 'a', name: 'Cotton', quantity: 1, unit: 'kg', category: 'material', emissionFactorId: 'ef-cotton' },
      ],
    });
    const { result } = renderHook(() => useCalculation());

    // An edit written after the hook rendered (the editor syncs to the store as the user types)
    useCalculatorStore.setState({
      bomItems: [
        { id: 'a', name: 'Cotton', quantity: 3, unit: 'kg', category: 'material', emissionFactorId: 'ef-cotton' },
        { id: 'n', name: 'Added Zip', quantity: 0.02, unit: 'kg', category: 'material', emissionFactorId: 'ef-zinc' },
      ],
    });
    await act(async () => {
      await result.current.startCalculation();
    });

    const request = vi.mocked(api.calculations.submit).mock.calls[0][0];
    expect(request.bom).toEqual([
      { name: 'Cotton', quantity: 3, unit: 'kg', category: 'material', emission_factor_id: 'ef-cotton' },
      { name: 'Added Zip', quantity: 0.02, unit: 'kg', category: 'material', emission_factor_id: 'ef-zinc' },
    ]);
  });
});
