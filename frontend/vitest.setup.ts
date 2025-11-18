/**
 * Vitest Setup File
 *
 * Global test configuration and setup for all vitest tests.
 */

import '@testing-library/jest-dom';
import { vi, beforeEach } from 'vitest';

// ============================================================================
// Global Test Utilities
// ============================================================================

// Make vitest test utilities globally available
(globalThis as any).vi = vi;

// ============================================================================
// Axios Mock Setup
// ============================================================================

// Import the axios mock (will be auto-used due to __mocks__ directory)
import { mockAxiosInstance } from './__mocks__/axios';

// Make mockAxiosInstance globally available for tests
(globalThis as any).mockAxiosInstance = mockAxiosInstance;

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
});
