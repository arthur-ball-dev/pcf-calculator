/**
 * Test Utilities
 *
 * Provides test setup utilities and custom render functions for React Testing Library.
 */

import React from 'react';
import { render as rtlRender } from '@testing-library/react';
import type { RenderOptions } from '@testing-library/react';

/**
 * Custom render function that wraps components with necessary providers
 */
function render(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return rtlRender(ui, options);
}

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { render };
