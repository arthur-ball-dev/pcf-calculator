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
      const card1 = screen.getByTestId('bom-card-1');
      const card2 = screen.getByTestId('bom-card-2');
      const card3 = screen.getByTestId('bom-card-3');

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

      expect(screen.getByText('material')).toBeInTheDocument();
      expect(screen.getByText('energy')).toBeInTheDocument();
      expect(screen.getByText('transport')).toBeInTheDocument();
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
      const editButtons = screen.getAllByTestId(/^edit-btn-/);
      const removeButtons = screen.getAllByTestId(/^remove-btn-/);

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
      await user.click(screen.getByTestId('edit-btn-1'));

      // Quantity input field should become editable
      const quantityInput = screen.getByTestId('quantity-input-1');
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

      await user.click(screen.getByTestId('edit-btn-1'));

      // Save and cancel buttons should appear
      expect(screen.getByTestId('save-btn-1')).toBeInTheDocument();
      expect(screen.getByTestId('cancel-btn-1')).toBeInTheDocument();
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

      await user.click(screen.getByTestId('edit-btn-1'));

      const quantityInput = screen.getByTestId('quantity-input-1');
      expect(quantityInput).toHaveFocus();
    });

    it('should hide edit and remove buttons while in edit mode', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByTestId('edit-btn-1'));

      // Edit and remove buttons should be replaced by save and cancel
      expect(screen.queryByTestId('edit-btn-1')).not.toBeInTheDocument();
      expect(screen.queryByTestId('remove-btn-1')).not.toBeInTheDocument();
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

      await user.click(screen.getByTestId('edit-btn-1'));

      const quantityInput = screen.getByTestId('quantity-input-1');
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
      await user.click(screen.getByTestId('edit-btn-1'));

      // Clear and enter new quantity
      const quantityInput = screen.getByTestId('quantity-input-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '200');

      // Save changes
      await user.click(screen.getByTestId('save-btn-1'));

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

      await user.click(screen.getByTestId('edit-btn-1'));
      await user.click(screen.getByTestId('save-btn-1'));

      // Should return to normal view
      expect(screen.queryByTestId('quantity-input-1')).not.toBeInTheDocument();
      expect(screen.getByTestId('edit-btn-1')).toBeInTheDocument();
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

      await user.click(screen.getByTestId('edit-btn-1'));

      const quantityInput = screen.getByTestId('quantity-input-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '150.75');
      await user.click(screen.getByTestId('save-btn-1'));

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

      await user.click(screen.getByTestId('edit-btn-1'));

      const quantityInput = screen.getByTestId('quantity-input-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '0');
      await user.click(screen.getByTestId('save-btn-1'));

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

      await user.click(screen.getByTestId('edit-btn-1'));

      const quantityInput = screen.getByTestId('quantity-input-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '-10');
      await user.click(screen.getByTestId('save-btn-1'));

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

      await user.click(screen.getByTestId('edit-btn-1'));
      await user.click(screen.getByTestId('cancel-btn-1'));

      // Should return to normal view
      expect(screen.queryByTestId('quantity-input-1')).not.toBeInTheDocument();
      expect(screen.getByTestId('edit-btn-1')).toBeInTheDocument();
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

      await user.click(screen.getByTestId('edit-btn-1'));

      // Change the value
      const quantityInput = screen.getByTestId('quantity-input-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '999');

      // Cancel
      await user.click(screen.getByTestId('cancel-btn-1'));

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

      await user.click(screen.getByTestId('edit-btn-1'));

      // Change the value
      const quantityInput = screen.getByTestId('quantity-input-1');
      await user.clear(quantityInput);
      await user.type(quantityInput, '999');

      // Cancel
      await user.click(screen.getByTestId('cancel-btn-1'));

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

      await user.click(screen.getByTestId('remove-btn-1'));

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

      await user.click(screen.getByTestId('remove-btn-1'));

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

      await user.click(screen.getByTestId('remove-btn-1'));

      await waitFor(() => {
        expect(screen.getByTestId('confirm-remove-btn')).toBeInTheDocument();
      });

      await user.click(screen.getByTestId('confirm-remove-btn'));

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

      await user.click(screen.getByTestId('remove-btn-1'));

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

      await user.click(screen.getByTestId('remove-btn-1'));

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
    it('should have edit button with minimum 44x44px touch target', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const editButton = screen.getByTestId('edit-btn-1');
      const styles = window.getComputedStyle(editButton);

      // Button should have sufficient height (44px = 2.75rem = h-11)
      // Check for h-11 class or min-h-[44px] or computed height
      expect(editButton.className).toMatch(/h-11|min-h-\[44px\]|min-h-11/);
    });

    it('should have remove button with minimum 44x44px touch target', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const removeButton = screen.getByTestId('remove-btn-1');

      // Button should have sufficient height (44px = 2.75rem = h-11)
      expect(removeButton.className).toMatch(/h-11|min-h-\[44px\]|min-h-11/);
    });

    it('should have save button with minimum 44x44px touch target', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByTestId('edit-btn-1'));

      const saveButton = screen.getByTestId('save-btn-1');
      expect(saveButton.className).toMatch(/h-11|min-h-\[44px\]|min-h-11/);
    });

    it('should have cancel button with minimum 44x44px touch target', async () => {
      const user = userEvent.setup();
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      await user.click(screen.getByTestId('edit-btn-1'));

      const cancelButton = screen.getByTestId('cancel-btn-1');
      expect(cancelButton.className).toMatch(/h-11|min-h-\[44px\]|min-h-11/);
    });

    it('should have adequate width for touch targets', () => {
      render(
        <BOMCardList
          items={mockBomItems}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const editButton = screen.getByTestId('edit-btn-1');
      const removeButton = screen.getByTestId('remove-btn-1');

      // Buttons should have sufficient width (w-11 = 44px)
      expect(editButton.className).toMatch(/w-11|min-w-\[44px\]|min-w-11/);
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

      expect(screen.queryByTestId(/^bom-card-/)).not.toBeInTheDocument();
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

      expect(screen.queryByTestId('edit-btn-1')).not.toBeInTheDocument();
      expect(screen.queryByTestId('edit-btn-2')).not.toBeInTheDocument();
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

      expect(screen.queryByTestId('remove-btn-1')).not.toBeInTheDocument();
      expect(screen.queryByTestId('remove-btn-2')).not.toBeInTheDocument();
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
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('material')).toBeInTheDocument();
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

      const editButton = screen.getByTestId('edit-btn-1');
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

      const removeButton = screen.getByTestId('remove-btn-1');
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

      await user.click(screen.getByTestId('edit-btn-1'));

      const quantityInput = screen.getByTestId('quantity-input-1');
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

      await user.click(screen.getByTestId('edit-btn-1'));

      const saveButton = screen.getByTestId('save-btn-1');
      const cancelButton = screen.getByTestId('cancel-btn-1');

      expect(saveButton).toHaveAttribute('aria-label');
      expect(cancelButton).toHaveAttribute('aria-label');
    });
  });

  // ==========================================================================
  // Test Suite 10: Category Badge Styling
  // ==========================================================================

  describe('Category Badge Styling', () => {
    it('should apply material category color', () => {
      render(
        <BOMCardList
          items={[mockBomItems[0]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const materialBadge = screen.getByText('material');
      expect(materialBadge.className).toMatch(/bg-blue|blue/i);
    });

    it('should apply energy category color', () => {
      render(
        <BOMCardList
          items={[mockBomItems[1]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const energyBadge = screen.getByText('energy');
      expect(energyBadge.className).toMatch(/bg-yellow|yellow/i);
    });

    it('should apply transport category color', () => {
      render(
        <BOMCardList
          items={[mockBomItems[2]]}
          onUpdate={mockUpdate}
          onRemove={mockRemove}
        />
      );

      const transportBadge = screen.getByText('transport');
      expect(transportBadge.className).toMatch(/bg-green|green/i);
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
      await user.click(screen.getByTestId('edit-btn-1'));
      expect(screen.getByTestId('quantity-input-1')).toBeInTheDocument();

      // Edit second item
      await user.click(screen.getByTestId('edit-btn-2'));

      // First item should exit edit mode
      expect(screen.queryByTestId('quantity-input-1')).not.toBeInTheDocument();
      // Second item should be in edit mode
      expect(screen.getByTestId('quantity-input-2')).toBeInTheDocument();
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
