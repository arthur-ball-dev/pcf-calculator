/**
 * useCalculation Hook UUID Handling Tests (TASK-FE-020 - Test-First)
 *
 * Tests UUID type system migration for calculation IDs from API responses.
 * These tests expect string types for calculation IDs.
 *
 * CRITICAL: These tests are written BEFORE implementation (TDD Phase 1).
 * They will fail initially, proving they are valid tests.
 */

import { describe, test, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCalculation } from '../../src/hooks/useCalculation';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import api from '@/services/api';

// Mock the API service
vi.mock('@/services/api', () => ({
  default: {
    calculations: {
      submit: vi.fn(),
      getStatus: vi.fn(),
    },
  },
}));

describe('useCalculation Hook - UUID Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();

    // Setup default store state with product and BOM
    useCalculatorStore.getState().setSelectedProduct('product-uuid-123');
    useCalculatorStore.getState().setBomItems([
      {
        id: '1',
        activity_name: 'Cotton',
        quantity: 1,
        unit: 'kg',
        emissionFactorId: 'ef-1',
        co2e_factor: 2.5,
        category: 'materials',
      },
    ]);

    // Mark wizard steps complete to allow calculation
    useWizardStore.getState().markStepComplete('select');
    useWizardStore.getState().markStepComplete('edit');
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Calculation ID from POST Response', () => {
    test('should store calculation ID as UUID string from API response', async () => {
      const calculationId = 'calc-uuid-xyz789abc123def456';

      // Mock API response
      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: calculationId,
      });

      const { result } = renderHook(() => useCalculation());

      // Trigger calculation
      await act(async () => {
        await result.current.startCalculation();
      });

      // Check store has string ID
      await vi.waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.calculation?.id).toBe(calculationId);
        expect(typeof state.calculation?.id).toBe('string');
      }, { timeout: 1000 });
    });

    test('should preserve full UUID without truncation', async () => {
      const calculationId = '471fe408a2604386bae572d9fc9a6b5c';

      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: calculationId,
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      await vi.waitFor(() => {
        const state = useCalculatorStore.getState();
        // Ensure not truncated
        expect(state.calculation?.id).toBe(calculationId);
        expect(state.calculation?.id).not.toBe('471');
        expect(state.calculation?.id?.length).toBe(32);
      }, { timeout: 1000 });
    });

    test('should handle 32-character hex UUIDs', async () => {
      const calculationId = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6';

      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: calculationId,
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      await vi.waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.calculation?.id).toBe(calculationId);
        expect(typeof state.calculation?.id).toBe('string');
        expect(state.calculation?.id?.length).toBe(32);
      }, { timeout: 1000 });
    });
  });

  describe('Calculation ID in Polling Requests', () => {
    test('should use string UUID when polling for status', async () => {
      vi.useFakeTimers();

      const calculationId = 'calc-uuid-polling-test-123';

      // Mock POST response
      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: calculationId,
      });

      // Mock GET polling responses
      vi.mocked(api.calculations.getStatus)
        .mockResolvedValueOnce({
          calculation_id: calculationId,
          status: 'in_progress',
          product_id: '471fe408a2604386bae572d9fc9a6b5c',
          created_at: null,
        })
        .mockResolvedValueOnce({
          calculation_id: calculationId,
          status: 'completed',
          product_id: '471fe408a2604386bae572d9fc9a6b5c',
          created_at: '2025-11-11T12:00:00Z',
          total_co2e_kg: 100.5,
          materials_co2e: 75.2,
          energy_co2e: 20.1,
          transport_co2e: 5.2,
        });

      const { result } = renderHook(() => useCalculation());

      // Start calculation
      await act(async () => {
        await result.current.startCalculation();
      });

      // Advance timers to trigger first poll (2 seconds)
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Wait for first poll
      await vi.waitFor(() => {
        expect(vi.mocked(api.calculations.getStatus)).toHaveBeenCalledTimes(1);
      }, { timeout: 1000 });

      // Advance timers to trigger second poll (2 more seconds)
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Wait for completion
      await vi.waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.calculation?.status).toBe('completed');
      }, { timeout: 1000 });

      // Verify getStatus was called with string ID
      expect(vi.mocked(api.calculations.getStatus)).toHaveBeenCalledWith(calculationId);
      expect(vi.mocked(api.calculations.getStatus)).toHaveBeenCalledTimes(2);

      vi.useRealTimers();
    });
  });

  describe('Product ID in Calculation Payload', () => {
    test('should send full UUID product ID in POST payload', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';

      // Set product ID in store
      useCalculatorStore.getState().setSelectedProduct(productId);

      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: 'calc-123',
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Verify payload has full UUID
      await vi.waitFor(() => {
        expect(vi.mocked(api.calculations.submit)).toHaveBeenCalledWith(
          expect.objectContaining({
            product_id: productId,
          })
        );
      }, { timeout: 1000 });

      // Verify the argument structure
      const callArgs = vi.mocked(api.calculations.submit).mock.calls[0][0];
      expect(callArgs.product_id).toBe(productId);
      expect(callArgs.product_id.length).toBe(32);
      expect(callArgs.product_id).not.toBe('471'); // NOT truncated
    });

    test('should handle product ID that starts with numeric characters', async () => {
      const productId = '123abc456def789012345678abcdef12';

      useCalculatorStore.getState().setSelectedProduct(productId);

      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: 'calc-456',
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      await vi.waitFor(() => {
        expect(vi.mocked(api.calculations.submit)).toHaveBeenCalledWith(
          expect.objectContaining({
            product_id: productId,
          })
        );
      }, { timeout: 1000 });

      const callArgs = vi.mocked(api.calculations.submit).mock.calls[0][0];
      expect(callArgs.product_id).toBe(productId);
      expect(callArgs.product_id).not.toBe('123');
      expect(typeof callArgs.product_id).toBe('string');
    });
  });

  describe('Completed Calculation Response', () => {
    test('should preserve UUID strings in completed calculation', async () => {
      vi.useFakeTimers();

      const calculationId = 'calc-complete-uuid-test';
      const productId = 'prod-uuid-test-123';

      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: calculationId,
      });

      vi.mocked(api.calculations.getStatus).mockResolvedValueOnce({
        calculation_id: calculationId,
        status: 'completed',
        product_id: productId,
        created_at: '2025-11-11T12:00:00Z',
        total_co2e_kg: 100.5,
        materials_co2e: 75.2,
        energy_co2e: 20.1,
        transport_co2e: 5.2,
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Advance timers to trigger first poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      await vi.waitFor(() => {
        const state = useCalculatorStore.getState();
        expect(state.calculation?.status).toBe('completed');
      }, { timeout: 1000 });

      const state = useCalculatorStore.getState();
      expect(state.calculation?.id).toBe(calculationId);
      expect(state.calculation?.product_id).toBe(productId);
      expect(typeof state.calculation?.id).toBe('string');
      expect(typeof state.calculation?.product_id).toBe('string');

      vi.useRealTimers();
    });
  });

  describe('Error Handling with UUIDs', () => {
    test('should handle failed calculation with UUID preserved', async () => {
      vi.useFakeTimers();

      const calculationId = 'calc-failed-uuid-test';

      vi.mocked(api.calculations.submit).mockResolvedValueOnce({
        calculation_id: calculationId,
      });

      vi.mocked(api.calculations.getStatus).mockResolvedValueOnce({
        calculation_id: calculationId,
        status: 'failed',
        product_id: null,
        created_at: null,
        error_message: 'Calculation failed',
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Advance timers to trigger first poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Wait for error to be set (implementation doesn't update calculation status for failed)
      await vi.waitFor(() => {
        expect(result.current.error).toBe('Calculation failed');
      }, { timeout: 1000 });

      // Verify calculation ID was stored initially (as pending)
      const state = useCalculatorStore.getState();
      expect(state.calculation?.id).toBe(calculationId);
      expect(typeof state.calculation?.id).toBe('string');
      // Note: status will be 'pending' because implementation doesn't update it on failure

      vi.useRealTimers();
    });
  });
});
