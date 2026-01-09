/**
 * ProductSelector Toggle Styling Tests
 *
 * TASK-FE-P8-009: Test BOM filter toggle button styling
 *
 * Test Scenarios:
 * 1. Active button has distinct styling (background color OR border OR font-weight)
 * 2. Toggle changes styling between buttons when clicked
 * 3. aria-pressed attribute matches styling state
 * 4. Color contrast meets WCAG AA (4.5:1)
 *
 * TDD Phase A: Tests written FIRST before implementation
 *
 * Note: The bug is that the current `bg-primary text-primary-foreground` styling
 * is not visually distinct enough. These tests verify that the active state has
 * ENHANCED styling with explicit colors AND additional visual emphasis (font-weight
 * or ring/border).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProductSelector from '../ProductSelector';
import { useCalculatorStore } from '@/store/calculatorStore';
import { useWizardStore } from '@/store/wizardStore';

// Mock the products API service
vi.mock('@/services/api/products', () => ({
  productsAPI: {
    list: vi.fn(() => Promise.resolve([])),
    getById: vi.fn(),
    search: vi.fn(() => Promise.resolve([])),
  },
}));

// Mock the emission factors API service
vi.mock('@/services/api/emissionFactors', () => ({
  emissionFactorsAPI: {
    list: vi.fn(() => Promise.resolve([])),
  },
}));

// Mock the BOM transform service
vi.mock('@/services/bomTransform', () => ({
  transformAPIBOMToFrontend: vi.fn(() => []),
}));

/**
 * Helper function to check if an element has ENHANCED active styling
 *
 * The bug reported is that `bg-primary text-primary-foreground` alone is not
 * visually distinct. Enhanced styling requires BOTH:
 * 1. Background color that's explicitly visible (primary or explicit color)
 * 2. Additional emphasis (font-weight OR ring/border)
 *
 * This ensures the active state is immediately obvious to users.
 */
const hasEnhancedActiveStyleClass = (element: HTMLElement): boolean => {
  const className = element.className;

  // Check for background color classes (Tailwind patterns)
  const hasBackgroundColor =
    /bg-(primary|blue|green|indigo|purple|slate|zinc|neutral)-\d+/.test(
      className
    ) ||
    className.includes('bg-primary');

  // Check for text color that indicates active state
  const hasActiveTextColor =
    className.includes('text-primary-foreground') ||
    className.includes('text-white');

  // Check for ENHANCED visual emphasis (this is what's MISSING in current implementation)
  const hasFontWeight =
    className.includes('font-medium') ||
    className.includes('font-semibold') ||
    className.includes('font-bold');

  const hasBorderOrRing =
    className.includes('ring-') ||
    className.includes('border-primary') ||
    className.includes('border-2') ||
    className.includes('outline-') ||
    className.includes('shadow-');

  // For active state to be CLEARLY visible, we need:
  // 1. Background + text color (basic styling)
  // 2. AND at least one enhancement (font-weight OR ring/border)
  const hasBasicStyling = hasBackgroundColor && hasActiveTextColor;
  const hasEnhancement = hasFontWeight || hasBorderOrRing;

  return hasBasicStyling && hasEnhancement;
};

/**
 * Helper function to check if element has basic active styling
 * (background + text color, but may lack enhancement)
 */
const hasBasicActiveStyleClass = (element: HTMLElement): boolean => {
  const className = element.className;

  const hasBackgroundColor =
    /bg-(primary|blue|green|indigo|purple|slate|zinc|neutral)-\d+/.test(
      className
    ) ||
    className.includes('bg-primary');

  const hasActiveTextColor =
    className.includes('text-primary-foreground') ||
    className.includes('text-white');

  return hasBackgroundColor && hasActiveTextColor;
};

/**
 * Helper function to check if element has "inactive" styling
 * Inactive styling typically has no background or a muted/transparent one
 */
const hasInactiveStyleClass = (element: HTMLElement): boolean => {
  const className = element.className;

  // Inactive buttons typically have:
  // - No solid background OR muted/ghost background
  // - hover: states only (not base states)
  // - No ring/border emphasis

  const hasNoSolidBackground =
    !className.includes('bg-primary') &&
    !className.includes('bg-blue-') &&
    !className.includes('bg-green-') &&
    !className.includes('bg-indigo-');

  return hasNoSolidBackground;
};

/**
 * Helper to wait for component to finish loading
 */
const waitForComponentToLoad = async () => {
  // Wait for the skeleton to disappear and toggle buttons to appear
  await waitFor(() => {
    expect(screen.queryByTestId('product-selector-skeleton')).not.toBeInTheDocument();
  });
};

