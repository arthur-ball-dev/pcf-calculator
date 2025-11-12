/**
 * Calculator Store Tests
 *
 * Tests for calculator state management including:
 * - Product selection
 * - BOM items management
 * - Calculation data storage
 * - Loading states
 * - Integration with wizard store
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';

describe('CalculatorStore', () => {
  beforeEach(() => {
    // Reset both stores before each test
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
  });

  describe('Initial State', () => {
    test('initializes with null selectedProductId', () => {
      const { selectedProductId } = useCalculatorStore.getState();
      expect(selectedProductId).toBeNull();
    });

    test('initializes with null selectedProduct', () => {
      const { selectedProduct } = useCalculatorStore.getState();
      expect(selectedProduct).toBeNull();
    });

    test('initializes with empty bomItems array', () => {
      const { bomItems } = useCalculatorStore.getState();
      expect(bomItems).toEqual([]);
    });

    test('initializes with hasUnsavedChanges false', () => {
      const { hasUnsavedChanges } = useCalculatorStore.getState();
      expect(hasUnsavedChanges).toBe(false);
    });

    test('initializes with null calculation', () => {
      const { calculation } = useCalculatorStore.getState();
      expect(calculation).toBeNull();
    });

    test('initializes with loading states false', () => {
      const { isLoadingProducts, isLoadingBOM } = useCalculatorStore.getState();
      expect(isLoadingProducts).toBe(false);
      expect(isLoadingBOM).toBe(false);
    });
  });

  describe('Product Selection', () => {
    test('setSelectedProduct updates selectedProductId', () => {
      const { setSelectedProduct } = useCalculatorStore.getState();

      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");

      const state = useCalculatorStore.getState();
      expect(state.selectedProductId).toBe("471fe408a2604386bae572d9fc9a6b5c");
    });

    test('setSelectedProduct marks wizard select step complete', () => {
      const { setSelectedProduct } = useCalculatorStore.getState();

      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");

      const wizardState = useWizardStore.getState();
      expect(wizardState.completedSteps).toContain('select');
    });

    test('setSelectedProduct with null clears selection', () => {
      const { setSelectedProduct } = useCalculatorStore.getState();

      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");
      setSelectedProduct(null);

      const state = useCalculatorStore.getState();
      expect(state.selectedProductId).toBeNull();
    });

    test('setSelectedProduct updates product details', () => {
      const { setSelectedProduct, setSelectedProductDetails } = useCalculatorStore.getState();

      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");

      const mockProduct = {
        id: "471fe408a2604386bae572d9fc9a6b5c",
        code: 'TEST-001',
        name: 'Test Product',
        category: 'Electronics',
        unit: 'unit' as const,
        is_finished_product: true
      };

      setSelectedProductDetails(mockProduct);

      const state = useCalculatorStore.getState();
      expect(state.selectedProduct).toEqual(mockProduct);
    });
  });

  describe('BOM Items Management', () => {
    test('setBomItems updates bomItems array', () => {
      const { setBomItems } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        },
        {
          id: '2',
          name: 'Polyester',
          quantity: 0.3,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-456def"
        }
      ];

      setBomItems(items);

      const state = useCalculatorStore.getState();
      expect(state.bomItems).toEqual(items);
    });

    test('setBomItems sets hasUnsavedChanges to true', () => {
      const { setBomItems } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        }
      ];

      setBomItems(items);

      const state = useCalculatorStore.getState();
      expect(state.hasUnsavedChanges).toBe(true);
    });

    test('updateBomItem updates single item in array', () => {
      const { setBomItems, updateBomItem } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        }
      ];

      setBomItems(items);
      updateBomItem('1', { quantity: 0.8 });

      const state = useCalculatorStore.getState();
      expect(state.bomItems[0].quantity).toBe(0.8);
      expect(state.bomItems[0].name).toBe('Cotton');
    });

    test('updateBomItem sets hasUnsavedChanges to true', () => {
      const { setBomItems, updateBomItem } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        }
      ];

      setBomItems(items);
      // Reset unsaved changes flag
      useCalculatorStore.setState({ hasUnsavedChanges: false });

      updateBomItem('1', { quantity: 0.8 });

      const state = useCalculatorStore.getState();
      expect(state.hasUnsavedChanges).toBe(true);
    });

    test('addBomItem adds new item to array', () => {
      const { addBomItem } = useCalculatorStore.getState();

      const newItem = {
        id: '1',
        name: 'Cotton',
        quantity: 0.5,
        unit: 'kg',
        category: 'material' as const,
        emissionFactorId: "ef-uuid-123abc"
      };

      addBomItem(newItem);

      const state = useCalculatorStore.getState();
      expect(state.bomItems).toContain(newItem);
      expect(state.bomItems.length).toBe(1);
    });

    test('removeBomItem removes item from array', () => {
      const { setBomItems, removeBomItem } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        },
        {
          id: '2',
          name: 'Polyester',
          quantity: 0.3,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-456def"
        }
      ];

      setBomItems(items);
      removeBomItem('1');

      const state = useCalculatorStore.getState();
      expect(state.bomItems.length).toBe(1);
      expect(state.bomItems[0].id).toBe('2');
    });
  });

  describe('Calculation Management', () => {
    test('setCalculation updates calculation data', () => {
      const { setCalculation } = useCalculatorStore.getState();

      const mockCalculation = {
        id: 'calc-123',
        product_id: "471fe408a2604386bae572d9fc9a6b5c",
        status: 'pending' as const,
        total_co2e: 0,
        materials_co2e: 0,
        energy_co2e: 0,
        transport_co2e: 0,
        waste_co2e: 0,
        calculation_type: 'cradle_to_gate' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setCalculation(mockCalculation);

      const state = useCalculatorStore.getState();
      expect(state.calculation).toEqual(mockCalculation);
    });

    test('setCalculation with completed status marks wizard step complete', () => {
      const { setCalculation } = useCalculatorStore.getState();

      const mockCalculation = {
        id: 'calc-123',
        product_id: "471fe408a2604386bae572d9fc9a6b5c",
        status: 'completed' as const,
        total_co2e: 150.5,
        materials_co2e: 100,
        energy_co2e: 30,
        transport_co2e: 15.5,
        waste_co2e: 5,
        calculation_type: 'cradle_to_gate' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setCalculation(mockCalculation);

      const wizardState = useWizardStore.getState();
      expect(wizardState.completedSteps).toContain('calculate');
    });

    test('setCalculation with completed status advances wizard to results', () => {
      const { setCalculation } = useCalculatorStore.getState();

      // Set up wizard to be at calculate step
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().setStep('calculate');

      const mockCalculation = {
        id: 'calc-123',
        product_id: "471fe408a2604386bae572d9fc9a6b5c",
        status: 'completed' as const,
        total_co2e: 150.5,
        materials_co2e: 100,
        energy_co2e: 30,
        transport_co2e: 15.5,
        waste_co2e: 5,
        calculation_type: 'cradle_to_gate' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setCalculation(mockCalculation);

      const wizardState = useWizardStore.getState();
      expect(wizardState.currentStep).toBe('results');
    });

    test('setCalculation with pending status does not advance wizard', () => {
      const { setCalculation } = useCalculatorStore.getState();

      const mockCalculation = {
        id: 'calc-123',
        product_id: "471fe408a2604386bae572d9fc9a6b5c",
        status: 'pending' as const,
        total_co2e: 0,
        materials_co2e: 0,
        energy_co2e: 0,
        transport_co2e: 0,
        waste_co2e: 0,
        calculation_type: 'cradle_to_gate' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setCalculation(mockCalculation);

      const wizardState = useWizardStore.getState();
      expect(wizardState.currentStep).toBe('select');
    });
  });

  describe('Loading States', () => {
    test('setLoadingProducts updates isLoadingProducts', () => {
      const { setLoadingProducts } = useCalculatorStore.getState();

      setLoadingProducts(true);

      const state = useCalculatorStore.getState();
      expect(state.isLoadingProducts).toBe(true);
    });

    test('setLoadingBOM updates isLoadingBOM', () => {
      const { setLoadingBOM } = useCalculatorStore.getState();

      setLoadingBOM(true);

      const state = useCalculatorStore.getState();
      expect(state.isLoadingBOM).toBe(true);
    });
  });

  describe('Reset Functionality', () => {
    test('reset clears all calculator state', () => {
      const {
        setSelectedProduct,
        setBomItems,
        setCalculation,
        reset
      } = useCalculatorStore.getState();

      // Set up state
      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");
      setBomItems([
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material',
          emissionFactorId: "ef-uuid-123abc"
        }
      ]);
      setCalculation({
        id: 'calc-123',
        product_id: "471fe408a2604386bae572d9fc9a6b5c",
        status: 'completed',
        total_co2e: 150.5,
        materials_co2e: 100,
        energy_co2e: 30,
        transport_co2e: 15.5,
        waste_co2e: 5,
        calculation_type: 'cradle_to_gate',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });

      // Reset
      reset();

      const state = useCalculatorStore.getState();
      expect(state.selectedProductId).toBeNull();
      expect(state.selectedProduct).toBeNull();
      expect(state.bomItems).toEqual([]);
      expect(state.hasUnsavedChanges).toBe(false);
      expect(state.calculation).toBeNull();
    });

    test('reset does not clear loading states', () => {
      const { setLoadingProducts, reset } = useCalculatorStore.getState();

      setLoadingProducts(true);
      reset();

      const state = useCalculatorStore.getState();
      // Loading states are transient and not reset
      expect(state.isLoadingProducts).toBe(true);
    });
  });

  describe('Wizard Integration', () => {
    test('product selection triggers wizard validation', () => {
      const { setSelectedProduct } = useCalculatorStore.getState();

      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");

      const wizardState = useWizardStore.getState();
      expect(wizardState.completedSteps).toContain('select');
      expect(wizardState.canProceed).toBe(true);
    });

    test('clearing product selection marks wizard step incomplete', () => {
      const { setSelectedProduct } = useCalculatorStore.getState();

      setSelectedProduct("471fe408a2604386bae572d9fc9a6b5c");
      setSelectedProduct(null);

      const wizardState = useWizardStore.getState();
      expect(wizardState.completedSteps).not.toContain('select');
    });

    test('completed calculation auto-advances wizard', () => {
      const { setCalculation } = useCalculatorStore.getState();

      // Setup wizard state
      useWizardStore.getState().markStepComplete('select');
      useWizardStore.getState().markStepComplete('edit');
      useWizardStore.getState().setStep('calculate');

      const mockCalculation = {
        id: 'calc-123',
        product_id: "471fe408a2604386bae572d9fc9a6b5c",
        status: 'completed' as const,
        total_co2e: 150.5,
        materials_co2e: 100,
        energy_co2e: 30,
        transport_co2e: 15.5,
        waste_co2e: 5,
        calculation_type: 'cradle_to_gate' as const,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };

      setCalculation(mockCalculation);

      const wizardState = useWizardStore.getState();
      expect(wizardState.currentStep).toBe('results');
    });
  });

  describe('Data Validation', () => {
    test('bomItems maintains immutability', () => {
      const { setBomItems, updateBomItem } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        }
      ];

      setBomItems(items);
      const originalItems = useCalculatorStore.getState().bomItems;

      updateBomItem('1', { quantity: 0.8 });

      // Original array should not be mutated
      expect(items[0].quantity).toBe(0.5);
      // Store should have new array
      expect(useCalculatorStore.getState().bomItems).not.toBe(originalItems);
    });

    test('updateBomItem handles non-existent item gracefully', () => {
      const { setBomItems, updateBomItem } = useCalculatorStore.getState();

      const items = [
        {
          id: '1',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material' as const,
          emissionFactorId: "ef-uuid-123abc"
        }
      ];

      setBomItems(items);
      updateBomItem('999', { quantity: 0.8 });

      const state = useCalculatorStore.getState();
      // Should not modify array if item not found
      expect(state.bomItems.length).toBe(1);
      expect(state.bomItems[0].quantity).toBe(0.5);
    });
  });
});
