import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { TooltipProvider } from '@/components/ui/tooltip';
import { TourProvider } from '@/contexts/TourContext';

/**
 * Custom render function with all necessary providers
 *
 * Usage:
 * import { render, screen } from '../testUtils';
 *
 * render(<MyComponent />);
 * expect(screen.getByText('Hello')).toBeInTheDocument();
 *
 * @param ui - React component to render
 * @param options - Render options
 * @returns Render result with utilities
 */
export function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
): RenderResult {
  // Create a new QueryClient for each test to ensure isolation
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Disable retries in tests
        cacheTime: 0, // Disable caching in tests
      },
    },
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <TourProvider>
            {children}
          </TourProvider>
        </TooltipProvider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Re-export everything from @testing-library/react
 */
export * from '@testing-library/react';

/**
 * Override render with custom version
 */
export { renderWithProviders as render };

/**
 * Export userEvent for user interactions
 */
export { userEvent };

/**
 * Helper: Wait for async operations to complete
 */
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

/**
 * Helper: Advance timers and wait for async operations
 */
export const advanceTimersAndWait = async (ms: number) => {
  vi.advanceTimersByTime(ms);
  await waitForAsync();
};

/**
 * Helper: Get store state (for debugging)
 */
export function getStoreState<T>(store: { getState: () => T }): T {
  return store.getState();
}

/**
 * Helper: Reset all stores to initial state
 */
export function resetAllStores(
  stores: Array<{ getState: () => { reset: () => void } }>
) {
  stores.forEach(store => {
    const state = store.getState();
    if (typeof state.reset === 'function') {
      state.reset();
    }
  });
}

/**
 * Mock data helpers
 */
export const mockData = {
  /**
   * Create a mock product
   */
  product: (overrides = {}) => ({
    id: 'prod-test-001',
    code: 'TEST-001',
    name: 'Test Product',
    category: 'Test Category',
    unit: 'unit',
    is_finished_product: true,
    ...overrides,
  }),

  /**
   * Create a mock BOM item
   */
  bomItem: (overrides = {}) => ({
    component_id: 'comp-test-001',
    component_name: 'Test Component',
    quantity: 1.0,
    unit: 'kg',
    category: 'material',
    emission_factor_id: 'ef-test-001',
    ...overrides,
  }),

  /**
   * Create a mock calculation result
   */
  calculationResult: (overrides = {}) => ({
    calculation_id: 'calc-test-001',
    product_id: 'prod-test-001',
    product_name: 'Test Product',
    status: 'completed',
    calculation_type: 'cradle_to_gate',
    total_emissions: 10.0,
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    breakdown: {
      materials_emissions: 5.0,
      energy_emissions: 3.0,
      transport_emissions: 1.5,
      waste_emissions: 0.5,
    },
    components: [],
    sankey_data: {
      nodes: [],
      links: [],
    },
    ...overrides,
  }),
};
