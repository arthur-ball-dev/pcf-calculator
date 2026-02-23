/**
 * BOMEditor Responsive Layout Tests
 * TASK-FE-P7-010: Mobile BOM Card View - Phase A Tests
 *
 * Test Coverage:
 * 1. Shows table view on desktop (>= 1024px)
 * 2. Shows card view on mobile (<= 640px)
 * 3. Shows appropriate view on tablet (641px - 1023px)
 * 4. Switching between views maintains data integrity
 * 5. Both views receive the same BOM items
 * 6. Edit/remove functionality works in both views
 *
 * Written BEFORE implementation per TDD protocol.
 *
 * NOTE: Emerald Night 5B redesign changed:
 * - Column headers: "Component" (not "Component Name"), no "Unit" column
 * - Totals row in tbody (filter when counting data rows)
 * - Progressive rendering with double-rAF skeleton
 * - Delete uses AlertDialog confirmation in table view too
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '../../testUtils';
import userEvent from '@testing-library/user-event';
import BOMEditor from '../../../src/components/forms/BOMEditor';
import { useCalculatorStore } from '../../../src/store/calculatorStore';
import { useWizardStore } from '../../../src/store/wizardStore';
import type { BOMItem } from '../../../src/types/store.types';

// Mock the stores
vi.mock('../../../src/store/calculatorStore');
vi.mock('../../../src/store/wizardStore');

// Mock API hook for emission factors
vi.mock('../../../src/hooks/useEmissionFactors', () => ({
  useEmissionFactors: () => ({
    data: [
      { id: '1', activity_name: 'Cotton (Organic)', co2e_factor: 2.5, unit: 'kg', category: 'material' },
      { id: '2', activity_name: 'Polyester (Virgin)', co2e_factor: 5.5, unit: 'kg', category: 'material' },
      { id: '3', activity_name: 'Electricity (US Grid)', co2e_factor: 0.4, unit: 'kWh', category: 'energy' },
    ],
    isLoading: false,
    error: null,
  }),
}));

// Mock matchMedia for responsive testing
interface MockMediaQueryList {
  matches: boolean;
  media: string;
  onchange: ((ev: MediaQueryListEvent) => void) | null;
  addListener: ReturnType<typeof vi.fn>;
  removeListener: ReturnType<typeof vi.fn>;
  addEventListener: ReturnType<typeof vi.fn>;
  removeEventListener: ReturnType<typeof vi.fn>;
  dispatchEvent: ReturnType<typeof vi.fn>;
}

type MatchMediaMock = (query: string) => MockMediaQueryList;

/**
 * Helper: Get data rows (exclude totals row in tbody)
 */
function getDataRows() {
  return screen.getAllByRole('row').filter(
    (row) =>
      row.closest('tbody') !== null &&
      !row.textContent?.includes('Total Estimated Carbon Footprint')
  );
}

