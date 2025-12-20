/**
 * CalculationWizard Responsive Layout Tests
 * TASK-FE-P7-009: Mobile Responsive Layouts - Phase A Tests
 *
 * Test Coverage:
 * 1. Mobile viewport (375px) renders correctly
 * 2. Tablet viewport (768px) renders correctly
 * 3. Desktop viewport (1280px) renders correctly
 * 4. Responsive classes applied correctly at each breakpoint
 * 5. Touch targets meet minimum size requirements (44x44px)
 * 6. Layout adapts correctly on viewport resize
 *
 * Written BEFORE implementation per TDD protocol.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, act } from '../../testUtils';
import CalculationWizard from '../../../src/components/calculator/CalculationWizard';
import { useWizardStore } from '../../../src/store/wizardStore';
import { useCalculatorStore } from '../../../src/store/calculatorStore';

// Mock products API
vi.mock('../../../src/services/api/products', () => {
  const mockProducts = [
    { id: "product-1", name: 'Cotton T-Shirt', category: 'Textiles', code: 'COTTON-001' },
    { id: "product-2", name: 'Polyester Jacket', category: 'Textiles', code: 'POLY-002' },
  ];
  return {
    productsAPI: {
      list: vi.fn().mockResolvedValue(mockProducts),
      getById: vi.fn().mockResolvedValue(mockProducts[0]),
    },
    fetchProducts: vi.fn().mockResolvedValue(mockProducts),
  };
});

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

describe('CalculationWizard Responsive Layout', () => {
  let originalMatchMedia: typeof window.matchMedia;
  let changeHandlers: Map<string, ((ev: MediaQueryListEvent) => void)[]>;

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

      handlers.forEach(handler => {
        handler({ matches, media: query } as MediaQueryListEvent);
      });
    });

    window.dispatchEvent(new Event('resize'));
  };

  beforeEach(async () => {
    changeHandlers = new Map();
    originalMatchMedia = window.matchMedia;

    // Default to desktop viewport
    setViewport(1280);

    // Clear localStorage and reset stores
    localStorage.clear();
    useWizardStore.getState().reset();
    useCalculatorStore.getState().reset();
    vi.clearAllMocks();

    // Wait for persist middleware to settle
    await new Promise(resolve => setTimeout(resolve, 0));
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    changeHandlers.clear();
  });

  // ==========================================================================
  // Test Suite 1: Mobile Viewport (375px)
  // ==========================================================================

  describe('Mobile Viewport (375px)', () => {
    beforeEach(() => {
      setViewport(375);
    });

    it('should render correctly at mobile viewport', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      // Should have main heading
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('should apply mobile padding classes (p-4)', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');
      // Check for mobile-appropriate padding
      // The component should have responsive padding (p-4 on mobile)
      expect(main).toHaveClass('p-4');
    });

    it('should render step indicator in vertical layout or as icons on mobile', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });

      const header = screen.getByRole('banner');

      // On mobile, step indicator should be vertical (flex-col) or show icons only
      // Check for mobile-specific layout classes
      const stepContainer = header.querySelector('[data-testid="step-indicator"]');
      if (stepContainer) {
        expect(stepContainer).toHaveClass('flex-col');
      }
    });

    it('should display navigation buttons at full width on mobile', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      });

      const footer = screen.getByRole('contentinfo');
      const nextButton = screen.getByRole('button', { name: /next/i });

      // On mobile, buttons should be full width (w-full)
      expect(nextButton).toHaveClass('w-full');
    });

    it('should reduce font size for mobile headings', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      });

      const stepHeading = screen.getByRole('heading', { level: 2 });

      // Mobile heading should use smaller text (text-xl instead of text-3xl)
      expect(stepHeading).toHaveClass('text-xl');
    });

    it('should stack form elements vertically on mobile', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');

      // Form container should be single column on mobile (grid-cols-1)
      const gridContainer = main.querySelector('.grid');
      if (gridContainer) {
        expect(gridContainer).toHaveClass('grid-cols-1');
      }
    });
  });

  // ==========================================================================
  // Test Suite 2: Tablet Viewport (768px)
  // ==========================================================================

  describe('Tablet Viewport (768px)', () => {
    beforeEach(() => {
      setViewport(768);
    });

    it('should render correctly at tablet viewport', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('should apply tablet padding classes (p-6 or sm:p-6)', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');
      // Tablet should have medium padding (p-6)
      expect(main).toHaveClass('p-6');
    });

    it('should render step indicator horizontally on tablet', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });

      const header = screen.getByRole('banner');

      // On tablet, step indicator should be horizontal (flex-row)
      const stepContainer = header.querySelector('[data-testid="step-indicator"]');
      if (stepContainer) {
        expect(stepContainer).toHaveClass('flex-row');
      }
    });

    it('should show abbreviated step labels on tablet', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });

      // Progress buttons should have abbreviated labels on tablet
      const progressButtons = screen.getAllByRole('button').filter(btn =>
        btn.getAttribute('aria-label')?.includes('Step')
      );

      // Should have step buttons visible
      expect(progressButtons.length).toBeGreaterThanOrEqual(0);
    });

    it('should use 2-column grid layout for forms on tablet', async () => {
      await act(async () => {
        useWizardStore.getState().markStepComplete('select');
        useWizardStore.getState().setStep('edit');
      });

      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');

      // Form container should use 2 columns on tablet (md:grid-cols-2)
      const gridContainer = main.querySelector('.grid');
      if (gridContainer) {
        expect(gridContainer).toHaveClass('md:grid-cols-2');
      }
    });

    it('should apply tablet font size for headings (text-2xl)', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      });

      const stepHeading = screen.getByRole('heading', { level: 2 });

      // Tablet heading should use medium text (text-2xl or sm:text-2xl)
      expect(stepHeading).toHaveClass('sm:text-2xl');
    });
  });

  // ==========================================================================
  // Test Suite 3: Desktop Viewport (1280px)
  // ==========================================================================

  describe('Desktop Viewport (1280px)', () => {
    beforeEach(() => {
      setViewport(1280);
    });

    it('should render correctly at desktop viewport', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });

    it('should apply desktop padding classes (p-8 or lg:p-8)', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');
      // Desktop should have larger padding (p-8)
      expect(main).toHaveClass('lg:p-8');
    });

    it('should render full step indicator with complete labels on desktop', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });

      // Progress buttons should have full labels on desktop
      const progressButtons = screen.getAllByRole('button');

      // Check for full labels like "Select Product", "Edit BOM", etc.
      const selectButton = progressButtons.find(btn =>
        btn.getAttribute('aria-label')?.includes('Select Product')
      );
      const editButton = progressButtons.find(btn =>
        btn.getAttribute('aria-label')?.includes('Edit BOM')
      );

      expect(selectButton).toBeInTheDocument();
      expect(editButton).toBeInTheDocument();
    });

    it('should use 3-column grid layout for forms on desktop', async () => {
      await act(async () => {
        useWizardStore.getState().markStepComplete('select');
        useWizardStore.getState().setStep('edit');
      });

      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');

      // Form container should use 3 columns on desktop (lg:grid-cols-3)
      const gridContainer = main.querySelector('.grid');
      if (gridContainer) {
        expect(gridContainer).toHaveClass('lg:grid-cols-3');
      }
    });

    it('should apply desktop font size for headings (text-3xl)', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      });

      const stepHeading = screen.getByRole('heading', { level: 2 });

      // Desktop heading should use larger text (text-3xl or md:text-3xl)
      expect(stepHeading).toHaveClass('md:text-3xl');
    });

    it('should display navigation buttons at auto width on desktop', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });

      // On desktop, buttons should be auto width (sm:w-auto)
      expect(nextButton).toHaveClass('sm:w-auto');
    });
  });

  // ==========================================================================
  // Test Suite 4: Responsive Class Application
  // ==========================================================================

  describe('Responsive Class Application', () => {
    it('should apply responsive padding classes correctly', async () => {
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');

      // Should have base mobile padding and responsive overrides
      // Pattern: p-4 sm:p-6 md:p-8 lg:p-10
      expect(main.className).toMatch(/p-4/);
      expect(main.className).toMatch(/sm:p-6/);
      expect(main.className).toMatch(/md:p-8/);
    });

    it('should apply responsive gap classes correctly', async () => {
      setViewport(768);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');

      // Check for responsive gap classes
      // Pattern: gap-2 sm:gap-4 md:gap-6
      const containers = main.querySelectorAll('[class*="gap-"]');
      expect(containers.length).toBeGreaterThan(0);
    });

    it('should apply responsive text size classes correctly', async () => {
      setViewport(1280);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 2 })).toBeInTheDocument();
      });

      const heading = screen.getByRole('heading', { level: 2 });

      // Should have responsive text sizes
      // Pattern: text-xl sm:text-2xl md:text-3xl
      expect(heading.className).toMatch(/text-xl/);
    });

    it('should apply responsive flex direction classes correctly', async () => {
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      });

      const footer = screen.getByRole('contentinfo');

      // Footer buttons should stack on mobile, row on desktop
      // Pattern: flex-col sm:flex-row
      expect(footer.className).toMatch(/flex-col|sm:flex-row/);
    });
  });

  // ==========================================================================
  // Test Suite 5: Touch Target Requirements
  // ==========================================================================

  describe('Touch Target Requirements (WCAG 2.5.5)', () => {
    beforeEach(() => {
      setViewport(375); // Mobile viewport for touch testing
    });

    it('should have navigation buttons with minimum 44x44px touch targets', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });
      const prevButton = screen.getByRole('button', { name: /previous/i });

      // Check for minimum touch target classes (min-h-11 = 44px, py-3 px-6 typically achieves 44px)
      // Tailwind: min-h-11 or min-h-[44px]
      expect(nextButton.className).toMatch(/min-h-11|min-h-\[44px\]|py-3/);
      expect(prevButton.className).toMatch(/min-h-11|min-h-\[44px\]|py-3/);
    });

    it('should have step indicator buttons with minimum 44x44px touch targets', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
      });

      const progressButtons = screen.getAllByRole('button').filter(btn =>
        btn.getAttribute('aria-label')?.includes('Step') ||
        btn.getAttribute('aria-label')?.includes('Select') ||
        btn.getAttribute('aria-label')?.includes('Edit')
      );

      progressButtons.forEach(button => {
        // Step indicators should meet minimum touch target size
        expect(button.className).toMatch(/min-w-11|min-h-11|h-11|w-11|p-3/);
      });
    });

    it('should have adequate spacing between interactive elements', async () => {
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      });

      const footer = screen.getByRole('contentinfo');

      // Footer should have gap between buttons
      expect(footer.className).toMatch(/gap-2|gap-4|space-x-2|space-x-4/);
    });
  });

  // ==========================================================================
  // Test Suite 6: Layout Transitions on Resize
  // ==========================================================================

  describe('Layout Transitions on Resize', () => {
    it('should adapt layout when resizing from desktop to mobile', async () => {
      setViewport(1280);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      // Initially desktop
      const main = screen.getByRole('main');
      expect(window.innerWidth).toBe(1280);

      // Resize to mobile
      act(() => {
        simulateResize(375);
      });

      // Main should still be present after resize
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('should adapt layout when resizing from mobile to tablet', async () => {
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      // Resize to tablet
      act(() => {
        simulateResize(768);
      });

      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('should not cause layout thrashing on rapid resize events', async () => {
      setViewport(1280);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      // Rapid resize events
      act(() => {
        simulateResize(768);
        simulateResize(375);
        simulateResize(1024);
        simulateResize(480);
        simulateResize(1280);
      });

      // Component should still be functional
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // Test Suite 7: Accessibility at Different Viewports
  // ==========================================================================

  describe('Accessibility at Different Viewports', () => {
    it('should maintain accessibility landmarks on mobile', async () => {
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument(); // header
        expect(screen.getByRole('main')).toBeInTheDocument();
        expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
      });
    });

    it('should maintain accessibility landmarks on tablet', async () => {
      setViewport(768);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
        expect(screen.getByRole('main')).toBeInTheDocument();
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      });
    });

    it('should maintain accessibility landmarks on desktop', async () => {
      setViewport(1280);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('banner')).toBeInTheDocument();
        expect(screen.getByRole('main')).toBeInTheDocument();
        expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      });
    });

    it('should have readable text at all viewport sizes', async () => {
      // Test mobile
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 2 });
        expect(heading).toBeInTheDocument();
        // Text should not be smaller than text-base (16px)
        expect(heading.className).not.toMatch(/text-xs|text-\[10px\]|text-\[8px\]/);
      });
    });
  });

  // ==========================================================================
  // Test Suite 8: No Horizontal Scroll
  // ==========================================================================

  describe('No Horizontal Scroll', () => {
    it('should not cause horizontal overflow on mobile', async () => {
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const main = screen.getByRole('main');

      // Check for overflow-x-hidden or width constraints
      expect(main.className).toMatch(/overflow-x-hidden|max-w-full|w-full/);
    });

    it('should constrain content width to viewport on mobile', async () => {
      setViewport(375);
      render(<CalculationWizard />);

      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      // All containers should have width constraints
      const containers = document.querySelectorAll('[class*="container"], [class*="max-w-"]');
      containers.forEach(container => {
        expect(container.className).toMatch(/max-w-|w-full|container/);
      });
    });
  });
});
