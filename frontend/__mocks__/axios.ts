/**
 * Axios Mock for Testing
 *
 * Provides a mock axios implementation for vitest tests.
 * This file is automatically used by vitest when axios is mocked.
 */

import { vi } from 'vitest';

// Create the mock axios instance that will be returned by axios.create()
export const mockAxiosInstance = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
  patch: vi.fn(),
  request: vi.fn(),
  interceptors: {
    request: {
      use: vi.fn(() => 0),
      eject: vi.fn(),
      clear: vi.fn(),
    },
    response: {
      use: vi.fn(() => 0),
      eject: vi.fn(),
      clear: vi.fn(),
    },
  },
};

// The axios module default export
const axiosMock = {
  create: vi.fn(() => mockAxiosInstance),
  isAxiosError: vi.fn((error: any) => error?.isAxiosError === true),
  ...mockAxiosInstance,  // Also provide methods on axios itself
};

export default axiosMock;
