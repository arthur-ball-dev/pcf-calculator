/**
 * Calculator Store
 *
 * Manages calculator state for the PCF Calculator including:
 * - Product selection
 * - Bill of Materials (BOM) editing
 * - Calculation process and results
 * - Loading states
 *
 * Integrates with wizardStore to trigger step completion when:
 * - Product is selected (completes 'select' step)
 * - Calculation completes (completes 'calculate' step and advances to 'results')
 *
 * UPDATED: TASK-FE-020 - UUID type system migration
 * - selectedProductId: string | null (was number | null)
 * - setSelectedProduct parameter: string | null (was number | null)
 * - All UUID fields now use string types (no parseInt conversion)
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { CalculatorState, BOMItem, Product, Calculation } from '../types/store.types';
import { useWizardStore } from './wizardStore';

export const useCalculatorStore = create<CalculatorState>()(
  devtools(
    (set, get) => ({
      // ================================================================
      // Initial State
      // ================================================================
      selectedProductId: null,
      selectedProduct: null,
      bomItems: [],
      hasUnsavedChanges: false,
      calculation: null,
      isLoadingProducts: false,
      isLoadingBOM: false,

      // ================================================================
      // Product Actions
      // ================================================================
      setSelectedProduct: (productId: string | null) => {
        // Runtime type validation to prevent number coercion (TASK-FE-020)
        // TypeScript cannot prevent this at runtime, so we validate explicitly
        if (productId !== null && typeof productId !== 'string') {
          console.warn('[CalculatorStore] Invalid product ID type. Expected string or null, got:', typeof productId);
          return; // Reject non-string values
        }
        
        set({ selectedProductId: productId });

        // Trigger wizard validation
        if (productId !== null) {
          useWizardStore.getState().markStepComplete('select');
        } else {
          useWizardStore.getState().markStepIncomplete('select');
        }
      },

      setSelectedProductDetails: (product: Product | null) => {
        set({ selectedProduct: product });
      },

      // ================================================================
      // BOM Actions
      // ================================================================
      setBomItems: (items: BOMItem[]) => {
        set({
          bomItems: items,
          hasUnsavedChanges: true,
        });
      },

      updateBomItem: (id: string, updates: Partial<BOMItem>) => {
        set((state) => {
          const updatedItems = state.bomItems.map((item) =>
            item.id === id ? { ...item, ...updates } : item
          );

          // Only update if item was found
          const itemFound = state.bomItems.some((item) => item.id === id);
          if (!itemFound) {
            return state; // No changes
          }

          return {
            bomItems: updatedItems,
            hasUnsavedChanges: true,
          };
        });
      },

      addBomItem: (item: BOMItem) => {
        set((state) => ({
          bomItems: [...state.bomItems, item],
          hasUnsavedChanges: true,
        }));
      },

      removeBomItem: (id: string) => {
        set((state) => ({
          bomItems: state.bomItems.filter((item) => item.id !== id),
          hasUnsavedChanges: true,
        }));
      },

      // ================================================================
      // Calculation Actions
      // ================================================================
      setCalculation: (calculation: Calculation | null) => {
        set({ calculation });

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
        set({ isLoadingProducts: loading });
      },

      setLoadingBOM: (loading: boolean) => {
        set({ isLoadingBOM: loading });
      },

      // ================================================================
      // Reset
      // ================================================================
      reset: () => {
        set({
          selectedProductId: null,
          selectedProduct: null,
          bomItems: [],
          hasUnsavedChanges: false,
          calculation: null,
          // Note: Loading states are NOT reset (transient state)
        });
      },
    }),
    { name: 'CalculatorStore' } // DevTools name
  )
);
