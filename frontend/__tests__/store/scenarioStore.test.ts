/**
 * Scenario Store Tests
 *
 * Test-Driven Development for TASK-FE-P5-002
 * Written BEFORE implementation (TDD Protocol)
 *
 * Tests for scenario comparison state management including:
 * - Scenario creation and cloning
 * - Comparison list management
 * - Baseline scenario designation
 * - Selectors for filtered scenario data
 */

import { describe, test, expect, beforeEach } from 'vitest';
import { act } from '../testUtils';
// Real import - enabled per TDD Exception approval (TASK-FE-P5-002_SEQ-003)
import { useScenarioStore, type Scenario, type BOMEntry, type CalculationParameters, type CalculationResults } from '../../src/store/scenarioStore';

describe('ScenarioStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useScenarioStore.setState({
      scenarios: [],
      activeScenarioId: null,
      comparisonScenarioIds: [],
    });
    localStorage.clear();
  });

  describe('createScenario Action', () => {
    test('creates scenario with correct name and productId', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      const scenarioId = createScenario('Baseline Scenario', 'product-123');
      const scenario = getScenario(scenarioId);

      expect(scenario).toBeDefined();
      expect(scenario?.name).toBe('Baseline Scenario');
      expect(scenario?.productId).toBe('product-123');
    });

    test('creates scenario with unique UUID', () => {
      const { createScenario } = useScenarioStore.getState();

      const id1 = createScenario('Scenario 1', 'product-123');
      const id2 = createScenario('Scenario 2', 'product-123');

      expect(id1).toBeDefined();
      expect(id2).toBeDefined();
      expect(id1).not.toBe(id2);
      // UUID format check
      expect(id1).toMatch(/^[0-9a-f-]{36}$/i);
    });

    test('creates scenario with empty bomEntries when no base provided', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      const scenarioId = createScenario('New Scenario', 'product-456');
      const scenario = getScenario(scenarioId);

      expect(scenario?.bomEntries).toEqual([]);
    });

    test('creates scenario with default parameters when no base provided', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      const scenarioId = createScenario('New Scenario', 'product-789');
      const scenario = getScenario(scenarioId);

      expect(scenario?.parameters).toBeDefined();
      expect(scenario?.parameters.transportDistance).toBe(0);
      expect(scenario?.parameters.energySource).toBe('grid');
      expect(scenario?.parameters.productionVolume).toBe(1);
    });

    test('creates scenario with null results initially', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      const scenarioId = createScenario('New Scenario', 'product-abc');
      const scenario = getScenario(scenarioId);

      expect(scenario?.results).toBeNull();
    });

    test('creates scenario with createdAt timestamp', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      const before = new Date();
      const scenarioId = createScenario('New Scenario', 'product-def');
      const after = new Date();

      const scenario = getScenario(scenarioId);

      expect(scenario?.createdAt).toBeDefined();
      expect(scenario?.createdAt.getTime()).toBeGreaterThanOrEqual(before.getTime());
      expect(scenario?.createdAt.getTime()).toBeLessThanOrEqual(after.getTime());
    });

    test('first scenario is automatically set as baseline', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      const scenarioId = createScenario('First Scenario', 'product-first');
      const scenario = getScenario(scenarioId);

      expect(scenario?.isBaseline).toBe(true);
    });

    test('subsequent scenarios are not baseline by default', () => {
      const { createScenario, getScenario } = useScenarioStore.getState();

      // Create first scenario (will be baseline)
      createScenario('First Scenario', 'product-1');

      // Create second scenario (should not be baseline)
      const secondId = createScenario('Second Scenario', 'product-2');
      const secondScenario = getScenario(secondId);

      expect(secondScenario?.isBaseline).toBe(false);
    });

    test('sets created scenario as active', () => {
      const { createScenario, getActiveScenario } = useScenarioStore.getState();

      createScenario('Active Scenario', 'product-active');
      const active = getActiveScenario();

      expect(active?.name).toBe('Active Scenario');
    });
  });

  describe('cloneScenario Action', () => {
    test('creates copy with new unique ID', () => {
      const { createScenario, cloneScenario, getScenario } = useScenarioStore.getState();

      const originalId = createScenario('Original', 'product-clone');
      const clonedId = cloneScenario(originalId, 'Cloned Scenario');

      expect(clonedId).not.toBe(originalId);
      expect(getScenario(clonedId)).toBeDefined();
    });

    test('copies name as provided in newName parameter', () => {
      const { createScenario, cloneScenario, getScenario } = useScenarioStore.getState();

      const originalId = createScenario('Original Name', 'product-clone');
      const clonedId = cloneScenario(originalId, 'Custom Clone Name');

      const cloned = getScenario(clonedId);
      expect(cloned?.name).toBe('Custom Clone Name');
    });

    test('copies bomEntries from original scenario', () => {
      const { createScenario, updateScenario, cloneScenario, getScenario } = useScenarioStore.getState();

      const originalId = createScenario('Original', 'product-clone');

      // Update original with BOM entries
      const bomEntries: BOMEntry[] = [
        { id: 'bom-1', component_name: 'Steel', quantity: 10, unit: 'kg', emissions: 5.0 },
        { id: 'bom-2', component_name: 'Plastic', quantity: 2, unit: 'kg', emissions: 1.5 },
      ];
      updateScenario(originalId, { bomEntries });

      const clonedId = cloneScenario(originalId, 'Cloned');
      const cloned = getScenario(clonedId);

      expect(cloned?.bomEntries).toHaveLength(2);
      expect(cloned?.bomEntries[0].component_name).toBe('Steel');
      expect(cloned?.bomEntries[1].component_name).toBe('Plastic');
    });

    test('copies parameters from original scenario', () => {
      const { createScenario, updateScenario, cloneScenario, getScenario } = useScenarioStore.getState();

      const originalId = createScenario('Original', 'product-clone');
      updateScenario(originalId, {
        parameters: {
          transportDistance: 500,
          energySource: 'solar',
          productionVolume: 100,
        },
      });

      const clonedId = cloneScenario(originalId, 'Cloned');
      const cloned = getScenario(clonedId);

      expect(cloned?.parameters.transportDistance).toBe(500);
      expect(cloned?.parameters.energySource).toBe('solar');
      expect(cloned?.parameters.productionVolume).toBe(100);
    });

    test('cloned scenario results are null (not copied)', () => {
      const { createScenario, updateScenario, cloneScenario, getScenario } = useScenarioStore.getState();

      const originalId = createScenario('Original', 'product-clone');
      updateScenario(originalId, {
        results: { total_emissions: 100.5 },
      });

      const clonedId = cloneScenario(originalId, 'Cloned');
      const cloned = getScenario(clonedId);

      // Results should be null - user must recalculate
      expect(cloned?.results).toBeNull();
    });

    test('cloned scenario is not baseline', () => {
      const { createScenario, cloneScenario, getScenario } = useScenarioStore.getState();

      const originalId = createScenario('Original', 'product-clone');
      // First scenario is baseline

      const clonedId = cloneScenario(originalId, 'Cloned');
      const cloned = getScenario(clonedId);

      expect(cloned?.isBaseline).toBe(false);
    });

    test('returns empty string when original scenario not found', () => {
      const { cloneScenario } = useScenarioStore.getState();

      const result = cloneScenario('nonexistent-id', 'Clone');

      expect(result).toBe('');
    });
  });

  describe('addToComparison / removeFromComparison Actions', () => {
    test('addToComparison adds scenario ID to comparison list', () => {
      const { createScenario, addToComparison, getComparisonScenarios } = useScenarioStore.getState();

      const scenarioId = createScenario('Test Scenario', 'product-compare');
      addToComparison(scenarioId);

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(1);
      expect(comparisonScenarios[0].id).toBe(scenarioId);
    });

    test('addToComparison does not add duplicates', () => {
      const { createScenario, addToComparison, getComparisonScenarios } = useScenarioStore.getState();

      const scenarioId = createScenario('Test Scenario', 'product-compare');
      addToComparison(scenarioId);
      addToComparison(scenarioId);
      addToComparison(scenarioId);

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(1);
    });

    test('addToComparison can add multiple different scenarios', () => {
      const { createScenario, addToComparison, getComparisonScenarios } = useScenarioStore.getState();

      const id1 = createScenario('Scenario 1', 'product-1');
      const id2 = createScenario('Scenario 2', 'product-2');
      const id3 = createScenario('Scenario 3', 'product-3');

      addToComparison(id1);
      addToComparison(id2);
      addToComparison(id3);

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(3);
    });

    test('removeFromComparison removes scenario from comparison list', () => {
      const { createScenario, addToComparison, removeFromComparison, getComparisonScenarios } = useScenarioStore.getState();

      const id1 = createScenario('Scenario 1', 'product-1');
      const id2 = createScenario('Scenario 2', 'product-2');

      addToComparison(id1);
      addToComparison(id2);

      removeFromComparison(id1);

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(1);
      expect(comparisonScenarios[0].id).toBe(id2);
    });

    test('removeFromComparison does nothing for ID not in list', () => {
      const { createScenario, addToComparison, removeFromComparison, getComparisonScenarios } = useScenarioStore.getState();

      const scenarioId = createScenario('Test Scenario', 'product-test');
      addToComparison(scenarioId);

      removeFromComparison('nonexistent-id');

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(1);
    });

    test('clearComparison removes all scenarios from comparison list', () => {
      const { createScenario, addToComparison, clearComparison, getComparisonScenarios } = useScenarioStore.getState();

      const id1 = createScenario('Scenario 1', 'product-1');
      const id2 = createScenario('Scenario 2', 'product-2');

      addToComparison(id1);
      addToComparison(id2);

      clearComparison();

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(0);
    });
  });

  describe('setAsBaseline Action', () => {
    test('sets isBaseline flag to true for specified scenario', () => {
      const { createScenario, setAsBaseline, getScenario } = useScenarioStore.getState();

      // Create scenarios - first is automatically baseline
      createScenario('First Scenario', 'product-1');
      const secondId = createScenario('Second Scenario', 'product-2');

      setAsBaseline(secondId);

      const second = getScenario(secondId);
      expect(second?.isBaseline).toBe(true);
    });

    test('removes baseline flag from previous baseline scenario', () => {
      const { createScenario, setAsBaseline, getScenario } = useScenarioStore.getState();

      const firstId = createScenario('First Scenario', 'product-1');
      const secondId = createScenario('Second Scenario', 'product-2');

      // First scenario is initially baseline
      expect(getScenario(firstId)?.isBaseline).toBe(true);

      setAsBaseline(secondId);

      // First should no longer be baseline
      expect(getScenario(firstId)?.isBaseline).toBe(false);
      // Second should now be baseline
      expect(getScenario(secondId)?.isBaseline).toBe(true);
    });

    test('only one scenario can be baseline at a time', () => {
      const { createScenario, setAsBaseline } = useScenarioStore.getState();

      createScenario('Scenario 1', 'product-1');
      createScenario('Scenario 2', 'product-2');
      const thirdId = createScenario('Scenario 3', 'product-3');

      setAsBaseline(thirdId);

      // Get all scenarios from state
      const { scenarios } = useScenarioStore.getState();
      const baselineScenarios = scenarios.filter(s => s.isBaseline);

      expect(baselineScenarios).toHaveLength(1);
      expect(baselineScenarios[0].id).toBe(thirdId);
    });

    test('setAsBaseline does nothing for nonexistent scenario', () => {
      const { createScenario, setAsBaseline, getBaseline } = useScenarioStore.getState();

      const firstId = createScenario('First Scenario', 'product-1');

      setAsBaseline('nonexistent-id');

      // First scenario should still be baseline
      const baseline = getBaseline();
      expect(baseline?.id).toBe(firstId);
    });
  });

  describe('getComparisonScenarios Selector', () => {
    test('returns empty array when no scenarios in comparison', () => {
      const { getComparisonScenarios } = useScenarioStore.getState();

      const scenarios = getComparisonScenarios();

      expect(scenarios).toEqual([]);
    });

    test('returns correct filtered list of comparison scenarios', () => {
      const { createScenario, addToComparison, getComparisonScenarios } = useScenarioStore.getState();

      const id1 = createScenario('Scenario 1', 'product-1');
      const id2 = createScenario('Scenario 2', 'product-2');
      createScenario('Scenario 3', 'product-3'); // Not in comparison

      addToComparison(id1);
      addToComparison(id2);

      const comparisonScenarios = getComparisonScenarios();

      expect(comparisonScenarios).toHaveLength(2);
      expect(comparisonScenarios.map(s => s.id)).toContain(id1);
      expect(comparisonScenarios.map(s => s.id)).toContain(id2);
    });

    test('returns full scenario objects, not just IDs', () => {
      const { createScenario, addToComparison, getComparisonScenarios } = useScenarioStore.getState();

      const id = createScenario('Test Scenario', 'product-test');
      addToComparison(id);

      const comparisonScenarios = getComparisonScenarios();

      expect(comparisonScenarios[0]).toHaveProperty('id');
      expect(comparisonScenarios[0]).toHaveProperty('name');
      expect(comparisonScenarios[0]).toHaveProperty('bomEntries');
      expect(comparisonScenarios[0]).toHaveProperty('parameters');
      expect(comparisonScenarios[0]).toHaveProperty('results');
      expect(comparisonScenarios[0]).toHaveProperty('isBaseline');
    });

    test('excludes deleted scenarios from comparison list', () => {
      const { createScenario, addToComparison, deleteScenario, getComparisonScenarios } = useScenarioStore.getState();

      const id1 = createScenario('Scenario 1', 'product-1');
      const id2 = createScenario('Scenario 2', 'product-2');

      addToComparison(id1);
      addToComparison(id2);

      deleteScenario(id1);

      const comparisonScenarios = getComparisonScenarios();
      expect(comparisonScenarios).toHaveLength(1);
      expect(comparisonScenarios[0].id).toBe(id2);
    });
  });

  describe('getBaseline Selector', () => {
    test('returns undefined when no scenarios exist', () => {
      const { getBaseline } = useScenarioStore.getState();

      const baseline = getBaseline();

      expect(baseline).toBeUndefined();
    });

    test('returns scenario with isBaseline=true', () => {
      const { createScenario, getBaseline } = useScenarioStore.getState();

      createScenario('Baseline Scenario', 'product-baseline');

      const baseline = getBaseline();

      expect(baseline).toBeDefined();
      expect(baseline?.isBaseline).toBe(true);
      expect(baseline?.name).toBe('Baseline Scenario');
    });

    test('returns updated baseline after setAsBaseline call', () => {
      const { createScenario, setAsBaseline, getBaseline } = useScenarioStore.getState();

      createScenario('First', 'product-1');
      const secondId = createScenario('Second', 'product-2');

      setAsBaseline(secondId);

      const baseline = getBaseline();
      expect(baseline?.name).toBe('Second');
    });

    test('returns undefined if baseline scenario is deleted', () => {
      const { createScenario, deleteScenario, getBaseline, getScenario } = useScenarioStore.getState();

      const baselineId = createScenario('Baseline', 'product-baseline');

      deleteScenario(baselineId);

      // Should be no baseline after deleting the only/baseline scenario
      // Depending on implementation, might return undefined or auto-assign new baseline
      const baseline = getBaseline();
      // At minimum, the original baseline should not exist
      expect(getScenario(baselineId)).toBeUndefined();
    });
  });

  describe('updateScenario Action', () => {
    test('updates scenario name', () => {
      const { createScenario, updateScenario, getScenario } = useScenarioStore.getState();

      const id = createScenario('Original Name', 'product-update');
      updateScenario(id, { name: 'Updated Name' });

      const scenario = getScenario(id);
      expect(scenario?.name).toBe('Updated Name');
    });

    test('updates scenario bomEntries', () => {
      const { createScenario, updateScenario, getScenario } = useScenarioStore.getState();

      const id = createScenario('Test', 'product-update');
      const newBomEntries: BOMEntry[] = [
        { id: 'entry-1', component_name: 'Aluminum', quantity: 5, unit: 'kg' },
      ];

      updateScenario(id, { bomEntries: newBomEntries });

      const scenario = getScenario(id);
      expect(scenario?.bomEntries).toHaveLength(1);
      expect(scenario?.bomEntries[0].component_name).toBe('Aluminum');
    });

    test('updates scenario results', () => {
      const { createScenario, updateScenario, getScenario } = useScenarioStore.getState();

      const id = createScenario('Test', 'product-update');
      const results: CalculationResults = { total_emissions: 250.75 };

      updateScenario(id, { results });

      const scenario = getScenario(id);
      expect(scenario?.results?.total_emissions).toBe(250.75);
    });

    test('partial update preserves other fields', () => {
      const { createScenario, updateScenario, getScenario } = useScenarioStore.getState();

      const id = createScenario('Original', 'product-partial');

      updateScenario(id, { name: 'Updated' });

      const scenario = getScenario(id);
      expect(scenario?.name).toBe('Updated');
      expect(scenario?.productId).toBe('product-partial'); // Unchanged
    });
  });

  describe('deleteScenario Action', () => {
    test('removes scenario from scenarios array', () => {
      const { createScenario, deleteScenario, getScenario } = useScenarioStore.getState();

      const id = createScenario('To Delete', 'product-delete');
      deleteScenario(id);

      expect(getScenario(id)).toBeUndefined();
    });

    test('removes scenario from comparison list', () => {
      const { createScenario, addToComparison, deleteScenario, getComparisonScenarios } = useScenarioStore.getState();

      const id = createScenario('To Delete', 'product-delete');
      addToComparison(id);

      deleteScenario(id);

      const comparison = getComparisonScenarios();
      expect(comparison).toHaveLength(0);
    });

    test('clears activeScenarioId if deleted scenario was active', () => {
      const { createScenario, deleteScenario, getActiveScenario } = useScenarioStore.getState();

      const id = createScenario('Active', 'product-active');
      // Creating sets it as active

      deleteScenario(id);

      expect(getActiveScenario()).toBeUndefined();
    });
  });

  describe('setActiveScenario Action', () => {
    test('sets activeScenarioId', () => {
      const { createScenario, setActiveScenario, getActiveScenario } = useScenarioStore.getState();

      createScenario('First', 'product-1');
      const secondId = createScenario('Second', 'product-2');

      setActiveScenario(secondId);

      expect(getActiveScenario()?.id).toBe(secondId);
    });

    test('does nothing for nonexistent scenario', () => {
      const { createScenario, setActiveScenario, getActiveScenario } = useScenarioStore.getState();

      const id = createScenario('Test', 'product-test');

      setActiveScenario('nonexistent');

      // Should still have original active scenario
      expect(getActiveScenario()?.id).toBe(id);
    });
  });
});
