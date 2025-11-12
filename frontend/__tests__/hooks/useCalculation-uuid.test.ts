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
import { renderHook, waitFor } from '@testing-library/react';
import { useCalculation } from '../../src/hooks/useCalculation';
import { useCalculatorStore } from '../../src/store/calculatorStore';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('useCalculation Hook - UUID Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCalculatorStore.getState().reset();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Calculation ID from POST Response', () => {
    test('should store calculation ID as UUID string from API response', async () => {
      const calculationId = 'calc-uuid-xyz789abc123def456';

      // Mock POST /api/v1/calculate
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({
          calculation_id: calculationId,
        }),
      });

      const { result } = renderHook(() => useCalculation());

      // Trigger calculation
      await waitFor(async () => {
        await result.current.startCalculation();
      });

      // Check store has string ID
      const state = useCalculatorStore.getState();
      expect(state.calculation?.id).toBe(calculationId);
      expect(typeof state.calculation?.id).toBe('string');
    });

    test('should preserve full UUID without truncation', async () => {
      const calculationId = '471fe408a2604386bae572d9fc9a6b5c';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({
          calculation_id: calculationId,
        }),
      });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      const state = useCalculatorStore.getState();
      // Ensure not truncated
      expect(state.calculation?.id).toBe(calculationId);
      expect(state.calculation?.id).not.toBe('471');
      expect(state.calculation?.id?.length).toBe(32);
    });

    test('should handle 32-character hex UUIDs', async () => {
      const calculationId = 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({
          calculation_id: calculationId,
        }),
      });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      const state = useCalculatorStore.getState();
      expect(state.calculation?.id).toBe(calculationId);
      expect(typeof state.calculation?.id).toBe('string');
      expect(state.calculation?.id?.length).toBe(32);
    });
  });

  describe('Calculation ID in Polling Requests', () => {
    test('should use string UUID when polling for status', async () => {
      const calculationId = 'calc-uuid-polling-test-123';

      // Mock POST response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({
          calculation_id: calculationId,
        }),
      });

      // Mock GET polling responses
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            id: calculationId,
            status: 'in_progress',
            product_id: '471fe408a2604386bae572d9fc9a6b5c',
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            id: calculationId,
            status: 'completed',
            product_id: '471fe408a2604386bae572d9fc9a6b5c',
            total_co2e_kg: 100.5,
            materials_co2e: 75.2,
            energy_co2e: 20.1,
            transport_co2e: 5.2,
          }),
        });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      // Wait for polling to complete
      await waitFor(
        () => {
          expect(result.current.calculation?.status).toBe('completed');
        },
        { timeout: 5000 }
      );

      // Verify GET requests used string ID in URL
      const getCalls = mockFetch.mock.calls.filter(
        (call) => call[0]?.includes('/api/v1/calculations/')
      );
      expect(getCalls.length).toBeGreaterThan(0);
      expect(getCalls[0][0]).toContain(calculationId);
      expect(getCalls[0][0]).not.toContain('NaN');
    });
  });

  describe('Product ID in Calculation Payload', () => {
    test('should send full UUID product ID in POST payload', async () => {
      const productId = '471fe408a2604386bae572d9fc9a6b5c';

      // Set product ID in store
      useCalculatorStore.getState().setSelectedProduct(productId);

      let capturedPayload: any;

      mockFetch.mockImplementationOnce(async (url, options) => {
        if (options?.body) {
          capturedPayload = JSON.parse(options.body as string);
        }
        return {
          ok: true,
          status: 202,
          json: async () => ({
            calculation_id: 'calc-123',
          }),
        };
      });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      // Verify payload has full UUID
      expect(capturedPayload.product_id).toBe(productId);
      expect(capturedPayload.product_id.length).toBe(32);
      expect(capturedPayload.product_id).not.toBe('471'); // NOT truncated
    });

    test('should handle product ID that starts with numeric characters', async () => {
      const productId = '123abc456def789012345678abcdef12';

      useCalculatorStore.getState().setSelectedProduct(productId);

      let capturedPayload: any;

      mockFetch.mockImplementationOnce(async (url, options) => {
        if (options?.body) {
          capturedPayload = JSON.parse(options.body as string);
        }
        return {
          ok: true,
          status: 202,
          json: async () => ({
            calculation_id: 'calc-456',
          }),
        };
      });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      expect(capturedPayload.product_id).toBe(productId);
      expect(capturedPayload.product_id).not.toBe('123');
      expect(typeof capturedPayload.product_id).toBe('string');
    });
  });

  describe('Completed Calculation Response', () => {
    test('should preserve UUID strings in completed calculation', async () => {
      const calculationId = 'calc-complete-uuid-test';
      const productId = 'prod-uuid-test-123';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({
          calculation_id: calculationId,
        }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          id: calculationId,
          status: 'completed',
          product_id: productId,
          total_co2e_kg: 100.5,
          materials_co2e: 75.2,
          energy_co2e: 20.1,
          transport_co2e: 5.2,
          created_at: '2025-11-11T12:00:00Z',
        }),
      });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      await waitFor(
        () => {
          expect(result.current.calculation?.status).toBe('completed');
        },
        { timeout: 5000 }
      );

      expect(result.current.calculation?.id).toBe(calculationId);
      expect(result.current.calculation?.product_id).toBe(productId);
      expect(typeof result.current.calculation?.id).toBe('string');
      expect(typeof result.current.calculation?.product_id).toBe('string');
    });
  });

  describe('Error Handling with UUIDs', () => {
    test('should handle failed calculation with UUID preserved', async () => {
      const calculationId = 'calc-failed-uuid-test';

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({
          calculation_id: calculationId,
        }),
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          id: calculationId,
          status: 'failed',
          error_message: 'Calculation failed',
        }),
      });

      const { result } = renderHook(() => useCalculation());

      await waitFor(async () => {
        await result.current.startCalculation();
      });

      await waitFor(
        () => {
          expect(result.current.calculation?.status).toBe('failed');
        },
        { timeout: 5000 }
      );

      expect(result.current.calculation?.id).toBe(calculationId);
      expect(typeof result.current.calculation?.id).toBe('string');
    });
  });
});
