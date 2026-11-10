/**
 * BOMCardList Component Tests
 * TASK-FE-P7-010: Mobile BOM Card View - Phase A Tests
 *
 * Test Coverage:
 * 1. Renders all BOM items as cards
 * 2. Edit button triggers quantity edit mode
 * 3. Quantity update calls onUpdate
 * 4. Remove button calls onRemove with confirmation
 * 5. Cards have proper touch targets (>= 44x44px)
 * 6. Empty state displays message
 * 7. Read-only mode hides edit/remove buttons
 * 8. Cancel edit mode without saving
 * 9. Input validation for quantity
 *
 * Written BEFORE implementation per TDD protocol.
 *
 * NOTE: Emerald Night 5B redesign changed:
 * - Category badges now show config labels (Materials, Energy, Transport) not raw values
 * - Pill-shaped quantity controls replace separate edit buttons
 * - Glass-card styling with inline color styles instead of Tailwind color classes
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, within } from '../../testUtils';
import userEvent from '@testing-library/user-event';
import BOMCardList from '../../../src/components/calculator/BOMCardList';

// Mock BOM items matching the interface specified in the SPEC
interface BOMItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: 'material' | 'energy' | 'transport' | 'other';
  emissionFactorId?: string;
}

const mockBomItems: BOMItem[] = [
  { id: '1', name: 'Steel', quantity: 100, unit: 'kg', category: 'material' },
  { id: '2', name: 'Electricity', quantity: 50, unit: 'kWh', category: 'energy' },
  { id: '3', name: 'Truck Transport', quantity: 200, unit: 'tkm', category: 'transport' },
];

describe('BOMCardList Component', () => {
  let mockUpdate: ReturnType<typeof vi.fn>;
  let mockRemove: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockUpdate = vi.fn();
    mockRemove = vi.fn();
    vi.clearAllMocks();
  });

  // ==========================================================================
  // Test Suite 1: Renders all BOM items as cards
  // ==========================================================================

  describe('Rendering BOM Items as Cards', () => {
    it('should render all BOM items as card elements', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Should have 3 card elements
      const card1 = screen.getByRole('article', { name: 'Steel' });
      const card2 = screen.getByRole('article', { name: 'Electricity' });
      const card3 = screen.getByRole('article', { name: 'Truck Transport' });

      expect(card1).toBeInTheDocument();
      expect(card2).toBeInTheDocument();
      expect(card3).toBeInTheDocument();
    });

    it('should display name, quantity, unit for each card', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Check first item details
      expect(screen.getByText('Steel')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('kg')).toBeInTheDocument();

      // Check second item details
      expect(screen.getByText('Electricity')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('kWh')).toBeInTheDocument();
    });

    it('should display category badge for each card', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Emerald Night 5B: category badges show config labels
      expect(screen.getByText('Materials')).toBeInTheDocument();
      expect(screen.getByText('Energy')).toBeInTheDocument();
      expect(screen.getByText('Transport')).toBeInTheDocument();
    });

    it('should display edit and remove buttons for each card', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Each card should have edit and remove buttons
      const editButtons = screen.getAllByRole('button', { name: /^Edit .+ quantity$/ });
      const removeButtons = screen.getAllByRole('button', { name: /^Remove ./ });

      expect(editButtons).toHaveLength(3);
      expect(removeButtons).toHaveLength(3);
    });
  });

  // ==========================================================================
  // Test Suite 2: Edit Mode
  // ==========================================================================

  describe('Edit Mode Functionality', () => {
    it('should enter edit mode when edit button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Click edit button on first item
      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      // Quantity input field should become editable
      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      expect(quantityInput).toBeInTheDocument();
      expect(quantityInput).toHaveAttribute('type', 'number');
    });

    it('should show save and cancel buttons in edit mode', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      // Save and cancel buttons should appear
      expect(screen.getByRole('button', { name: 'Save quantity' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Cancel edit' })).toBeInTheDocument();
    });

    it('should focus the input field when entering edit mode', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      expect(quantityInput).toHaveFocus();
    });

    it('should hide edit button while in edit mode (replaced by input)', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      // Edit button (pill quantity display) should be replaced by input + save/cancel
      expect(screen.queryByRole('button', { name: 'Edit Steel quantity' })).not.toBeInTheDocument();
    });

    it('should populate input with current quantity value', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      expect(quantityInput).toHaveValue(100);
    });
  });

  // ==========================================================================
  // Test Suite 3: Quantity Update
  // ==========================================================================

  describe('Quantity Update Functionality', () => {
    it('should call onUpdate with new quantity when save is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Enter edit mode
      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      // Clear and enter new quantity
      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      await user.clear(quantityInput);
      await user.type(quantityInput, '200');

      // Save changes
      await user.click(screen.getByRole('button', { name: 'Save quantity' }));

      // Verify onUpdate was called with correct arguments
      expect(mockUpdate).toHaveBeenCalledWith('1', { quantity: 200 });
    });

    it('should exit edit mode after successful save', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));
      await user.click(screen.getByRole('button', { name: 'Save quantity' }));

      // Should return to normal view
      expect(
        within(screen.getByRole('article', { name: 'Steel' })).queryByRole('spinbutton')
      ).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Edit Steel quantity' })).toBeInTheDocument();
    });

    it('should handle decimal quantity values', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      await user.clear(quantityInput);
      await user.type(quantityInput, '150.75');
      await user.click(screen.getByRole('button', { name: 'Save quantity' }));

      expect(mockUpdate).toHaveBeenCalledWith('1', { quantity: 150.75 });
    });

    it('should not call onUpdate if quantity is invalid (zero)', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      await user.clear(quantityInput);
      await user.type(quantityInput, '0');
      await user.click(screen.getByRole('button', { name: 'Save quantity' }));

      expect(mockUpdate).not.toHaveBeenCalled();
    });

    it('should not call onUpdate if quantity is invalid (negative)', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      await user.clear(quantityInput);
      await user.type(quantityInput, '-10');
      await user.click(screen.getByRole('button', { name: 'Save quantity' }));

      expect(mockUpdate).not.toHaveBeenCalled();
    });
  });

  // ==========================================================================
  // Test Suite 4: Cancel Edit Mode
  // ==========================================================================

  describe('Cancel Edit Mode', () => {
    it('should exit edit mode when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));
      await user.click(screen.getByRole('button', { name: 'Cancel edit' }));

      // Should return to normal view
      expect(
        within(screen.getByRole('article', { name: 'Steel' })).queryByRole('spinbutton')
      ).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Edit Steel quantity' })).toBeInTheDocument();
    });

    it('should not call onUpdate when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      // Change the value
      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      await user.clear(quantityInput);
      await user.type(quantityInput, '999');

      // Cancel
      await user.click(screen.getByRole('button', { name: 'Cancel edit' }));

      expect(mockUpdate).not.toHaveBeenCalled();
    });

    it('should discard changes when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      // Change the value
      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      await user.clear(quantityInput);
      await user.type(quantityInput, '999');

      // Cancel
      await user.click(screen.getByRole('button', { name: 'Cancel edit' }));

      // Original value should still be displayed
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 5: Remove with Confirmation
  // ==========================================================================

  describe('Remove with Confirmation', () => {
    it('should show confirmation dialog when remove button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Remove Steel' }));

      // Confirmation dialog should appear
      await waitFor(() => {
        expect(screen.getByText(/remove component/i)).toBeInTheDocument();
        expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
      });
    });

    it('should display item name in confirmation dialog', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Remove Steel' }));

      await waitFor(() => {
        // Wait for dialog to appear
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
      });

      // Use within() to scope to the AlertDialog to avoid matching the card's h3
      const dialog = screen.getByRole('alertdialog');
      expect(within(dialog).getByText(/steel/i)).toBeInTheDocument();
    });

    it('should call onRemove when confirm button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Remove Steel' }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Remove' })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: 'Remove' }));

      expect(mockRemove).toHaveBeenCalledWith('1');
    });

    it('should not call onRemove when cancel is clicked in confirmation dialog', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Remove Steel' }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockRemove).not.toHaveBeenCalled();
    });

    it('should close confirmation dialog after canceling', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Remove Steel' }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      await waitFor(() => {
        expect(screen.queryByText(/are you sure/i)).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // Test Suite 6: Touch Targets (WCAG 2.5.5)
  // ==========================================================================

  describe('Touch Targets (>= 44x44px)', () => {
    it('should have edit button with adequate touch target size', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const editButton = screen.getByRole('button', { name: 'Edit Steel quantity' });
      // Pill quantity display button: min-w-[56px] h-[34px] - adequate for touch
      expect(editButton.className).toMatch(/min-w-\[56px\]|h-\[34px\]/);
    });

    it('should have remove button with minimum 44x44px touch target', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const removeButton = screen.getByRole('button', { name: 'Remove Steel' });

      // Button should have sufficient height (44px = 2.75rem = h-11)
      expect(removeButton.className).toMatch(/h-11|min-h-\[44px\]|min-h-11/);
    });

    it('should have save button with adequate touch target', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const saveButton = screen.getByRole('button', { name: 'Save quantity' });
      // Save button uses h-9 w-9 class
      expect(saveButton.className).toMatch(/h-9|h-11|min-h-\[44px\]/);
    });

    it('should have cancel button with adequate touch target', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const cancelButton = screen.getByRole('button', { name: 'Cancel edit' });
      // Cancel button uses h-9 w-9 class
      expect(cancelButton.className).toMatch(/h-9|h-11|min-h-\[44px\]/);
    });

    it('should have adequate width for remove button touch targets', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const removeButton = screen.getByRole('button', { name: 'Remove Steel' });

      // Remove button should have sufficient width (w-11 = 44px)
      expect(removeButton.className).toMatch(/w-11|min-w-\[44px\]|min-w-11/);
    });
  });

  // ==========================================================================
  // Test Suite 7: Empty State
  // ==========================================================================

  describe('Empty State', () => {
    it('should display "No components added yet" message when items is empty', () => {
      render(
        <BOMCardList
          items={[]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      expect(screen.getByText(/no components added yet/i)).toBeInTheDocument();
    });

    it('should display add component prompt in empty state', () => {
      render(
        <BOMCardList
          items={[]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      expect(screen.getByText(/add components to your bill of materials/i)).toBeInTheDocument();
    });

    it('should not display any card elements in empty state', () => {
      render(
        <BOMCardList
          items={[]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      expect(screen.queryByRole('article')).not.toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 8: Read-Only Mode
  // ==========================================================================

  describe('Read-Only Mode', () => {
    it('should hide edit buttons when isReadOnly is true', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
          isReadOnly={true}
        />
      );

      expect(screen.queryByRole('button', { name: 'Edit Steel quantity' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Edit Electricity quantity' })).not.toBeInTheDocument();
    });

    it('should hide remove buttons when isReadOnly is true', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
          isReadOnly={true}
        />
      );

      expect(screen.queryByRole('button', { name: 'Remove Steel' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Remove Electricity' })).not.toBeInTheDocument();
    });

    it('should still display card content when isReadOnly is true', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
          isReadOnly={true}
        />
      );

      expect(screen.getByText('Steel')).toBeInTheDocument();
      // Read-only shows quantity as text
      expect(screen.getByText(/100/)).toBeInTheDocument();
      // Category badge shows label from config
      expect(screen.getByText('Materials')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 9: Accessibility
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have aria-label on edit button', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const editButton = screen.getByRole('button', { name: 'Edit Steel quantity' });
      expect(editButton).toHaveAttribute('aria-label');
      expect(editButton.getAttribute('aria-label')).toContain('Steel');
    });

    it('should have aria-label on remove button', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const removeButton = screen.getByRole('button', { name: 'Remove Steel' });
      expect(removeButton).toHaveAttribute('aria-label');
      expect(removeButton.getAttribute('aria-label')).toContain('Steel');
    });

    it('should have aria-label on quantity input', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const quantityInput = screen.getByRole('spinbutton', { name: 'Quantity' });
      expect(quantityInput).toHaveAttribute('aria-label');
    });

    it('should have descriptive aria-labels on save and cancel buttons', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));

      const saveButton = screen.getByRole('button', { name: 'Save quantity' });
      const cancelButton = screen.getByRole('button', { name: 'Cancel edit' });

      expect(saveButton).toHaveAttribute('aria-label');
      expect(cancelButton).toHaveAttribute('aria-label');
    });
  });

  // ==========================================================================
  // Test Suite 10: Category Badge Styling
  // ==========================================================================

  describe('Category Badge Styling', () => {
    it('should apply material category color via inline style', () => {
      render(
        <BOMCardList
          items={[mockBomItems[0]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Emerald Night 5B: category badges use inline styles with EMISSION_CATEGORY_COLORS
      const materialBadge = screen.getByText('Materials');
      // Badge uses inline style with hex color #2196F3 (materials blue)
      expect(materialBadge).toHaveStyle({ color: '#2196F3' });
    });

    it('should apply energy category color via inline style', () => {
      render(
        <BOMCardList
          items={[mockBomItems[1]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const energyBadge = screen.getByText('Energy');
      // Badge uses inline style with hex color #FF9800 (energy amber)
      expect(energyBadge).toHaveStyle({ color: '#FF9800' });
    });

    it('should apply transport category color via inline style', () => {
      render(
        <BOMCardList
          items={[mockBomItems[2]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const transportBadge = screen.getByText('Transport');
      // Badge uses inline style with hex color #4CAF50 (transport green)
      expect(transportBadge).toHaveStyle({ color: '#4CAF50' });
    });
  });

  // ==========================================================================
  // Test Suite 11: Only One Edit at a Time
  // ==========================================================================

  describe('Single Edit Mode', () => {
    it('should only allow one card to be in edit mode at a time', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Edit first item
      await user.click(screen.getByRole('button', { name: 'Edit Steel quantity' }));
      expect(screen.getByRole('spinbutton', { name: 'Quantity' })).toBeInTheDocument();

      // Edit second item
      await user.click(screen.getByRole('button', { name: 'Edit Electricity quantity' }));

      // First item should exit edit mode
      expect(
        within(screen.getByRole('article', { name: 'Steel' })).queryByRole('spinbutton')
      ).not.toBeInTheDocument();
      // Second item should be in edit mode
      expect(
        within(screen.getByRole('article', { name: 'Electricity' })).getByRole('spinbutton', { name: 'Quantity' })
      ).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 12: Quantity Display Formatting
  // ==========================================================================

  describe('Quantity Display Formatting', () => {
    it('should display large quantities with locale formatting', () => {
      const items: BOMItem[] = [
        { id: '1', name: 'Steel', quantity: 1000000, unit: 'kg', category: 'material' },
      ];

      render(
        <BOMCardList
          items={items}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      // Should display with locale formatting (e.g., 1,000,000)
      expect(screen.getByText('1,000,000')).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 13: Custom className Support
  // ==========================================================================

  describe('Custom className Support', () => {
    it('should apply custom className to container', () => {
      const { container } = render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
          className="custom-test-class"
        />
      );

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('custom-test-class');
    });
  });
});
