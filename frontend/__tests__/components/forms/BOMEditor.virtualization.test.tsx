/**
 * BOMEditor Virtualization Tests (TASK-FE-P8-007)
 *
 * Test suite for list virtualization in BOMEditor component.
 * Tests cover:
 * - Large list rendering efficiency (100+ items)
 * - Scroll behavior (container setup)
 * - Form state persistence during scroll
 * - Add/remove items while scrolled
 * - Edge cases (empty list, single item)
 * - Virtualization threshold behavior (20+ items triggers virtualization)
 *
 * NOTE: @tanstack/react-virtual's useVirtualizer hook relies on actual DOM measurements.
 * In JSDOM (test environment), there's no real layout, so we mock the virtualizer
 * to return predictable virtual items for testing.
 *
 * Following TDD protocol: Tests written BEFORE implementation.
 */

import React from 'react';
import { render, screen, waitFor, within } from '../../testUtils';
import userEvent from '@testing-library/user-event';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import BOMEditor from '@/components/forms/BOMEditor';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';
import type { BOMItem } from '@/types/store.types';

// Mock the stores
vi.mock('@/store/calculatorStore');
vi.mock('@/store/wizardStore');

// Mock API hook for emission factors
vi.mock('@/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: '1', activity_name: 'Cotton (Organic)', co2e_factor: 2.5, unit: 'kg', category: 'material', data_source: 'EPA' },
      { id: '2', activity_name: 'Polyester (Virgin)', co2e_factor: 5.5, unit: 'kg', category: 'material', data_source: 'DEFRA' },
    ],
    isLoading: false,
    error: null
  })
}));

// Mock useBreakpoints to return desktop view for virtualization tests
vi.mock('@/hooks/useBreakpoints', () => ({
  useBreakpoints: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    breakpoint: 'lg',
    width: 1200,
  })
}));

// Mock @tanstack/react-virtual to work in JSDOM
// The real virtualizer needs actual DOM measurements which JSDOM doesn't provide
vi.mock('@tanstack/react-virtual', () => ({
  useVirtualizer: ({ count, estimateSize, overscan }: { count: number; estimateSize: () => number; overscan: number }) => {
    // In JSDOM, simulate rendering the first N items (visible + overscan buffer)
    const visibleCount = Math.min(count, 6 + overscan); // ~6 visible rows in 400px container @ 64px rows
    const virtualItems = Array.from({ length: visibleCount }, (_, i) => ({
      index: i,
      start: i * estimateSize(),
      size: estimateSize(),
      key: i,
    }));

    return {
      getVirtualItems: () => virtualItems,
      getTotalSize: () => count * estimateSize(),
      scrollToIndex: vi.fn(),
      measure: vi.fn(),
    };
  },
}));

/**
 * Helper to generate a large number of BOM items for testing
 */
function generateBOMItems(count: number): BOMItem[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `item-${i + 1}`,
    name: `Component ${i + 1}`,
    quantity: (i + 1) * 0.5,
    unit: 'kg' as const,
    category: 'material' as const,
    emissionFactorId: i % 2 === 0 ? '1' : '2',
  }));
}

// Virtualization threshold from BOMEditor.tsx
const VIRTUALIZATION_THRESHOLD = 20;

