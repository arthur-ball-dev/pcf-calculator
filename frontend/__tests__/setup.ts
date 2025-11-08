/**
 * Test Setup
 *
 * Configures testing environment with jest-dom matchers and global utilities.
 * Includes polyfills for JSDOM limitations.
 */

import '@testing-library/jest-dom';
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// ============================================================================
// JSDOM Polyfills for Radix UI Components
// ============================================================================

// Polyfill for Element.prototype.hasPointerCapture (used by Radix Select)
if (!Element.prototype.hasPointerCapture) {
  Element.prototype.hasPointerCapture = function () {
    return false;
  };
}

// Polyfill for Element.prototype.scrollIntoView (used by Radix Select)
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = function () {
    // No-op in test environment
  };
}

// Polyfill for Element.prototype.releasePointerCapture (used by Radix Select)
if (!Element.prototype.releasePointerCapture) {
  Element.prototype.releasePointerCapture = function () {
    // No-op in test environment
  };
}

// Polyfill for Element.prototype.setPointerCapture (used by Radix Select)
if (!Element.prototype.setPointerCapture) {
  Element.prototype.setPointerCapture = function () {
    // No-op in test environment
  };
}

// Mock IntersectionObserver (used by some Radix components)
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as any;

// Mock ResizeObserver (used by some Radix components)
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any;
