/**
 * Scenario Store
 *
 * Manages scenario comparison state for the PCF Calculator.
 * Implements scenario CRUD operations, comparison list management,
 * and baseline scenario designation.
 *
 * Features:
 * - Scenario creation and cloning
 * - Comparison list management (add/remove/clear)
 * - Baseline scenario designation
 * - Selectors for filtered scenario data
 * - DevTools integration for debugging
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { v4 as uuidv4 } from 'uuid';

// ================================================================
// Type Definitions
// ================================================================

export interface BOMEntry {
  id: string;
  component_name: string;
  quantity: number;
  unit: string;
  emissions?: number;
}

export interface CalculationParameters {
  transportDistance: number;
  energySource: string;
  productionVolume: number;
}

export interface CalculationResults {
  total_emissions: number;
  breakdown?: Record<string, number>;
}

export interface Scenario {
  id: string;
  name: string;
  productId: string;
  bomEntries: BOMEntry[];
  parameters: CalculationParameters;
  results: CalculationResults | null;
  createdAt: Date;
  isBaseline: boolean;
}

interface ScenarioStoreState {
  scenarios: Scenario[];
  activeScenarioId: string | null;
  comparisonScenarioIds: string[];
}

interface ScenarioStoreActions {
  // Actions
  createScenario: (name: string, productId: string, baseScenarioId?: string) => string;
  updateScenario: (id: string, updates: Partial<Scenario>) => void;
  deleteScenario: (id: string) => void;
  cloneScenario: (id: string, newName: string) => string;
  setActiveScenario: (id: string) => void;
  addToComparison: (id: string) => void;
  removeFromComparison: (id: string) => void;
  clearComparison: () => void;
  setAsBaseline: (id: string) => void;

  // Selectors
  getScenario: (id: string) => Scenario | undefined;
  getActiveScenario: () => Scenario | undefined;
  getComparisonScenarios: () => Scenario[];
  getBaseline: () => Scenario | undefined;
}

export type ScenarioStore = ScenarioStoreState & ScenarioStoreActions;

// ================================================================
// Default Values
// ================================================================

const DEFAULT_PARAMETERS: CalculationParameters = {
  transportDistance: 0,
  energySource: 'grid',
  productionVolume: 1,
};

// ================================================================
// Store Implementation
// ================================================================

export const useScenarioStore = create<ScenarioStore>()(
  devtools(
    immer((set, get) => ({
      // ================================================================
      // Initial State
      // ================================================================
      scenarios: [],
      activeScenarioId: null,
      comparisonScenarioIds: [],

      // ================================================================
      // Actions
      // ================================================================

      createScenario: (name: string, productId: string, baseScenarioId?: string): string => {
        const state = get();
        const baseScenario = baseScenarioId
          ? state.getScenario(baseScenarioId)
          : undefined;

        const id = uuidv4();
        const isFirstScenario = state.scenarios.length === 0;

        set((draft) => {
          draft.scenarios.push({
            id,
            name,
            productId,
            bomEntries: baseScenario?.bomEntries ? [...baseScenario.bomEntries] : [],
            parameters: baseScenario?.parameters
              ? { ...baseScenario.parameters }
              : { ...DEFAULT_PARAMETERS },
            results: null,
            createdAt: new Date(),
            isBaseline: isFirstScenario,
          });
          draft.activeScenarioId = id;
        });

        return id;
      },

      updateScenario: (id: string, updates: Partial<Scenario>): void => {
        set((draft) => {
          const index = draft.scenarios.findIndex((s) => s.id === id);
          if (index !== -1) {
            draft.scenarios[index] = {
              ...draft.scenarios[index],
              ...updates,
            };
          }
        });
      },

      deleteScenario: (id: string): void => {
        set((draft) => {
          // Remove from scenarios array
          draft.scenarios = draft.scenarios.filter((s) => s.id !== id);

          // Remove from comparison list
          draft.comparisonScenarioIds = draft.comparisonScenarioIds.filter(
            (cid) => cid !== id
          );

          // Clear active scenario if it was deleted
          if (draft.activeScenarioId === id) {
            draft.activeScenarioId = null;
          }
        });
      },

      cloneScenario: (id: string, newName: string): string => {
        const state = get();
        const original = state.getScenario(id);

        if (!original) {
          return '';
        }

        const newId = uuidv4();

        set((draft) => {
          draft.scenarios.push({
            id: newId,
            name: newName,
            productId: original.productId,
            bomEntries: original.bomEntries.map((entry) => ({ ...entry })),
            parameters: { ...original.parameters },
            results: null, // Results are not copied - must recalculate
            createdAt: new Date(),
            isBaseline: false, // Cloned scenarios are never baseline
          });
          draft.activeScenarioId = newId;
        });

        return newId;
      },

      setActiveScenario: (id: string): void => {
        const state = get();
        const scenario = state.getScenario(id);

        if (scenario) {
          set((draft) => {
            draft.activeScenarioId = id;
          });
        }
      },

      addToComparison: (id: string): void => {
        set((draft) => {
          if (!draft.comparisonScenarioIds.includes(id)) {
            draft.comparisonScenarioIds.push(id);
          }
        });
      },

      removeFromComparison: (id: string): void => {
        set((draft) => {
          draft.comparisonScenarioIds = draft.comparisonScenarioIds.filter(
            (cid) => cid !== id
          );
        });
      },

      clearComparison: (): void => {
        set((draft) => {
          draft.comparisonScenarioIds = [];
        });
      },

      setAsBaseline: (id: string): void => {
        const state = get();
        const scenario = state.getScenario(id);

        if (!scenario) {
          return;
        }

        set((draft) => {
          // Remove baseline flag from all scenarios
          draft.scenarios.forEach((s) => {
            s.isBaseline = false;
          });

          // Set new baseline
          const targetIndex = draft.scenarios.findIndex((s) => s.id === id);
          if (targetIndex !== -1) {
            draft.scenarios[targetIndex].isBaseline = true;
          }
        });
      },

      // ================================================================
      // Selectors
      // ================================================================

      getScenario: (id: string): Scenario | undefined => {
        return get().scenarios.find((s) => s.id === id);
      },

      getActiveScenario: (): Scenario | undefined => {
        const state = get();
        if (!state.activeScenarioId) return undefined;
        return state.scenarios.find((s) => s.id === state.activeScenarioId);
      },

      getComparisonScenarios: (): Scenario[] => {
        const state = get();
        return state.scenarios.filter((s) =>
          state.comparisonScenarioIds.includes(s.id)
        );
      },

      getBaseline: (): Scenario | undefined => {
        return get().scenarios.find((s) => s.isBaseline);
      },
    })),
    { name: 'ScenarioStore' }
  )
);
