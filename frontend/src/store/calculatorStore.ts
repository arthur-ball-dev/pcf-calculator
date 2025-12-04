/**
 * Calculator Store
 *
 * Manages calculator state for the PCF Calculator including:
 * - Product selection
 * - Bill of Materials (BOM) editing
 * - Calculation process and results
 * - Loading states
 * - Undo/Redo functionality
 *
 * Integrates with wizardStore to trigger step completion when:
 * - Product is selected (completes 'select' step)
 * - Calculation completes (completes 'calculate' step and advances to 'results')
 *
 * UPDATED: TASK-FE-020 - UUID type system migration
 * - selectedProductId: string | null (was number | null)
 * - setSelectedProduct parameter: string | null (was number | null)
 * - All UUID fields now use string types (no parseInt conversion)
 *
 * UPDATED: TASK-FE-P5-003 - Added undo/redo middleware integration
 * - Undo/redo for BOM editing operations
 * - History limit of 50 entries
 * - 500ms debounce for rapid changes
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { CalculatorState, BOMItem, Product, Calculation } from '../types/store.types';
import { useWizardStore } from './wizardStore';
import { undoRedo, type UndoRedoActions } from './middleware/undoRedoMiddleware';

// ============================================================================
// Extended State Type (with Undo/Redo)
// ============================================================================

type CalculatorStoreState = CalculatorState & UndoRedoActions;

// ============================================================================
// Initial State Values
// ============================================================================

const getInitialStateValues = () => ({
  selectedProductId: null as string | null,
  selectedProduct: null as Product | null,
  bomItems: [] as BOMItem[],
  hasUnsavedChanges: false,
  calculation: null as Calculation | null,
  isLoadingProducts: false,
  isLoadingBOM: false,
});

// ============================================================================
// Store Implementation
// ============================================================================

export const useCalculatorStore = create<CalculatorStoreState>()(
  devtools(
    undoRedo(
      (set, _get) => ({
        // ================================================================
        // Initial State
        // ================================================================
        ...getInitialStateValues(),

        // ================================================================
        // Product Actions
        // ================================================================
        setSelectedProduct: (productId: string | null) => {
          // Runtime type validation to prevent number coercion (TASK-FE-020)
          // TypeScript cannot prevent this at runtime, so we validate explicitly
          if (productId !== null && typeof productId !== 'string') {
            console.warn(
              '[CalculatorStore] Invalid product ID type. Expected string or null, got:',
              typeof productId
            );
            return; // Reject non-string values
          }

          set((state) => {
            state.selectedProductId = productId;
          });

          // Trigger wizard validation
          if (productId !== null) {
            useWizardStore.getState().markStepComplete('select');
          } else {
            useWizardStore.getState().markStepIncomplete('select');
          }
        },

        setSelectedProductDetails: (product: Product | null) => {
          set((state) => {
            state.selectedProduct = product;
          });
        },

        // ================================================================
        // BOM Actions
        // ================================================================
        setBomItems: (items: BOMItem[]) => {
          set((state) => {
            state.bomItems = items;
            state.hasUnsavedChanges = true;
          });
        },

        updateBomItem: (id: string, updates: Partial<BOMItem>) => {
          set((state) => {
            const itemIndex = state.bomItems.findIndex((item) => item.id === id);
            if (itemIndex !== -1) {
              Object.assign(state.bomItems[itemIndex], updates);
              state.hasUnsavedChanges = true;
            }
          });
        },

        addBomItem: (item: BOMItem) => {
          set((state) => {
            state.bomItems.push(item);
            state.hasUnsavedChanges = true;
          });
        },

        removeBomItem: (id: string) => {
          set((state) => {
            const itemIndex = state.bomItems.findIndex((item) => item.id === id);
            if (itemIndex !== -1) {
              state.bomItems.splice(itemIndex, 1);
              state.hasUnsavedChanges = true;
            }
          });
        },

        // ================================================================
        // Calculation Actions
        // ================================================================
        setCalculation: (calculation: Calculation | null) => {
          set((state) => {
            state.calculation = calculation;
          });

          // If calculation completed, trigger wizard advancement
          if (calculation?.status === 'completed') {
            useWizardStore.getState().markStepComplete('calculate');
            useWizardStore.getState().goNext();
          }
        },

        // ================================================================
        // Loading Actions
        // ================================================================
        setLoadingProducts: (loading: boolean) => {
          set((state) => {
            state.isLoadingProducts = loading;
          });
        },

        setLoadingBOM: (loading: boolean) => {
          set((state) => {
            state.isLoadingBOM = loading;
          });
        },

        // ================================================================
        // Reset - resets state and clears undo/redo history
        // ================================================================
        reset: () => {
          // First clear history to prevent the reset from being tracked
          useCalculatorStore.getState().clearHistory();

          // Then reset state values
          set((state) => {
            const initial = getInitialStateValues();
            state.selectedProductId = initial.selectedProductId;
            state.selectedProduct = initial.selectedProduct;
            state.bomItems = initial.bomItems;
            state.hasUnsavedChanges = initial.hasUnsavedChanges;
            state.calculation = initial.calculation;
            // Note: Loading states are NOT reset (transient state)
          });

          // Clear history again to remove the reset change from history
          useCalculatorStore.getState().clearHistory();
        },
      }),
      {
        limit: 50,
        debounceMs: 500,
      }
    ),
    { name: 'CalculatorStore' } // DevTools name
  )
);
