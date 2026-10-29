/**
 * useCalculation.startCalculation must act on the store's current state, not on
 * the state captured when the hook last rendered.
 *
 * In the wizard, the BOM editor writes bomItems to the calculator store and the
 * Calculate button can be clicked before React has re-rendered the wizard with
 * that update. The render-time snapshot still says "no items", the guard returned,
 * and nothing happened (no POST /calculate, no overlay progress): the intermittent
 * wizardFlow Scenario 1 failure (1 run in 3, with no load on the machine).
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor } from '../testUtils';
import { rest } from 'msw';
import { server } from '../../__mocks__/server';
import { useCalculation } from '../../src/hooks/useCalculation';
import { useCalculatorStore } from '../../src/store/calculatorStore';

describe('useCalculation reads the store at call time', () => {
  beforeEach(() => {
    useCalculatorStore.getState().reset();
  });

  it('starts the calculation when bomItems were written after the last render', async () => {
    const submitted: string[] = [];
    server.use(
      rest.post('http://localhost:8000/api/v1/calculate', async (req, res, ctx) => {
        const body = await req.json();
        submitted.push(body.product_id);
        return res(ctx.status(202), ctx.json({ calculation_id: 'calc-stale', status: 'pending' }));
      })
    );

    // Hook renders while the store is still empty ...
    const { result } = renderHook(() => useCalculation());

    // ... then the store is updated outside React's render cycle, exactly as the
    // BOM editor's sync effect does, and the click handler runs before a re-render.
    useCalculatorStore.setState({
      selectedProductId: 'prod-001',
      bomItems: [
        { id: 'comp-1', name: 'cotton', quantity: 1, unit: 'kg', category: 'material', emissionFactorId: null },
      ],
    });
    await result.current.startCalculation();

    await waitFor(() => expect(submitted).toEqual(['prod-001']));
    expect(useCalculatorStore.getState().calculation?.id).toBe('calc-stale');
  });
});
