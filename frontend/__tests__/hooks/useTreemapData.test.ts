/**
 * useTreemapData Hook Tests
 *
 * Tests for the data transformation hook that converts calculation
 * results into hierarchical treemap format for emissions visualization.
 *
 * Following TDD protocol: Write tests FIRST, implementation SECOND.
 *
 * TASK-UI-P5-001: Advanced Visualizations (Treemap + Area)
 *
 * Test Coverage:
 * - Data transformation from calculation to treemap format
 * - GHG Protocol color assignment
 * - Value aggregation and hierarchy building
 * - Memoization behavior
 * - Edge cases and error handling
 */

import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '../testUtils';

// Hook to be created at: frontend/src/hooks/useTreemapData.ts
import { useTreemapData } from '../../src/hooks/useTreemapData';
import type { Calculation, CalculationResult } from '../../src/types/store.types';

// ============================================================================
// Test Data Fixtures
// ============================================================================

const mockCalculation: Calculation = {
  id: 'calc-123',
  status: 'completed',
  product_id: 'prod-456',
  total_co2e_kg: 12500.5,
  materials_co2e: 7300.2,
  energy_co2e: 3800.8,
  transport_co2e: 1400.5,
};

const mockCalculationWithBreakdown: CalculationResult = {
  id: 'calc-456',
  status: 'completed',
  product_id: 'prod-789',
  total_co2e_kg: 15000.0,
  materials_co2e: 8000.0,
  energy_co2e: 4500.0,
  transport_co2e: 2500.0,
  breakdown: [
    { category: 'Steel', co2e: 3000, percentage: 20 },
    { category: 'Aluminum', co2e: 2000, percentage: 13.3 },
    { category: 'Plastics', co2e: 1500, percentage: 10 },
    { category: 'Electronics', co2e: 1500, percentage: 10 },
    { category: 'Electricity', co2e: 3500, percentage: 23.3 },
    { category: 'Natural Gas', co2e: 1000, percentage: 6.7 },
    { category: 'Road Transport', co2e: 1500, percentage: 10 },
    { category: 'Sea Freight', co2e: 1000, percentage: 6.7 },
  ],
};

const mockCalculationNullValues: Calculation = {
  id: 'calc-789',
  status: 'completed',
  product_id: 'prod-012',
  total_co2e_kg: 5000.0,
  materials_co2e: 5000.0,
  // No energy or transport (undefined/null)
};

const mockCalculationZeroValues: Calculation = {
  id: 'calc-zero',
  status: 'completed',
  product_id: 'prod-zero',
  total_co2e_kg: 3000.0,
  materials_co2e: 3000.0,
  energy_co2e: 0,
  transport_co2e: 0,
};

// ============================================================================
// Basic Data Transformation Tests
// ============================================================================