describe('ProductSelector - BOM Filter Toggle Styling', () => {
  beforeEach(() => {
    // Reset stores before each test
    localStorage.clear();
    useCalculatorStore.getState().reset();
    useWizardStore.getState().reset();
  });

  describe('Scenario 1: Active button has distinct styling', () => {
    it('should apply ENHANCED active styling to "With BOMs" button when showOnlyWithBom is true', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      // Get the toggle buttons by their test IDs
      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: "With BOMs" should have ENHANCED active styling (not just basic)
      // This is the key test - the bug is that basic styling alone is not distinct
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(true);

      // Assert: "All Products" should NOT have active styling
      expect(hasBasicActiveStyleClass(allProductsButton)).toBe(false);
    });

    it('should have visible background color AND font-weight/ring on active button', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const className = withBomButton.className;

      // Assert: Active button should have background color class
      expect(className).toMatch(
        /bg-(primary|blue-\d+|indigo-\d+|green-\d+|slate-\d+)/
      );

      // Assert: Active button should have ADDITIONAL visual emphasis
      // This is what makes the styling "clearly visible" as per SPEC
      const hasEnhancement =
        className.includes('font-medium') ||
        className.includes('font-semibold') ||
        className.includes('font-bold') ||
        className.includes('ring-') ||
        className.includes('shadow-');

      expect(hasEnhancement).toBe(true);
    });

    it('should apply inactive styling to non-selected button', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: Inactive button should NOT have solid background
      expect(hasInactiveStyleClass(allProductsButton)).toBe(true);
    });

    it('should have clear visual distinction between active and inactive buttons', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: Both buttons exist
      expect(withBomButton).toBeInTheDocument();
      expect(allProductsButton).toBeInTheDocument();

      // Assert: Active button has enhanced styling, inactive does not
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(true);
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(false);
    });
  });

  describe('Scenario 2: Toggle changes styling between buttons', () => {
    it('should change "All Products" to ENHANCED active styling when clicked', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Verify initial state - "All Products" is inactive
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(false);

      // Act: Click "All Products" button
      await user.click(allProductsButton);

      // Assert: "All Products" should now have ENHANCED active styling
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(true);
    });

    it('should remove active styling from "With BOMs" when "All Products" is clicked', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Verify initial state - "With BOMs" has enhanced active styling
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(true);

      // Act: Click "All Products" button
      await user.click(allProductsButton);

      // Assert: "With BOMs" should no longer have active styling
      expect(hasBasicActiveStyleClass(withBomButton)).toBe(false);
    });

    it('should toggle styling back to "With BOMs" when clicked again', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Act: Click "All Products" first
      await user.click(allProductsButton);

      // Verify intermediate state
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(true);
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(false);

      // Act: Click "With BOMs" to toggle back
      await user.click(withBomButton);

      // Assert: Styling should return to initial state
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(true);
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(false);
    });

    it('should update styling immediately on click without delay', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Act & Assert: Click and immediately check styling
      await user.click(allProductsButton);

      // Styling should be updated synchronously (no async delay needed)
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(true);
    });
  });

  describe('Scenario 3: Accessibility - aria-pressed matches styling', () => {
    it('should have aria-pressed="true" on active button', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');

      // Assert: aria-pressed should match active state
      expect(withBomButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('should have aria-pressed="false" on inactive button', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: aria-pressed should match inactive state
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');
    });

    it('should update aria-pressed when toggle is clicked', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Verify initial state
      expect(withBomButton).toHaveAttribute('aria-pressed', 'true');
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');

      // Act: Click "All Products"
      await user.click(allProductsButton);

      // Assert: aria-pressed should be updated
      expect(withBomButton).toHaveAttribute('aria-pressed', 'false');
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
    });

    it('should have aria-pressed matching visual styling state', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: When aria-pressed="true", button should have enhanced active styling
      expect(withBomButton).toHaveAttribute('aria-pressed', 'true');
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(true);

      // Assert: When aria-pressed="false", button should NOT have active styling
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');
      expect(hasBasicActiveStyleClass(allProductsButton)).toBe(false);

      // Act: Toggle and verify consistency
      await user.click(allProductsButton);

      // Assert: After toggle, aria-pressed and styling should still match
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'true');
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(true);

      expect(withBomButton).toHaveAttribute('aria-pressed', 'false');
      expect(hasBasicActiveStyleClass(withBomButton)).toBe(false);
    });

    it('should have correct button roles for screen readers', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: Buttons should be actual button elements or have button role
      expect(withBomButton.tagName).toBe('BUTTON');
      expect(allProductsButton.tagName).toBe('BUTTON');

      // Assert: Buttons should have type="button" to prevent form submission
      expect(withBomButton).toHaveAttribute('type', 'button');
      expect(allProductsButton).toHaveAttribute('type', 'button');
    });
  });

  describe('Scenario 4: Color contrast meets WCAG AA', () => {
    /**
     * Note: JSDOM doesn't compute actual CSS colors, so we verify
     * that appropriate Tailwind classes are used that meet WCAG AA.
     *
     * The following color combinations meet WCAG AA (4.5:1):
     * - bg-primary with text-primary-foreground
     * - bg-blue-600 with text-white
     * - bg-gray-900 with text-white
     * - hover:bg-muted typically uses accessible colors
     */

    it('should use color classes that meet WCAG AA for active state', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const className = withBomButton.className;

      // Assert: Should use accessible color combinations
      // Primary with primary-foreground is designed to be accessible
      const hasAccessibleColorCombo =
        (className.includes('bg-primary') &&
          className.includes('text-primary-foreground')) ||
        (className.includes('bg-blue-600') && className.includes('text-white')) ||
        (className.includes('bg-blue-700') && className.includes('text-white')) ||
        (className.includes('bg-indigo-600') &&
          className.includes('text-white')) ||
        (className.includes('bg-slate-900') &&
          className.includes('text-white'));

      expect(hasAccessibleColorCombo).toBe(true);
    });

    it('should use color classes that meet WCAG AA for inactive state', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const allProductsButton = screen.getByTestId('bom-filter-all');
      const className = allProductsButton.className;

      // Assert: Inactive state should use readable text
      // Typically text-gray-700 on white background meets WCAG AA
      const hasAccessibleInactiveColors =
        !className.includes('text-gray-300') && // Too light
        !className.includes('text-gray-200') && // Too light
        !className.includes('text-gray-100'); // Too light

      expect(hasAccessibleInactiveColors).toBe(true);
    });

    it('should maintain distinguishable styling between states', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: Active and inactive states should be visually different
      // This ensures users can distinguish between them
      const activeClassName = withBomButton.className;
      const inactiveClassName = allProductsButton.className;

      // They should have different class combinations
      expect(activeClassName).not.toBe(inactiveClassName);

      // Active should have more styling (background, text color)
      expect(activeClassName.length).toBeGreaterThan(0);
      expect(inactiveClassName.length).toBeGreaterThan(0);
    });
  });

  describe('Additional Test Requirements', () => {
    it('should have keyboard focus visible on both buttons', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Act: Tab to the buttons
      await user.tab();

      // Assert: At least one button should be focusable
      // The exact focus order depends on the DOM structure
      const focusedElement = document.activeElement;
      expect(
        focusedElement === withBomButton || focusedElement === allProductsButton
      ).toBe(true);
    });

    it('should support keyboard navigation between toggle buttons', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');

      // Act: Focus and press Enter to activate
      withBomButton.focus();
      await user.keyboard('{Enter}');

      // The button should be activatable via keyboard
      expect(withBomButton).toHaveAttribute('aria-pressed', 'true');

      // Tab to next button
      await user.tab();

      // Focus should move to the other button or stay in the toggle group
      const currentFocus = document.activeElement;
      expect(currentFocus).toBeInstanceOf(HTMLButtonElement);
    });

    it('should render toggle buttons within a container for visual grouping', async () => {
      // Arrange & Act
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Assert: Both buttons should share a parent container
      const withBomParent = withBomButton.parentElement;
      const allProductsParent = allProductsButton.parentElement;

      expect(withBomParent).toBe(allProductsParent);

      // The container should have flex for proper layout
      if (withBomParent) {
        expect(withBomParent.className).toContain('flex');
      }
    });

    it('should maintain toggle state after rapid clicking', async () => {
      // Arrange
      const user = userEvent.setup();
      render(<ProductSelector />);
      await waitForComponentToLoad();

      const withBomButton = screen.getByTestId('bom-filter-with-bom');
      const allProductsButton = screen.getByTestId('bom-filter-all');

      // Act: Rapid clicking
      await user.click(allProductsButton);
      await user.click(withBomButton);
      await user.click(allProductsButton);
      await user.click(withBomButton);

      // Assert: Final state should be "With BOMs" active with enhanced styling
      expect(withBomButton).toHaveAttribute('aria-pressed', 'true');
      expect(allProductsButton).toHaveAttribute('aria-pressed', 'false');
      expect(hasEnhancedActiveStyleClass(withBomButton)).toBe(true);
      expect(hasEnhancedActiveStyleClass(allProductsButton)).toBe(false);
    });
  });
});