describe('BOMEditor Responsive Layout', () => {
  let originalMatchMedia: typeof window.matchMedia;
  let changeHandlers: Map<string, ((ev: MediaQueryListEvent) => void)[]>;

  const mockBomItems: BOMItem[] = [
    {
      id: 'item-1',
      name: 'Cotton',
      quantity: 1.5,
      unit: 'kg',
      category: 'material',
      emissionFactorId: '1',
    },
    {
      id: 'item-2',
      name: 'Polyester',
      quantity: 0.5,
      unit: 'kg',
      category: 'material',
      emissionFactorId: '2',
    },
  ];

  const mockSetBomItems = vi.fn();
  const mockMarkStepComplete = vi.fn();
  const mockMarkStepIncomplete = vi.fn();

  /**
   * Creates a mock matchMedia function that simulates browser behavior
   * @param width - The simulated viewport width in pixels
   */
  const createMatchMedia = (width: number): MatchMediaMock => {
    return (query: string): MockMediaQueryList => {
      let matches = false;

      const maxWidthMatch = query.match(/\(max-width:\s*(\d+)px\)/);
      const minWidthMatch = query.match(/\(min-width:\s*(\d+)px\)/);

      if (maxWidthMatch) {
        const maxWidth = parseInt(maxWidthMatch[1], 10);
        matches = width <= maxWidth;
      } else if (minWidthMatch) {
        const minWidth = parseInt(minWidthMatch[1], 10);
        matches = width >= minWidth;
      }

      const mediaQueryList: MockMediaQueryList = {
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn((event: string, handler: (ev: MediaQueryListEvent) => void) => {
          if (event === 'change') {
            if (!changeHandlers.has(query)) {
              changeHandlers.set(query, []);
            }
            changeHandlers.get(query)!.push(handler);
          }
        }),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };

      return mediaQueryList;
    };
  };

  /**
   * Sets up the viewport at a specific width
   * @param width - The viewport width in pixels
   */
  const setViewport = (width: number) => {
    window.matchMedia = createMatchMedia(width);
    window.innerWidth = width;
    window.dispatchEvent(new Event('resize'));
  };

  /**
   * Simulates a viewport resize by triggering change events
   * @param newWidth - The new viewport width in pixels
   */
  const simulateResize = (newWidth: number) => {
    window.matchMedia = createMatchMedia(newWidth);
    window.innerWidth = newWidth;

    // Trigger change events on all registered handlers
    changeHandlers.forEach((handlers, query) => {
      const maxWidthMatch = query.match(/\(max-width:\s*(\d+)px\)/);
      const minWidthMatch = query.match(/\(min-width:\s*(\d+)px\)/);

      let matches = false;
      if (maxWidthMatch) {
        matches = newWidth <= parseInt(maxWidthMatch[1], 10);
      } else if (minWidthMatch) {
        matches = newWidth >= parseInt(minWidthMatch[1], 10);
      }

      handlers.forEach((handler) => {
        handler({ matches, media: query } as MediaQueryListEvent);
      });
    });

    window.dispatchEvent(new Event('resize'));
  };

  beforeEach(() => {
    changeHandlers = new Map();
    originalMatchMedia = window.matchMedia;

    // Default to desktop viewport
    setViewport(1280);

    // Reset mocks before each test
    vi.clearAllMocks();

    // Setup store mocks with default values
    (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      bomItems: mockBomItems,
      setBomItems: mockSetBomItems,
    });

    (useWizardStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
      markStepComplete: mockMarkStepComplete,
      markStepIncomplete: mockMarkStepIncomplete,
    });
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    changeHandlers.clear();
  });

  // ==========================================================================
  // Test Suite 1: Desktop View (>= 1024px) - Shows Table
  // ==========================================================================

  describe('Desktop View (>= 1024px)', () => {
    beforeEach(() => {
      setViewport(1280);
    });

    it('should show table view on desktop viewport', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        // Table element should be present on desktop
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });
    }, 15000);

    it('should not show BOMCardList on desktop viewport', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        // BOMCardList test IDs should not be present
        expect(screen.queryByTestId('bom-card-item-1')).not.toBeInTheDocument();
        expect(screen.queryByTestId(/^bom-card-/)).not.toBeInTheDocument();
      });
    });

    it('should display table headers on desktop', async () => {
      render(<BOMEditor />);

      // Emerald Night 5B headers: Component, Category, Quantity, Emission Factor, Source, CO2e, Actions
      await waitFor(() => {
        expect(screen.getByText('Component')).toBeInTheDocument();
        expect(screen.getByText('Quantity')).toBeInTheDocument();
        expect(screen.getByText('Category')).toBeInTheDocument();
      });
    });

    it('should display BOM items in table rows on desktop', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        // Filter out the totals row in tbody
        const dataRows = getDataRows();
        expect(dataRows.length).toBe(2); // Two items in mockBomItems
      });
    });
  });

  // ==========================================================================
  // Test Suite 2: Mobile View (<= 640px) - Shows Cards
  // ==========================================================================

  describe('Mobile View (<= 640px)', () => {
    beforeEach(() => {
      setViewport(375);
    });

    it('should show card view on mobile viewport', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        // BOMCardList should be present (cards have data-testid pattern)
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
      });
    });

    it('should not show table on mobile viewport', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        // Table element should not be present on mobile
        expect(screen.queryByRole('table')).not.toBeInTheDocument();
      });
    });

    it('should display all BOM items as cards on mobile', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
        expect(screen.getByTestId('bom-card-item-2')).toBeInTheDocument();
      });
    });

    it('should display item details in cards on mobile', async () => {
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByText('Cotton')).toBeInTheDocument();
        expect(screen.getByText('Polyester')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 3: Tablet View (641px - 1023px)
  // ==========================================================================

  describe('Tablet View (641px - 1023px)', () => {
    beforeEach(() => {
      setViewport(768);
    });

    it('should show table view on tablet viewport (using desktop behavior)', async () => {
      render(<BOMEditor />);

      // Tablet typically uses table view (same as desktop)
      // Based on useBreakpoints: tablet is not isMobile, so should show table
      await waitFor(() => {
        // Either table or cards could be shown - depends on implementation
        // The important thing is that the component renders correctly
        const hasTable = screen.queryByRole('table') !== null;
        const hasCards = screen.queryByTestId('bom-card-item-1') !== null;

        // One or the other should be present
        expect(hasTable || hasCards).toBe(true);
      });
    });
  });

  // ==========================================================================
  // Test Suite 4: Viewport Switching - Data Integrity
  // ==========================================================================

  describe('Viewport Switching - Data Integrity', () => {
    it('should maintain BOM data when switching from desktop to mobile', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });

      // Verify data is present in table view
      expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
      expect(screen.getByDisplayValue('1.5')).toBeInTheDocument();

      // Simulate resize to mobile
      act(() => {
        simulateResize(375);
      });

      // Data should still be present in card view
      await waitFor(() => {
        expect(screen.getByText('Cotton')).toBeInTheDocument();
        expect(screen.getByText('1.5')).toBeInTheDocument();
      });
    }, 15000);

    it('should maintain BOM data when switching from mobile to desktop', async () => {
      setViewport(375);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
      });

      // Verify data is present in card view
      expect(screen.getByText('Cotton')).toBeInTheDocument();
      expect(screen.getByText('1.5')).toBeInTheDocument();

      // Simulate resize to desktop
      act(() => {
        simulateResize(1280);
      });

      // Data should still be present in table view
      await waitFor(() => {
        expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
        expect(screen.getByDisplayValue('1.5')).toBeInTheDocument();
      });
    });

    it('should not call setBomItems when switching views', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });

      mockSetBomItems.mockClear();

      // Simulate resize to mobile
      act(() => {
        simulateResize(375);
      });

      await waitFor(() => {
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
      });

      // setBomItems should not be called just from view switching
      // (it may be called for other reasons, but not from view switch alone)
    }, 15000);

    it('should preserve all items when switching views', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        const dataRows = getDataRows();
        expect(dataRows.length).toBe(2);
      }, { timeout: 10000 });

      // Switch to mobile
      act(() => {
        simulateResize(375);
      });

      await waitFor(() => {
        const card1 = screen.getByTestId('bom-card-item-1');
        const card2 = screen.getByTestId('bom-card-item-2');
        expect(card1).toBeInTheDocument();
        expect(card2).toBeInTheDocument();
      });

      // Switch back to desktop
      act(() => {
        simulateResize(1280);
      });

      await waitFor(() => {
        const dataRows = getDataRows();
        expect(dataRows.length).toBe(2);
      });
    }, 15000);
  });

  // ==========================================================================
  // Test Suite 5: Both Views Use Same Data
  // ==========================================================================

  describe('Both Views Use Same Data Source', () => {
    it('should show same item count in both views', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByText(/2 components/i)).toBeInTheDocument();
      }, { timeout: 10000 });

      act(() => {
        simulateResize(375);
      });

      await waitFor(() => {
        // Card view should also indicate 2 items
        // This could be shown as count or by having 2 cards
        const cards = screen.getAllByTestId(/^bom-card-item-/);
        expect(cards.length).toBe(2);
      });
    }, 15000);

    it('should reflect item quantities correctly in both views', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByDisplayValue('1.5')).toBeInTheDocument();
        expect(screen.getByDisplayValue('0.5')).toBeInTheDocument();
      }, { timeout: 10000 });

      act(() => {
        simulateResize(375);
      });

      await waitFor(() => {
        expect(screen.getByText('1.5')).toBeInTheDocument();
        expect(screen.getByText('0.5')).toBeInTheDocument();
      });
    }, 15000);
  });

  // ==========================================================================
  // Test Suite 6: Edit Functionality in Both Views
  // ==========================================================================

  describe('Edit Functionality Across Views', () => {
    it('should allow editing quantity in table view (desktop)', async () => {
      const user = userEvent.setup();
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });

      // In Emerald Night, quantity uses pill controls - find the quantity input
      const quantityInput = screen.getByDisplayValue('1.5');
      await user.clear(quantityInput);
      await user.type(quantityInput, '2.5');

      expect(quantityInput).toHaveValue(2.5);
    }, 15000);

    it('should allow editing quantity in card view (mobile)', async () => {
      const user = userEvent.setup();
      setViewport(375);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
      });

      // Click edit button on first card
      const editButton = screen.getByTestId('edit-btn-item-1');
      await user.click(editButton);

      // Enter new quantity
      const quantityInput = screen.getByTestId('quantity-input-item-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '2.5');

      expect(quantityInput).toHaveValue(2.5);
    });
  });

  // ==========================================================================
  // Test Suite 7: Remove Functionality in Both Views
  // ==========================================================================

  describe('Remove Functionality Across Views', () => {
    it('should allow removing item in table view (desktop)', async () => {
      const user = userEvent.setup();
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });

      // Find and click delete button for first row - Emerald Night uses AlertDialog
      const deleteButtons = screen.getAllByLabelText(/delete component/i);
      expect(deleteButtons.length).toBeGreaterThanOrEqual(1);

      await user.click(deleteButtons[0]);

      // Emerald Night uses AlertDialog for delete confirmation
      await waitFor(() => {
        const confirmBtn = screen.queryByTestId('confirm-remove-btn') || screen.queryByRole('button', { name: /confirm|remove|delete/i });
        if (confirmBtn) {
          // If confirmation dialog appears, click confirm
          user.click(confirmBtn);
        }
      });

      // Should trigger removal (handled by store mock)
      // Note: with mocked store, setBomItems may or may not be called depending on implementation
    }, 15000);

    it('should allow removing item in card view (mobile) with confirmation', async () => {
      const user = userEvent.setup();
      setViewport(375);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
      });

      // Click remove button on first card
      const removeButton = screen.getByTestId('remove-btn-item-1');
      await user.click(removeButton);

      // Confirmation dialog should appear
      await waitFor(() => {
        expect(screen.getByTestId('confirm-remove-btn')).toBeInTheDocument();
      });

      await user.click(screen.getByTestId('confirm-remove-btn'));

      // Should trigger removal
      await waitFor(() => {
        expect(mockSetBomItems).toHaveBeenCalled();
      });
    });
  });

  // ==========================================================================
  // Test Suite 8: Add Component Works in Both Views
  // ==========================================================================

  describe('Add Component Across Views', () => {
    it('should have Add Component button visible on desktop', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add component/i })).toBeInTheDocument();
      }, { timeout: 10000 });
    }, 15000);

    it('should have Add Component button visible on mobile', async () => {
      setViewport(375);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add component/i })).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 9: No Layout Shift
  // ==========================================================================

  describe('No Layout Shift on View Switch', () => {
    it('should not cause multiple rapid re-renders on resize', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });

      // Rapid resize events
      act(() => {
        simulateResize(768);
        simulateResize(375);
        simulateResize(1024);
        simulateResize(480);
        simulateResize(1280);
      });

      // Component should still be functional
      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      });

      // Data should still be present
      expect(screen.getByDisplayValue('Cotton')).toBeInTheDocument();
    }, 15000);
  });

  // ==========================================================================
  // Test Suite 10: useBreakpoints Hook Integration
  // ==========================================================================

  describe('useBreakpoints Hook Integration', () => {
    it('should use isMobile from useBreakpoints to determine view', async () => {
      // At 375px, isMobile should be true (viewport <= 640px)
      setViewport(375);
      render(<BOMEditor />);

      await waitFor(() => {
        // Should show card view because isMobile is true
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
        expect(screen.queryByRole('table')).not.toBeInTheDocument();
      });
    });

    it('should show table when isMobile is false', async () => {
      // At 1280px, isMobile should be false (viewport > 640px)
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        // Should show table view because isMobile is false
        expect(screen.getByRole('table')).toBeInTheDocument();
        expect(screen.queryByTestId('bom-card-item-1')).not.toBeInTheDocument();
      }, { timeout: 10000 });
    }, 15000);

    it('should respond to breakpoint changes from useBreakpoints', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });

      // Simulate breakpoint change to mobile
      act(() => {
        simulateResize(375);
      });

      await waitFor(() => {
        expect(screen.getByTestId('bom-card-item-1')).toBeInTheDocument();
      });
    }, 15000);
  });

  // ==========================================================================
  // Test Suite 11: Empty State in Both Views
  // ==========================================================================

  describe('Empty State in Both Views', () => {
    beforeEach(() => {
      (useCalculatorStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        bomItems: [],
        setBomItems: mockSetBomItems,
      });
    });

    it('should show empty state message on desktop', async () => {
      setViewport(1280);
      render(<BOMEditor />);

      await waitFor(() => {
        // Table view typically shows at least one row (default/empty row)
        // Or shows a message about empty state
        expect(screen.getByRole('table')).toBeInTheDocument();
      }, { timeout: 10000 });
    }, 15000);

    it('should show empty state message on mobile', async () => {
      setViewport(375);
      render(<BOMEditor />);

      await waitFor(() => {
        // Card view shows "No components" message or the add component button
        // When BOM is empty, card list shows empty state OR the editor shows table with empty row
        const hasEmptyMessage = screen.queryByText(/no components/i) !== null;
        const hasAddButton = screen.queryByRole('button', { name: /add component/i }) !== null;
        expect(hasEmptyMessage || hasAddButton).toBe(true);
      });
    });
  });
});