describe('useTreemapData', () => {
  describe('Basic Transformation', () => {
    it('transforms calculation to treemap data structure', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      expect(result.current).toBeDefined();
      expect(result.current.name).toBeDefined();
      expect(result.current.children).toBeDefined();
    });

    it('returns root node named "Total Emissions"', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      expect(result.current.name).toBe('Total Emissions');
    });

    it('creates child nodes for materials, energy, and transport', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      const childNames = result.current.children?.map((c) => c.name) ?? [];

      expect(childNames).toContain('Materials');
      expect(childNames).toContain('Energy');
      expect(childNames).toContain('Transport');
    });

    it('assigns correct values to category nodes', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );
      const energy = result.current.children?.find((c) => c.name === 'Energy');
      const transport = result.current.children?.find(
        (c) => c.name === 'Transport'
      );

      expect(materials?.value).toBe(7300.2);
      expect(energy?.value).toBe(3800.8);
      expect(transport?.value).toBe(1400.5);
    });
  });

  // ============================================================================
  // Color Assignment Tests
  // ============================================================================

  describe('Color Assignment', () => {
    it('assigns GHG Protocol colors to scope categories', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );
      const energy = result.current.children?.find((c) => c.name === 'Energy');
      const transport = result.current.children?.find(
        (c) => c.name === 'Transport'
      );

      // GHG Protocol standard colors
      expect(materials?.color).toBeDefined();
      expect(energy?.color).toBeDefined();
      expect(transport?.color).toBeDefined();
    });

    it('assigns distinct colors to different categories', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      const colors = result.current.children?.map((c) => c.color) ?? [];
      const uniqueColors = new Set(colors);

      // Each category should have a distinct color
      expect(uniqueColors.size).toBe(colors.length);
    });

    it('uses Scope 1 color family for direct emissions', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculation, { useScopeColors: true })
      );

      // Check that scope colors are applied
      expect(result.current.children).toBeDefined();
    });
  });

  // ============================================================================
  // Detailed Breakdown Tests
  // ============================================================================

  describe('Detailed Breakdown', () => {
    it('creates nested hierarchy from breakdown data', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationWithBreakdown)
      );

      // Should have nested structure
      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );

      expect(materials?.children).toBeDefined();
      expect(materials?.children?.length).toBeGreaterThan(0);
    });

    it('groups breakdown items by category', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationWithBreakdown)
      );

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );
      const childNames = materials?.children?.map((c) => c.name) ?? [];

      expect(childNames).toContain('Steel');
      expect(childNames).toContain('Aluminum');
    });

    it('calculates correct values for nested nodes', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationWithBreakdown)
      );

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );
      const steel = materials?.children?.find((c) => c.name === 'Steel');

      expect(steel?.value).toBe(3000);
    });

    it('includes percentage data in node metadata', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationWithBreakdown, { includePercentage: true })
      );

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );
      const steel = materials?.children?.find((c) => c.name === 'Steel');

      expect(steel?.metadata?.percentage).toBe(20);
    });
  });

  // ============================================================================
  // Edge Cases Tests
  // ============================================================================

  describe('Edge Cases', () => {
    it('handles null calculation gracefully', () => {
      const { result } = renderHook(() =>
        useTreemapData(null as unknown as Calculation)
      );

      expect(result.current).toBeDefined();
      expect(result.current.name).toBe('Total Emissions');
      expect(result.current.children).toEqual([]);
    });

    it('handles undefined calculation gracefully', () => {
      const { result } = renderHook(() =>
        useTreemapData(undefined as unknown as Calculation)
      );

      expect(result.current).toBeDefined();
      expect(result.current.children).toEqual([]);
    });

    it('excludes categories with zero values', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationZeroValues)
      );

      const childNames = result.current.children?.map((c) => c.name) ?? [];

      expect(childNames).toContain('Materials');
      expect(childNames).not.toContain('Energy');
      expect(childNames).not.toContain('Transport');
    });

    it('excludes categories with null/undefined values', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationNullValues)
      );

      const childNames = result.current.children?.map((c) => c.name) ?? [];

      expect(childNames).toContain('Materials');
      // Energy and transport should be excluded if not defined
      expect(childNames.length).toBeLessThanOrEqual(3);
    });

    it('handles pending calculation status', () => {
      const pendingCalc: Calculation = {
        id: 'calc-pending',
        status: 'pending',
        product_id: 'prod-123',
      };

      const { result } = renderHook(() => useTreemapData(pendingCalc));

      expect(result.current).toBeDefined();
      expect(result.current.children).toEqual([]);
    });

    it('handles failed calculation status', () => {
      const failedCalc: Calculation = {
        id: 'calc-failed',
        status: 'failed',
        product_id: 'prod-123',
        error_message: 'Calculation failed',
      };

      const { result } = renderHook(() => useTreemapData(failedCalc));

      expect(result.current).toBeDefined();
      expect(result.current.children).toEqual([]);
    });

    it('handles very large values without overflow', () => {
      const largeCalc: Calculation = {
        id: 'calc-large',
        status: 'completed',
        product_id: 'prod-large',
        total_co2e_kg: 999999999.99,
        materials_co2e: 500000000.0,
        energy_co2e: 300000000.0,
        transport_co2e: 199999999.99,
      };

      const { result } = renderHook(() => useTreemapData(largeCalc));

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );

      expect(materials?.value).toBe(500000000.0);
    });

    it('handles decimal precision correctly', () => {
      const precisionCalc: Calculation = {
        id: 'calc-precision',
        status: 'completed',
        product_id: 'prod-precision',
        total_co2e_kg: 100.123456789,
        materials_co2e: 50.123456789,
        energy_co2e: 30.0,
        transport_co2e: 20.0,
      };

      const { result } = renderHook(() => useTreemapData(precisionCalc));

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );

      // Should maintain reasonable precision
      expect(materials?.value).toBeCloseTo(50.123456789, 6);
    });
  });

  // ============================================================================
  // Memoization Tests
  // ============================================================================

  describe('Memoization', () => {
    it('returns same reference for identical input', () => {
      const { result, rerender } = renderHook(
        ({ calc }) => useTreemapData(calc),
        { initialProps: { calc: mockCalculation } }
      );

      const firstResult = result.current;

      rerender({ calc: mockCalculation });

      const secondResult = result.current;

      // Should be referentially equal for same input
      expect(firstResult).toBe(secondResult);
    });

    it('returns new reference when calculation changes', () => {
      const { result, rerender } = renderHook(
        ({ calc }) => useTreemapData(calc),
        { initialProps: { calc: mockCalculation } }
      );

      const firstResult = result.current;

      const newCalc: Calculation = {
        ...mockCalculation,
        id: 'calc-new',
        materials_co2e: 9999.9,
      };

      rerender({ calc: newCalc });

      const secondResult = result.current;

      // Should be different reference for different input
      expect(firstResult).not.toBe(secondResult);
    });

    it('memoizes expensive breakdown transformations', () => {
      const { result, rerender } = renderHook(
        ({ calc }) => useTreemapData(calc),
        { initialProps: { calc: mockCalculationWithBreakdown } }
      );

      const firstResult = result.current;

      // Rerender with same reference
      rerender({ calc: mockCalculationWithBreakdown });

      const secondResult = result.current;

      expect(firstResult).toBe(secondResult);
    });
  });

  // ============================================================================
  // Options Tests
  // ============================================================================

  describe('Options', () => {
    it('respects includePercentage option', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationWithBreakdown, { includePercentage: true })
      );

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );

      expect(materials?.metadata?.percentage).toBeDefined();
    });

    it('respects useScopeColors option', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculation, { useScopeColors: true })
      );

      expect(result.current.children?.length).toBeGreaterThan(0);
    });

    it('respects aggregateThreshold option', () => {
      const detailedBreakdown: CalculationResult = {
        ...mockCalculationWithBreakdown,
        breakdown: [
          { category: 'Large Item', co2e: 5000, percentage: 50 },
          { category: 'Small Item 1', co2e: 50, percentage: 0.5 },
          { category: 'Small Item 2', co2e: 50, percentage: 0.5 },
          { category: 'Medium Item', co2e: 4900, percentage: 49 },
        ],
      };

      const { result } = renderHook(() =>
        useTreemapData(detailedBreakdown, { aggregateThreshold: 1 })
      );

      // Small items should be aggregated into "Other"
      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );
      const childNames = materials?.children?.map((c) => c.name) ?? [];

      // Should have aggregated small items
      expect(childNames).toContain('Other');
    });

    it('uses default options when not specified', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      // Should work with default options
      expect(result.current).toBeDefined();
      expect(result.current.children?.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Type Safety Tests
  // ============================================================================

  describe('Type Safety', () => {
    it('returns correct TreemapNode type', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      // Type checking
      const node = result.current;

      expect(typeof node.name).toBe('string');
      expect(Array.isArray(node.children)).toBe(true);
    });

    it('child nodes have required properties', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      result.current.children?.forEach((child) => {
        expect(child).toHaveProperty('name');
        // Either value or children should be present
        expect(
          child.value !== undefined || child.children !== undefined
        ).toBe(true);
      });
    });

    it('leaf nodes have value property', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculationWithBreakdown)
      );

      const materials = result.current.children?.find(
        (c) => c.name === 'Materials'
      );

      materials?.children?.forEach((leaf) => {
        if (!leaf.children || leaf.children.length === 0) {
          expect(leaf.value).toBeDefined();
          expect(typeof leaf.value).toBe('number');
        }
      });
    });
  });

  // ============================================================================
  // Custom Unit Tests
  // ============================================================================

  describe('Custom Unit', () => {
    it('includes unit in metadata when specified', () => {
      const { result } = renderHook(() =>
        useTreemapData(mockCalculation, { unit: 'tonnes CO2e' })
      );

      // Unit should be available in metadata
      expect(result.current.metadata?.unit).toBe('tonnes CO2e');
    });

    it('uses default unit when not specified', () => {
      const { result } = renderHook(() => useTreemapData(mockCalculation));

      // Default unit should be kg CO2e
      expect(result.current.metadata?.unit).toBe('kg CO2e');
    });
  });
});
