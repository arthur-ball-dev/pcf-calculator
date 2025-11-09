/**
 * Sankey Transform Tests
 *
 * Tests for transforming calculation results to Nivo Sankey format.
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-FE-008: Nivo Sankey Implementation
 */

import { describe, it, expect } from 'vitest';
import {
  transformToSankeyData,
  getNodeColor,
  getCategoryFromValue,
} from '../../src/utils/sankeyTransform';
import type { Calculation } from '../../src/types/store.types';

describe('sankeyTransform', () => {
  describe('transformToSankeyData', () => {
    it('should transform calculation results to Sankey nodes and links format', () => {
      const calculationResult: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 12.5,
        materials_co2e: 7.3,
        energy_co2e: 3.8,
        transport_co2e: 1.4,
      };

      const sankeyData = transformToSankeyData(calculationResult);

      // Should have nodes for each category and total
      expect(sankeyData.nodes).toHaveLength(4); // materials, energy, transport, total

      // Check materials node
      const materialsNode = sankeyData.nodes.find((n) => n.id === 'materials');
      expect(materialsNode).toBeDefined();
      expect(materialsNode?.label).toBe('Materials');
      expect(materialsNode?.nodeColor).toBe('#2196F3'); // Blue

      // Check energy node
      const energyNode = sankeyData.nodes.find((n) => n.id === 'energy');
      expect(energyNode).toBeDefined();
      expect(energyNode?.label).toBe('Energy');
      expect(energyNode?.nodeColor).toBe('#FFC107'); // Amber

      // Check transport node
      const transportNode = sankeyData.nodes.find((n) => n.id === 'transport');
      expect(transportNode).toBeDefined();
      expect(transportNode?.label).toBe('Transport');
      expect(transportNode?.nodeColor).toBe('#4CAF50'); // Green

      // Check total node
      const totalNode = sankeyData.nodes.find((n) => n.id === 'total');
      expect(totalNode).toBeDefined();
      expect(totalNode?.label).toBe('Total PCF');
      expect(totalNode?.nodeColor).toBe('#003f7f'); // Navy

      // Should have links from categories to total
      expect(sankeyData.links).toHaveLength(3);

      // Check materials link
      const materialsLink = sankeyData.links.find((l) => l.source === 'materials');
      expect(materialsLink).toBeDefined();
      expect(materialsLink?.target).toBe('total');
      expect(materialsLink?.value).toBe(7.3);

      // Check energy link
      const energyLink = sankeyData.links.find((l) => l.source === 'energy');
      expect(energyLink).toBeDefined();
      expect(energyLink?.target).toBe('total');
      expect(energyLink?.value).toBe(3.8);

      // Check transport link
      const transportLink = sankeyData.links.find((l) => l.source === 'transport');
      expect(transportLink).toBeDefined();
      expect(transportLink?.target).toBe('total');
      expect(transportLink?.value).toBe(1.4);
    });

    it('should exclude categories with zero emissions', () => {
      const calculationResult: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 10.0,
        materials_co2e: 10.0,
        energy_co2e: 0,
        transport_co2e: 0,
      };

      const sankeyData = transformToSankeyData(calculationResult);

      // Should only have materials and total nodes
      expect(sankeyData.nodes).toHaveLength(2);
      expect(sankeyData.nodes.find((n) => n.id === 'materials')).toBeDefined();
      expect(sankeyData.nodes.find((n) => n.id === 'total')).toBeDefined();
      expect(sankeyData.nodes.find((n) => n.id === 'energy')).toBeUndefined();
      expect(sankeyData.nodes.find((n) => n.id === 'transport')).toBeUndefined();

      // Should only have one link
      expect(sankeyData.links).toHaveLength(1);
      expect(sankeyData.links[0].source).toBe('materials');
    });

    it('should handle calculations with no breakdown data', () => {
      const calculationResult: Calculation = {
        id: 'calc-123',
        status: 'completed',
        product_id: 'prod-456',
        total_co2e_kg: 15.0,
        // No breakdown data
      };

      const sankeyData = transformToSankeyData(calculationResult);

      // Should return empty nodes and links when no breakdown available
      expect(sankeyData.nodes).toHaveLength(0);
      expect(sankeyData.links).toHaveLength(0);
    });

    it('should return empty data for non-completed calculations', () => {
      const calculationResult: Calculation = {
        id: 'calc-123',
        status: 'pending',
        product_id: 'prod-456',
      };

      const sankeyData = transformToSankeyData(calculationResult);

      expect(sankeyData.nodes).toHaveLength(0);
      expect(sankeyData.links).toHaveLength(0);
    });

    it('should handle null calculation input', () => {
      const sankeyData = transformToSankeyData(null);

      expect(sankeyData.nodes).toHaveLength(0);
      expect(sankeyData.links).toHaveLength(0);
    });
  });

  describe('getNodeColor', () => {
    it('should return correct color for materials category', () => {
      expect(getNodeColor('materials')).toBe('#2196F3');
    });

    it('should return correct color for energy category', () => {
      expect(getNodeColor('energy')).toBe('#FFC107');
    });

    it('should return correct color for transport category', () => {
      expect(getNodeColor('transport')).toBe('#4CAF50');
    });

    it('should return correct color for process category', () => {
      expect(getNodeColor('process')).toBe('#9C27B0');
    });

    it('should return correct color for waste category', () => {
      expect(getNodeColor('waste')).toBe('#757575');
    });

    it('should return correct color for total category', () => {
      expect(getNodeColor('total')).toBe('#003f7f');
    });

    it('should return default color for unknown category', () => {
      expect(getNodeColor('unknown')).toBe('#cccccc');
    });
  });

  describe('getCategoryFromValue', () => {
    it('should determine category from co2e value name', () => {
      expect(getCategoryFromValue('materials_co2e')).toBe('materials');
      expect(getCategoryFromValue('energy_co2e')).toBe('energy');
      expect(getCategoryFromValue('transport_co2e')).toBe('transport');
    });

    it('should return null for unrecognized value name', () => {
      expect(getCategoryFromValue('unknown_value')).toBeNull();
    });
  });
});
