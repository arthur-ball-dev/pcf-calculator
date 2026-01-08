/**
 * Test Setup
 *
 * Configures testing environment with jest-dom matchers, MSW, and global utilities.
 * Includes polyfills for JSDOM limitations and localStorage mock for Zustand persistence.
 */

// ============================================================================
// localStorage Mock (MUST be defined before any store imports)
// ============================================================================

/**
 * In-memory localStorage mock for Node.js test environment.
 * Zustand persist middleware requires localStorage to be available.
 *
 * Note: jsdom provides localStorage, but this explicit mock ensures:
 * - Consistent behavior across environments
 * - Ability to clear storage between tests
 * - Clear error messages if something goes wrong
 */
class LocalStorageMock implements Storage {
  private store: Map<string, string>;

  constructor() {
    this.store = new Map();
  }

  get length(): number {
    return this.store.size;
  }

  key(index: number): string | null {
    const keys = Array.from(this.store.keys());
    return keys[index] ?? null;
  }

  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, String(value));
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }
}

// Install mock on globalThis if not already present (jsdom may provide it)
if (typeof globalThis.localStorage === "undefined") {
  const localStorageMock = new LocalStorageMock();
  Object.defineProperty(globalThis, "localStorage", {
    value: localStorageMock,
    writable: true,
    configurable: true,
  });
}

// Also mock sessionStorage for completeness
if (typeof globalThis.sessionStorage === "undefined") {
  const sessionStorageMock = new LocalStorageMock();
  Object.defineProperty(globalThis, "sessionStorage", {
    value: sessionStorageMock,
    writable: true,
    configurable: true,
  });
}

// ============================================================================
// Rest of setup file
// ============================================================================

import "@testing-library/jest-dom";
import { afterEach, beforeAll, afterAll, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";
import { server } from "../__mocks__/server";

// ============================================================================
// MSW Server Setup
// ============================================================================

// Start MSW server before all tests
beforeAll(() => {
  server.listen({ onUnhandledRequest: "warn" });
});

// Reset handlers after each test to ensure test isolation
afterEach(() => {
  server.resetHandlers();
});

// Cleanup React components after each test
afterEach(() => {
  cleanup();
});

// Clear localStorage and sessionStorage between tests
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

// Stop MSW server after all tests
afterAll(() => {
  server.close();
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