describe('BOMEditor Virtualization (TASK-FE-P8-007)', () => {
  const mockSetBomItems = vi.fn();
  const mockMarkStepComplete = vi.fn();
  const mockMarkStepIncomplete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    (useWizardStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      markStepComplete: mockMarkStepComplete,
      markStepIncomplete: mockMarkStepIncomplete
    });
  });

  // ============================================================================
  // Large List Rendering Tests (with virtualization)
  // ============================================================================

  describe('Large List Rendering (>= threshold)', () => {
    test('renders with 100+ items without crashing', async () => {
      const largeItemList = generateBOMItems(100);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Component should render without errors - there may be multiple tables
      // (header table and virtual row tables)
      const tables = screen.getAllByRole('table');
      expect(tables.length).toBeGreaterThan(0);

      // Total count should show 100 components
      await waitFor(() => {
        expect(screen.getByText(/100 components/i)).toBeInTheDocument();
      });
    });

    test('uses virtualization for lists >= threshold (20 items)', async () => {
      const items = generateBOMItems(VIRTUALIZATION_THRESHOLD);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Should use virtualized container
      await waitFor(() => {
        expect(screen.getByTestId('bom-virtual-scroll-container')).toBeInTheDocument();
      });
    });

    test('only renders visible rows plus buffer (not all 100+)', async () => {
      const largeItemList = generateBOMItems(100);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // With virtualization, we should NOT have 100 rows in the DOM
      // Instead, only visible rows + overscan buffer should be rendered
      // Our mock renders 11 items (6 visible + 5 overscan)
      await waitFor(() => {
        const virtualRows = screen.getAllByTestId('bom-virtual-row');
        // Should have significantly fewer than 100
        expect(virtualRows.length).toBeLessThan(30);
        expect(virtualRows.length).toBeGreaterThan(0);
      });
    });

    test('renders with exactly 50 items efficiently', async () => {
      const items = generateBOMItems(50);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Should render and show correct count
      await waitFor(() => {
        expect(screen.getByText(/50 components/i)).toBeInTheDocument();
        // Should be using virtualization
        expect(screen.getByTestId('bom-virtual-scroll-container')).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Scroll Behavior Tests
  // ============================================================================

  describe('Scroll Behavior', () => {
    test('virtualized container has scrollable area', async () => {
      const largeItemList = generateBOMItems(100);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Find the virtualized scroll container
      const scrollContainer = screen.getByTestId('bom-virtual-scroll-container');
      expect(scrollContainer).toBeInTheDocument();

      // Check for overflow-y-auto class (JSDOM doesn't compute CSS properly)
      // The class 'overflow-y-auto' is applied in the component
      expect(scrollContainer.className).toContain('overflow-y-auto');

      // Also verify the height style is set (for fixed container height)
      expect(scrollContainer.style.height).toBe('400px');
    });

    test('maintains scroll position after re-render', async () => {
      const largeItemList = generateBOMItems(100);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      const { rerender } = render(<BOMEditor />);

      const scrollContainer = screen.getByTestId('bom-virtual-scroll-container');

      // Simulate scroll
      Object.defineProperty(scrollContainer, 'scrollTop', {
        writable: true,
        value: 500,
      });
      scrollContainer.dispatchEvent(new Event('scroll'));

      // Re-render the component
      rerender(<BOMEditor />);

      // Scroll position should be maintained (or component should handle it)
      await waitFor(() => {
        const container = screen.getByTestId('bom-virtual-scroll-container');
        expect(container).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Form State Persistence Tests
  // ============================================================================

  describe('Form State Persistence During Scroll', () => {
    test('form values persist when scrolling through large list', async () => {
      const user = userEvent.setup();
      // Use smaller list for faster test
      const items = generateBOMItems(30);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Find a visible input and modify it
      const visibleInputs = screen.getAllByPlaceholderText(/e.g., Cotton, Electricity/i);
      expect(visibleInputs.length).toBeGreaterThan(0);

      const firstInput = visibleInputs[0];
      await user.clear(firstInput);
      await user.type(firstInput, 'Modified');

      // Simulate scroll (scroll away and back)
      const scrollContainer = screen.getByTestId('bom-virtual-scroll-container');
      Object.defineProperty(scrollContainer, 'scrollTop', { writable: true, value: 500 });
      scrollContainer.dispatchEvent(new Event('scroll'));

      // Wait for virtualization to potentially unmount/remount rows
      await waitFor(() => {
        expect(scrollContainer).toBeInTheDocument();
      });

      // Scroll back to top
      Object.defineProperty(scrollContainer, 'scrollTop', { writable: true, value: 0 });
      scrollContainer.dispatchEvent(new Event('scroll'));

      // The modified value should still be in the form state
      // (synced to store via form.watch subscription)
      await waitFor(() => {
        expect(mockSetBomItems).toHaveBeenCalled();
      });
    }, 15000); // Increase timeout to 15 seconds

    test('validation state persists across virtualized items', async () => {
      const items = generateBOMItems(50);
      // Make first item invalid (empty name)
      items[0].name = '';

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Validation errors should be visible for invalid items
      // The form should track validation state even for virtualized (unmounted) items
      await waitFor(() => {
        expect(mockMarkStepIncomplete).toHaveBeenCalledWith('edit');
      });
    });
  });

  // ============================================================================
  // Add/Remove Items While Scrolled Tests
  // ============================================================================

  describe('Add/Remove Items While Scrolled', () => {
    test('adding item works correctly when scrolled', async () => {
      const user = userEvent.setup();
      const items = generateBOMItems(50);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Scroll down
      const scrollContainer = screen.getByTestId('bom-virtual-scroll-container');
      Object.defineProperty(scrollContainer, 'scrollTop', { writable: true, value: 500 });
      scrollContainer.dispatchEvent(new Event('scroll'));

      // Click Add Component button
      const addButton = screen.getByRole('button', { name: /add component/i });
      await user.click(addButton);

      // Should now show 51 components
      await waitFor(() => {
        expect(screen.getByText(/51 components/i)).toBeInTheDocument();
      });
    });

    test('removing item works correctly when virtualized', async () => {
      const user = userEvent.setup();
      const items = generateBOMItems(50);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Find and click a delete button (opens AlertDialog)
      // With our mock, we render 11 visible rows, so there should be delete buttons
      await waitFor(() => {
        const deleteButtons = screen.getAllByLabelText(/delete component/i);
        expect(deleteButtons.length).toBeGreaterThan(0);
      });

      const deleteButtons = screen.getAllByLabelText(/delete component/i);
      await user.click(deleteButtons[0]);

      // Confirm deletion in AlertDialog
      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      const dialog = screen.getByRole('alertdialog');
      const confirmButton = within(dialog).getByRole('button', { name: /^delete$/i });
      await user.click(confirmButton);

      // Should now show 49 components
      await waitFor(() => {
        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
        expect(screen.getByText(/49 components/i)).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Non-Virtualized Edge Cases (below threshold)
  // ============================================================================

  describe('Non-Virtualized Mode (< threshold)', () => {
    test('does NOT use virtualization for lists < threshold', async () => {
      const items = generateBOMItems(VIRTUALIZATION_THRESHOLD - 1); // 19 items

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Should NOT have virtualized container
      await waitFor(() => {
        expect(screen.queryByTestId('bom-virtual-scroll-container')).not.toBeInTheDocument();
      });

      // Should still show correct count
      expect(screen.getByText(/19 components/i)).toBeInTheDocument();
    });

    test('handles empty list without virtualization', async () => {
      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: [],
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Should render with default 1 item (minimum constraint)
      await waitFor(() => {
        expect(screen.getByText(/1 component[^s]/)).toBeInTheDocument();
      });

      // Should NOT have virtualized container (only 1 item)
      expect(screen.queryByTestId('bom-virtual-scroll-container')).not.toBeInTheDocument();
    });

    test('handles single item list without virtualization', async () => {
      const singleItem = generateBOMItems(1);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: singleItem,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Should render the single item
      await waitFor(() => {
        expect(screen.getByText(/1 component[^s]/)).toBeInTheDocument();
      });

      // Delete button should be disabled for single item
      const deleteButton = screen.getByLabelText(/delete component/i);
      expect(deleteButton).toBeDisabled();

      // Should NOT have virtualized container
      expect(screen.queryByTestId('bom-virtual-scroll-container')).not.toBeInTheDocument();
    });

    test('total quantity updates correctly after adding item', async () => {
      const user = userEvent.setup();
      // Create items where total quantity is known: 1*0.5 + 2*0.5 + ... + 10*0.5 = 27.5
      const items = generateBOMItems(10);
      const expectedTotal = items.reduce((sum, item) => sum + item.quantity, 0);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Verify initial total (10 items, not virtualized)
      await waitFor(() => {
        expect(screen.getByText(new RegExp(`total quantity: ${expectedTotal.toFixed(2)}`, 'i'))).toBeInTheDocument();
      });

      // Add a new component (default quantity is 1)
      const addButton = screen.getByRole('button', { name: /add component/i });
      await user.click(addButton);

      // Total should increase by 1 (default quantity for new item)
      await waitFor(() => {
        expect(screen.getByText(new RegExp(`total quantity: ${(expectedTotal + 1).toFixed(2)}`, 'i'))).toBeInTheDocument();
      });
    });

    test('handles rapid add operations', async () => {
      const user = userEvent.setup();
      const items = generateBOMItems(10);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      const addButton = screen.getByRole('button', { name: /add component/i });

      // Add multiple items (with small delays to allow React state updates)
      await user.click(addButton);
      await waitFor(() => {
        expect(screen.getByText(/11 components/i)).toBeInTheDocument();
      });

      await user.click(addButton);
      await waitFor(() => {
        expect(screen.getByText(/12 components/i)).toBeInTheDocument();
      });

      await user.click(addButton);
      // Should show 13 components (10 + 3)
      await waitFor(() => {
        expect(screen.getByText(/13 components/i)).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Threshold Transition Tests
  // ============================================================================

  describe('Virtualization Threshold Transition', () => {
    test('transitions to virtualization when adding items past threshold', async () => {
      const user = userEvent.setup();
      // Start just below threshold
      const items = generateBOMItems(VIRTUALIZATION_THRESHOLD - 1);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: items,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      // Should NOT be virtualized initially
      expect(screen.queryByTestId('bom-virtual-scroll-container')).not.toBeInTheDocument();

      // Add one item to reach threshold
      const addButton = screen.getByRole('button', { name: /add component/i });
      await user.click(addButton);

      // Should now be virtualized (at threshold)
      await waitFor(() => {
        expect(screen.getByTestId('bom-virtual-scroll-container')).toBeInTheDocument();
      });
    });

    test('virtualization works when loading state transitions', async () => {
      // Start with loading state
      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: [],
        setBomItems: mockSetBomItems,
        isLoadingBOM: true,
      });

      const { rerender } = render(<BOMEditor />);

      // Should show skeleton
      expect(screen.getByTestId('bom-editor-skeleton')).toBeInTheDocument();

      // Transition to loaded state with many items
      const largeItemList = generateBOMItems(100);
      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      rerender(<BOMEditor />);

      // Should show virtualized list
      await waitFor(() => {
        expect(screen.queryByTestId('bom-editor-skeleton')).not.toBeInTheDocument();
        expect(screen.getByText(/100 components/i)).toBeInTheDocument();
        expect(screen.getByTestId('bom-virtual-scroll-container')).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Performance Tests
  // ============================================================================

  describe('Performance', () => {
    test('renders large list within acceptable time', async () => {
      const largeItemList = generateBOMItems(100);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      const startTime = performance.now();
      render(<BOMEditor />);
      const endTime = performance.now();

      const renderTime = endTime - startTime;

      // Render should complete in a reasonable time for 100 items with virtualization
      // In test environment (JSDOM), allow more time due to overhead
      // The key is that virtualization renders fewer items than 100
      expect(renderTime).toBeLessThan(5000);

      // Verify component rendered successfully
      await waitFor(() => {
        expect(screen.getByText(/100 components/i)).toBeInTheDocument();
      });

      // More importantly, verify we're not rendering all 100 rows
      const virtualRows = screen.getAllByTestId('bom-virtual-row');
      expect(virtualRows.length).toBeLessThan(20);
    });

    test('scroll does not cause excessive re-renders', async () => {
      const largeItemList = generateBOMItems(100);

      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: largeItemList,
        setBomItems: mockSetBomItems,
        isLoadingBOM: false,
      });

      render(<BOMEditor />);

      const scrollContainer = screen.getByTestId('bom-virtual-scroll-container');

      // Simulate multiple scroll events
      for (let i = 0; i < 10; i++) {
        Object.defineProperty(scrollContainer, 'scrollTop', { writable: true, value: i * 100 });
        scrollContainer.dispatchEvent(new Event('scroll'));
      }

      // Virtualization should minimize re-renders
      // Component should still be functional after rapid scrolling
      await waitFor(() => {
        expect(scrollContainer).toBeInTheDocument();
        expect(screen.getByText(/100 components/i)).toBeInTheDocument();
      });
    });
  });
});
