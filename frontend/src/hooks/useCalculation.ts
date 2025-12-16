/**
 * useCalculation Hook
 *
 * Manages PCF calculation submission and polling workflow:
 * - Submits calculation request (POST /calculate)
 * - Polls calculation status every 2 seconds (GET /calculations/{id})
 * - Handles timeout after 30 polls (60 seconds)
 * - Auto-advances to results when complete
 * - Manages error states and retry logic
 * - Cleanup on unmount
 *
 * TASK-FE-007: Calculate Flow with Polling
 */

import { useState, useEffect, useRef } from 'react';
import api from '@/services/api';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { Calculation } from '@/types/store.types';

const MAX_POLL_ATTEMPTS = 30; // 30 polls × 2 seconds = 60 seconds timeout
const POLL_INTERVAL_MS = 2000; // Poll every 2 seconds

export interface UseCalculationReturn {
  isCalculating: boolean;
  error: string | null;
  elapsedSeconds: number;
  startCalculation: () => Promise<void>;
  stopPolling: () => void;
}

/**
 * Custom hook for managing calculation submission and polling
 *
 * @returns Calculation state and control functions
 */
export function useCalculation(): UseCalculationReturn {
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollCountRef = useRef(0);
  const startTimeRef = useRef<number>(0);

  const { selectedProductId, bomItems, setCalculation } = useCalculatorStore();
  const { markStepComplete, goNext } = useWizardStore();

  /**
   * Stop polling and reset state
   */
  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsCalculating(false);
    setElapsedSeconds(0);
    startTimeRef.current = 0;
  };

  /**
   * Poll calculation status
   *
   * @param calculationId - Calculation UUID to poll
   */
  const pollStatus = async (calculationId: string) => {
    pollCountRef.current++;

    // Update elapsed time
    if (startTimeRef.current > 0) {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      setElapsedSeconds(elapsed);
    }

    // Check for timeout
    if (pollCountRef.current > MAX_POLL_ATTEMPTS) {
      stopPolling();
      setError('Calculation timeout. The server is busy, please try again.');
      return;
    }

    try {
      const status = await api.calculations.getStatus(calculationId);

      if (status.status === 'completed') {
        // Calculation complete
        stopPolling();

        const calculation: Calculation = {
          id: calculationId,
          status: 'completed',
          product_id: status.product_id || undefined,
          created_at: status.created_at || undefined,
          total_co2e_kg: status.total_co2e_kg,
          materials_co2e: status.materials_co2e,
          energy_co2e: status.energy_co2e,
          transport_co2e: status.transport_co2e,
          calculation_time_ms: status.calculation_time_ms,
          breakdown: status.breakdown,
        };

        setCalculation(calculation);
        markStepComplete('calculate');
        goNext(); // Auto-advance to results
      } else if (status.status === 'failed') {
        // Calculation failed
        stopPolling();
        setError(status.error_message || 'Calculation failed');
      } else {
        // Still processing - update status
        const calculation: Calculation = {
          id: calculationId,
          status: status.status,
          product_id: status.product_id || undefined,
          created_at: status.created_at || undefined,
        };

        setCalculation(calculation);
      }
    } catch (err) {
      // Log error but continue polling (transient network errors)
      console.error('Polling error:', err);
    }
  };

  /**
   * Start calculation submission and polling
   */
  const startCalculation = async () => {
    // Validation
    if (!selectedProductId || !bomItems.length) {
      return;
    }

    // Reset state
    setIsCalculating(true);
    setError(null);
    setElapsedSeconds(0);
    pollCountRef.current = 0;
    startTimeRef.current = Date.now();

    try {
      // Submit calculation request
      const response = await api.calculations.submit({
        product_id: String(selectedProductId),
      });

      const calculationId = response.calculation_id;

      // Update store with pending calculation
      setCalculation({
        id: calculationId,
        status: 'pending',
      });

      // Start polling
      pollIntervalRef.current = setInterval(() => {
        pollStatus(calculationId);
      }, POLL_INTERVAL_MS);
    } catch (err) {
      setIsCalculating(false);
      setError('Failed to submit calculation. Please try again.');
      console.error('Calculation submission error:', err);
    }
  };

  /**
   * Cleanup polling on unmount
   */
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []);

  return {
    isCalculating,
    error,
    elapsedSeconds,
    startCalculation,
    stopPolling,
  };
}
