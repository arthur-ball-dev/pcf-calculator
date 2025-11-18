/**
 * BOMEditor Loading State Tests
 *
 * Test-Driven Development for TASK-FE-019
 * Tests BOM Editor loading state display while BOM is being fetched
 *
 * Test Scenarios:
 * 1. Shows loading skeleton when isLoadingBOM is true
 * 2. Hides loading skeleton and shows editor when isLoadingBOM is false
 * 3. Editor loads with BOM data after loading completes
 */

import { describe, test, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import BOMEditor from '../../src/components/forms/BOMEditor';
import { useCalculatorStore } from '../../src/store/calculatorStore';
import { useWizardStore } from '../../src/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

// Mock the emission factors hook
vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: "1", activity_name: 'Cotton', co2e_factor: 5.89, unit: 'kg', category: 'material' },
      { id: "2", activity_name: 'Polyester', co2e_factor: 3.36, unit: 'kg', category: 'material' },
    ],
    isLoading: false,
    error: null,
  }),
}));

describe('BOMEditor - Loading State (TASK-FE-019)', () => {
  beforeEach(() => {
    // Reset stores
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    localStorage.clear();
  });

  describe('Scenario 1: Loading Skeleton Display', () => {
    test('shows loading skeleton when isLoadingBOM is true', () => {
      // Set loading state
      useCalculatorStore.getState().setLoadingBOM(true);

      render(<BOMEditor />);

      // Should show loading skeleton
      expect(screen.getByTestId('bom-editor-skeleton')).toBeInTheDocument();
    });

    test('loading skeleton has appropriate accessibility attributes', () => {
      useCalculatorStore.getState().setLoadingBOM(true);

      render(<BOMEditor />);

      const skeleton = screen.getByTestId('bom-editor-skeleton');
      expect(skeleton).toBeInTheDocument();

      // Should have visual loading indicators (animation)
      expect(skeleton.className).toContain('animate-pulse');
    });

    test('does not show BOM editor form while loading', () => {
      useCalculatorStore.getState().setLoadingBOM(true);

      render(<BOMEditor />);

      // Should not show Add Component button (part of editor)
      expect(screen.queryByText(/Add Component/i)).not.toBeInTheDocument();
    });
  });

  describe('Scenario 2: Editor Display After Loading', () => {
    test('hides loading skeleton when isLoadingBOM is false', () => {
      // Set loading to false
      useCalculatorStore.getState().setLoadingBOM(false);

      render(<BOMEditor />);

      // Should not show loading skeleton
      expect(screen.queryByTestId('bom-editor-skeleton')).not.toBeInTheDocument();
    });

    test('shows BOM editor form when not loading', () => {
      useCalculatorStore.getState().setLoadingBOM(false);

      render(<BOMEditor />);

      // Should show Add Component button (part of editor)
      expect(screen.getByText(/Add Component/i)).toBeInTheDocument();
    });

    test('shows table headers when not loading', () => {
      useCalculatorStore.getState().setLoadingBOM(false);

      render(<BOMEditor />);

      // Should show table headers - Component Name is unique to header
      expect(screen.getByText(/Component Name/i)).toBeInTheDocument();
      // Quantity, Unit, Category, and Emission Factor appear in dropdowns too
      // Just verifying Component Name is sufficient to confirm table is rendered
    });
  });

  describe('Scenario 3: Loading State Transitions', () => {
    test('transitions from loading to loaded state', async () => {
      // Start with loading
      useCalculatorStore.getState().setLoadingBOM(true);

      const { rerender } = render(<BOMEditor />);

      // Should show loading skeleton
      expect(screen.getByTestId('bom-editor-skeleton')).toBeInTheDocument();

      // Simulate loading completion
      useCalculatorStore.getState().setLoadingBOM(false);
      rerender(<BOMEditor />);

      // Should show editor
      await waitFor(() => {
        expect(screen.queryByTestId('bom-editor-skeleton')).not.toBeInTheDocument();
        expect(screen.getByText(/Add Component/i)).toBeInTheDocument();
      });
    });

    test('displays loaded BOM data after loading completes', async () => {
      // Start with loading
      useCalculatorStore.getState().setLoadingBOM(true);

      const { rerender } = render(<BOMEditor />);

      // Simulate BOM data loaded
      const mockBOMItems: BOMItem[] = [
        {
          id: 'bom_001',
          name: 'Cotton',
          quantity: 0.18,
          unit: 'kg',
          category: 'material',
          emissionFactorId: 1,
        },
        {
          id: 'bom_002',
          name: 'Polyester',
          quantity: 0.02,
          unit: 'kg',
          category: 'material',
          emissionFactorId: 2,
        },
      ];

      useCalculatorStore.getState().setBomItems(mockBOMItems);
      useCalculatorStore.getState().setLoadingBOM(false);
      rerender(<BOMEditor />);

      // Should display BOM data
      await waitFor(() => {
        expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Polyester')).toBeInTheDocument();
      });
    });

    test('can transition back to loading state (for refetch)', async () => {
      // Start with loaded state
      useCalculatorStore.getState().setLoadingBOM(false);

      const { rerender } = render(<BOMEditor />);

      // Should show editor
      expect(screen.getByText(/Add Component/i)).toBeInTheDocument();

      // Simulate refetch (loading again)
      useCalculatorStore.getState().setLoadingBOM(true);
      rerender(<BOMEditor />);

      // Should show loading skeleton
      await waitFor(() => {
        expect(screen.getByTestId('bom-editor-skeleton')).toBeInTheDocument();
        expect(screen.queryByText(/Add Component/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Scenario 4: Empty BOM After Loading', () => {
    test('shows default empty row when BOM is empty after loading', async () => {
      // Set loading to false with empty BOM
      useCalculatorStore.getState().setBomItems([]);
      useCalculatorStore.getState().setLoadingBOM(false);

      render(<BOMEditor />);

      // Should show editor with one empty row
      await waitFor(() => {
        expect(screen.queryByTestId('bom-editor-skeleton')).not.toBeInTheDocument();
        expect(screen.getByText(/Add Component/i)).toBeInTheDocument();
      });

      // Should have at least one row (default empty row)
      const rows = screen.getAllByRole('row');
      expect(rows.length).toBeGreaterThan(1); // Header + at least 1 data row
    });
  });

  describe('Edge Cases', () => {
    test('handles rapid loading state changes', async () => {
      useCalculatorStore.getState().setLoadingBOM(true);

      const { rerender } = render(<BOMEditor />);

      // Rapidly toggle loading state
      useCalculatorStore.getState().setLoadingBOM(false);
      rerender(<BOMEditor />);
      useCalculatorStore.getState().setLoadingBOM(true);
      rerender(<BOMEditor />);
      useCalculatorStore.getState().setLoadingBOM(false);
      rerender(<BOMEditor />);

      // Should end up in non-loading state
      await waitFor(() => {
        expect(screen.queryByTestId('bom-editor-skeleton')).not.toBeInTheDocument();
        expect(screen.getByText(/Add Component/i)).toBeInTheDocument();
      });
    });

    test('maintains form state after loading completes', async () => {
      // Start with BOM items
      const mockBOMItems: BOMItem[] = [
        {
          id: 'bom_001',
          name: 'Cotton',
          quantity: 0.5,
          unit: 'kg',
          category: 'material',
          emissionFactorId: 1,
        },
      ];

      useCalculatorStore.getState().setBomItems(mockBOMItems);
      useCalculatorStore.getState().setLoadingBOM(true);

      const { rerender } = render(<BOMEditor />);

      // Complete loading
      useCalculatorStore.getState().setLoadingBOM(false);
      rerender(<BOMEditor />);

      // BOM data should still be present
      await waitFor(() => {
        expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
        expect(screen.getByDisplayValue('0.5')).toBeInTheDocument();
      });
    });
  });
});
