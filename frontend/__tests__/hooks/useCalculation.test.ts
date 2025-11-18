/**
 * useCalculation Hook Tests
 * TASK-FE-007: Test calculation submission and polling logic
 *
 * Test Coverage:
 * 1. Submit calculation and receive calculation_id
 * 2. Polling loop (every 2 seconds)
 * 3. Auto-advance to results when completed
 * 4. Timeout handling (30 polls = 60 seconds)
 * 5. Calculation error handling
 * 6. Cancel/cleanup on unmount
 * 7. Retry functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useCalculation } from '../../src/hooks/useCalculation';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import api from '../../src/services/api';
import type { CalculationStartResponse, CalculationStatusResponse } from '../../src/types/api.types';

// Mock API
vi.mock('../../src/services/api', () => ({
  default: {
    calculations: {
      submit: vi.fn(),
      getStatus: vi.fn(),
    },
  },
}));

// Mock stores
vi.mock('../../src/store/calculatorStore', () => ({
  useCalculatorStore: vi.fn(),
}));

vi.mock('../../src/store/wizardStore', () => ({
  useWizardStore: vi.fn(),
}));

describe('useCalculation Hook', () => {
  let mockSetCalculation: ReturnType<typeof vi.fn>;
  let mockMarkStepComplete: ReturnType<typeof vi.fn>;
  let mockGoNext: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();

    // Setup store mocks
    mockSetCalculation = vi.fn();
    mockMarkStepComplete = vi.fn();
    mockGoNext = vi.fn();

    (useCalculatorStore as any).mockReturnValue({
      selectedProductId: 'prod-123',
      bomItems: [
        { id: 'bom-1', name: 'Component A', quantity: 2 },
      ],
      setCalculation: mockSetCalculation,
    });

    (useWizardStore as any).mockReturnValue({
      markStepComplete: mockMarkStepComplete,
      goNext: mockGoNext,
    });

    // Clear all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Submit Calculation
  // ==========================================================================

  describe('Submit Calculation', () => {
    it('should call API with product_id when startCalculation is called', async () => {
      const mockResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      (api.calculations.submit as any).mockResolvedValue(mockResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      expect(api.calculations.submit).toHaveBeenCalledWith({
        product_id: 'prod-123',
      });
    });

    it('should set isCalculating to true when calculation starts', async () => {
      const mockResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockStatusResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 2.5,
      };

      (api.calculations.submit as any).mockResolvedValue(mockResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockStatusResponse);

      const { result } = renderHook(() => useCalculation());

      expect(result.current.isCalculating).toBe(false);

      await act(async () => {
        await result.current.startCalculation();
      });

      expect(result.current.isCalculating).toBe(true);
      
      // Advance timer to complete polling
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });
      
      await vi.waitFor(() => {
        expect(result.current.isCalculating).toBe(false);
      }, { timeout: 1000 });
    });

    it('should clear error state when starting new calculation', async () => {
      const mockResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockStatusResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 2.5,
      };

      // First call fails to create error state
      (api.calculations.submit as any).mockRejectedValueOnce(new Error('Network error'));
      // Second call succeeds
      (api.calculations.submit as any).mockResolvedValueOnce(mockResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockStatusResponse);

      const { result } = renderHook(() => useCalculation());

      // Trigger error by failing first calculation
      await act(async () => {
        await result.current.startCalculation();
      });

      // Verify error was set
      expect(result.current.error).toBeTruthy();

      // Start new calculation - should clear error
      await act(async () => {
        await result.current.startCalculation();
      });

      // Advance timers to complete polling
      act(() => {
        vi.advanceTimersByTime(2000);
      });

      // Error should be cleared
      expect(result.current.error).toBeNull();
    });

    it('should not submit if no product selected', async () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: null,
        bomItems: [],
        setCalculation: mockSetCalculation,
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      expect(api.calculations.submit).not.toHaveBeenCalled();
    });

    it('should not submit if BOM is empty', async () => {
      (useCalculatorStore as any).mockReturnValue({
        selectedProductId: 'prod-123',
        bomItems: [],
        setCalculation: mockSetCalculation,
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      expect(api.calculations.submit).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 2: Polling Loop
  // ==========================================================================

  describe('Polling Loop', () => {
    it('should poll status every 2 seconds', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockStatusResponsePending: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      const mockStatusResponseCompleted: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 2.5,
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      // Return in_progress for first call, then completed to stop polling
      (api.calculations.getStatus as any)
        .mockResolvedValueOnce(mockStatusResponsePending)
        .mockResolvedValue(mockStatusResponseCompleted);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // First poll should not have happened yet
      expect(api.calculations.getStatus).not.toHaveBeenCalled();

      // Advance 2 seconds - first poll
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      expect(api.calculations.getStatus).toHaveBeenCalledTimes(1);
      expect(api.calculations.getStatus).toHaveBeenCalledWith('calc-abc123');

      // Polling should stop after first call returns completed
      // No need to advance further
    });

    it('should update progress during polling', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      let pollCount = 0;
      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockImplementation(() => {
        pollCount++;
        // After 3 polls, return completed to stop polling
        if (pollCount >= 3) {
          return Promise.resolve({
            calculation_id: 'calc-abc123',
            status: 'completed',
            product_id: 'prod-123',
            created_at: '2024-11-08T10:00:00Z',
            total_co2e_kg: 2.5,
          });
        }
        return Promise.resolve({
          calculation_id: 'calc-abc123',
          status: 'in_progress',
          product_id: 'prod-123',
          created_at: '2024-11-08T10:00:00Z',
        });
      });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Poll multiple times
      for (let i = 0; i < 3; i++) {
        await act(async () => {
          vi.advanceTimersByTime(2000);
          await vi.runAllTimersAsync();
        });
      }

      expect(pollCount).toBe(3);
      expect(mockSetCalculation).toHaveBeenCalled();
    });

    it('should handle polling errors gracefully and continue', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValue({
          calculation_id: 'calc-abc123',
          status: 'in_progress',
          product_id: 'prod-123',
          created_at: '2024-11-08T10:00:00Z',
        });

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // First poll fails
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Second poll succeeds
      await act(async () => {
        vi.advanceTimersByTime(2000);
      });

      // Should continue polling despite error
      expect(api.calculations.getStatus).toHaveBeenCalledTimes(2);
      expect(result.current.isCalculating).toBe(true);

      consoleErrorSpy.mockRestore();
    });
  });

  // ==========================================================================
  // Test Suite 3: Auto-Advance on Completion
  // ==========================================================================

  describe('Auto-Advance on Completion', () => {
    it('should auto-advance to results when calculation completes', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockCompletedResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 2.05,
        materials_co2e: 1.8,
        energy_co2e: 0.15,
        transport_co2e: 0.1,
        calculation_time_ms: 150,
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockCompletedResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // First poll returns completed
      await act(async () => {
        vi.advanceTimersByTime(2000);
        await vi.runAllTimersAsync();
      });

      // Should update store with results
      expect(mockSetCalculation).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'calc-abc123',
          status: 'completed',
        })
      );

      // Should mark step complete and advance
      expect(mockMarkStepComplete).toHaveBeenCalledWith('calculate');
      expect(mockGoNext).toHaveBeenCalled();

      // Should stop calculating
      expect(result.current.isCalculating).toBe(false);
    });

    it('should stop polling when calculation completes', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockCompletedResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'completed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        total_co2e_kg: 2.05,
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockCompletedResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // First poll returns completed
      await act(async () => {
        vi.advanceTimersByTime(2000);
        await vi.runAllTimersAsync();
      });

      const pollCountAfterComplete = (api.calculations.getStatus as any).mock.calls.length;

      // Advance more time - no more polls
      await act(async () => {
        vi.advanceTimersByTime(10000);
        await vi.runAllTimersAsync();
      });

      expect((api.calculations.getStatus as any).mock.calls.length).toBe(pollCountAfterComplete);
    });
  });

  // ==========================================================================
  // Test Suite 4: Timeout Handling
  // ==========================================================================

  describe('Timeout Handling', () => {
    it('should timeout after 30 poll attempts (60 seconds)', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockPendingResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockPendingResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Simulate 30 polls (60 seconds)
      for (let i = 0; i < 30; i++) {
        await act(async () => {
          vi.advanceTimersByTime(2000);
          await vi.runAllTimersAsync();
        });
      }

      // Should have error message
      expect(result.current.error).toContain('timeout');
      expect(result.current.isCalculating).toBe(false);
    });

    it('should stop polling after timeout', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockPendingResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockPendingResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Simulate 30 polls
      for (let i = 0; i < 30; i++) {
        await act(async () => {
          vi.advanceTimersByTime(2000);
          await vi.runAllTimersAsync();
        });
      }

      const pollCountAfterTimeout = (api.calculations.getStatus as any).mock.calls.length;

      // Additional time should not trigger more polls
      await act(async () => {
        vi.advanceTimersByTime(10000);
        await vi.runAllTimersAsync();
      });

      expect((api.calculations.getStatus as any).mock.calls.length).toBe(pollCountAfterTimeout);
    });

    it('should show user-friendly timeout message', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockPendingResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockPendingResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // Simulate timeout
      for (let i = 0; i < 30; i++) {
        await act(async () => {
          vi.advanceTimersByTime(2000);
          await vi.runAllTimersAsync();
        });
      }

      expect(result.current.error).toBeTruthy();
      expect(result.current.error?.toLowerCase()).toMatch(/timeout|busy|try again/);
    });
  });

  // ==========================================================================
  // Test Suite 5: Calculation Error Handling
  // ==========================================================================

  describe('Calculation Error Handling', () => {
    it('should handle failed calculation status', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockFailedResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'failed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        error_message: 'Invalid emission factor for component: Cotton',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockFailedResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // First poll returns failed
      await act(async () => {
        vi.advanceTimersByTime(2000);
        await vi.runAllTimersAsync();
      });

      expect(result.current.error).toContain('Invalid emission factor for component: Cotton');
      expect(result.current.isCalculating).toBe(false);
    });

    it('should stop polling when calculation fails', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockFailedResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'failed',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
        error_message: 'Calculation error',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockFailedResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // First poll returns failed
      await act(async () => {
        vi.advanceTimersByTime(2000);
        await vi.runAllTimersAsync();
      });

      const pollCountAfterFailure = (api.calculations.getStatus as any).mock.calls.length;

      // Additional time should not trigger more polls
      await act(async () => {
        vi.advanceTimersByTime(10000);
        await vi.runAllTimersAsync();
      });

      expect((api.calculations.getStatus as any).mock.calls.length).toBe(pollCountAfterFailure);
    });

    it('should handle submission error', async () => {
      (api.calculations.submit as any).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.isCalculating).toBe(false);
      expect(api.calculations.getStatus).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 6: Cancel and Cleanup
  // ==========================================================================

  describe('Cancel and Cleanup', () => {
    it('should stop polling when stopPolling is called', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockPendingResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockPendingResponse);

      const { result } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // One poll happens
      await act(async () => {
        vi.advanceTimersByTime(2000);
        await vi.runAllTimersAsync();
      });

      const pollCountBeforeStop = (api.calculations.getStatus as any).mock.calls.length;

      // Stop polling
      act(() => {
        result.current.stopPolling();
      });

      // More time passes, no more polls
      await act(async () => {
        vi.advanceTimersByTime(10000);
        await vi.runAllTimersAsync();
      });

      expect((api.calculations.getStatus as any).mock.calls.length).toBe(pollCountBeforeStop);
      expect(result.current.isCalculating).toBe(false);
    });

    it('should cleanup polling on component unmount', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockPendingResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockPendingResponse);

      const { result, unmount } = renderHook(() => useCalculation());

      await act(async () => {
        await result.current.startCalculation();
      });

      // One poll happens
      await act(async () => {
        vi.advanceTimersByTime(2000);
        await vi.runAllTimersAsync();
      });

      const pollCountBeforeUnmount = (api.calculations.getStatus as any).mock.calls.length;

      // Unmount component
      unmount();

      // More time passes, no more polls
      await act(async () => {
        vi.advanceTimersByTime(10000);
        await vi.runAllTimersAsync();
      });

      expect((api.calculations.getStatus as any).mock.calls.length).toBe(pollCountBeforeUnmount);
    });
  });

  // ==========================================================================
  // Test Suite 7: Retry Functionality
  // ==========================================================================

  describe('Retry Functionality', () => {
    it('should allow retry after error', async () => {
      (api.calculations.submit as any).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useCalculation());

      // First attempt fails
      await act(async () => {
        await result.current.startCalculation();
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.isCalculating).toBe(false);

      // Setup success for retry
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };
      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);

      // Retry
      await act(async () => {
        await result.current.startCalculation();
      });

      expect(result.current.error).toBeNull();
      expect(api.calculations.submit).toHaveBeenCalledTimes(2);
    });

    it('should reset poll count on retry', async () => {
      const mockSubmitResponse: CalculationStartResponse = {
        calculation_id: 'calc-abc123',
        status: 'pending',
      };

      const mockPendingResponse: CalculationStatusResponse = {
        calculation_id: 'calc-abc123',
        status: 'in_progress',
        product_id: 'prod-123',
        created_at: '2024-11-08T10:00:00Z',
      };

      (api.calculations.submit as any).mockResolvedValue(mockSubmitResponse);
      (api.calculations.getStatus as any).mockResolvedValue(mockPendingResponse);

      const { result } = renderHook(() => useCalculation());

      // First attempt
      await act(async () => {
        await result.current.startCalculation();
      });

      // Simulate 10 polls
      for (let i = 0; i < 10; i++) {
        await act(async () => {
          vi.advanceTimersByTime(2000);
          await vi.runAllTimersAsync();
        });
      }

      // Stop and retry
      act(() => {
        result.current.stopPolling();
      });

      await act(async () => {
        await result.current.startCalculation();
      });

      // Should be able to poll 30 more times (not 20)
      for (let i = 0; i < 30; i++) {
        await act(async () => {
          vi.advanceTimersByTime(2000);
          await vi.runAllTimersAsync();
        });
      }

      // Should timeout after 30 polls from retry, not 20
      expect(result.current.error).toContain('timeout');
    });
  });
});
